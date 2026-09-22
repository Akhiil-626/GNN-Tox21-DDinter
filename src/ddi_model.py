"""
Dual-Encoder Drug-Drug Interaction (DDI) Model.

Defines standalone encoder-only versions of the GCN/GIN/MPNN architectures
from model.py (conv layers + pooling, no classification head), applied to
TWO molecules with a single shared encoder instance (Siamese-style weight
sharing). Their embeddings are combined through an interaction module to
predict an interaction outcome.

The encoders here intentionally duplicate the conv-layer loops from
model.py's GCNModel/GINModel/MPNNModel rather than wrapping and bypassing
those classes' `head` attribute -- this avoids any shared mutable state
between the two forward passes (molecule A, then molecule B), which matters
once this runs under Flask's threaded=True in app.py.

This is intentionally the simplest possible version first: concatenation +
MLP. Co-attention / cross-molecule interpretability comes later, once this
shell trains correctly end-to-end.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from torch_geometric.nn import GCNConv, GINConv, NNConv, global_mean_pool, global_add_pool


class GCNEncoder(nn.Module):
    """
    Encoder-only version of GCNModel: same conv-layer loop and pooling as
    GCNModel.forward() in model.py, but stops at graph_feat -- no head.
    Kept independent from GCNModel (rather than wrapping/bypassing it) so
    there's no shared mutable state between two calls run back-to-back on
    molecule A and molecule B (relevant once this runs under Flask's
    threaded=True in app.py).
    """
    def __init__(self, in_dim: int = 72, hidden_dim: int = 128, num_layers: int = 3,
                 dropout: float = 0.2, pooling: str = 'mean'):
        super().__init__()
        self.num_layers = num_layers
        self.dropout = dropout
        self.pooling = pooling

        self.convs = nn.ModuleList()
        self.bns = nn.ModuleList()
        self.convs.append(GCNConv(in_dim, hidden_dim))
        self.bns.append(nn.BatchNorm1d(hidden_dim))
        for _ in range(num_layers - 1):
            self.convs.append(GCNConv(hidden_dim, hidden_dim))
            self.bns.append(nn.BatchNorm1d(hidden_dim))

    def forward(self, x, edge_index, edge_attr=None, batch=None):
        if batch is None:
            batch = torch.zeros(x.size(0), dtype=torch.long, device=x.device)

        h = x
        for i in range(self.num_layers):
            h = self.convs[i](h, edge_index)
            h = self.bns[i](h)
            h = F.relu(h)
            h = F.dropout(h, p=self.dropout, training=self.training)

        if self.pooling == 'sum':
            return global_add_pool(h, batch)
        return global_mean_pool(h, batch)


class GINEncoder(nn.Module):
    """Encoder-only version of GINModel -- mirrors GINModel.forward() up to pooling."""
    def __init__(self, in_dim: int = 72, hidden_dim: int = 128, num_layers: int = 3,
                 dropout: float = 0.2):
        super().__init__()
        self.num_layers = num_layers
        self.dropout = dropout

        self.convs = nn.ModuleList()
        self.bns = nn.ModuleList()
        for i in range(num_layers):
            input_dim = in_dim if i == 0 else hidden_dim
            mlp = nn.Sequential(
                nn.Linear(input_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim)
            )
            self.convs.append(GINConv(mlp, train_eps=True))
            self.bns.append(nn.BatchNorm1d(hidden_dim))

    def forward(self, x, edge_index, edge_attr=None, batch=None):
        if batch is None:
            batch = torch.zeros(x.size(0), dtype=torch.long, device=x.device)

        h = x
        for i in range(self.num_layers):
            h = self.convs[i](h, edge_index)
            h = self.bns[i](h)
            h = F.relu(h)
            h = F.dropout(h, p=self.dropout, training=self.training)

        return global_add_pool(h, batch)


class MPNNEncoder(nn.Module):
    """Encoder-only version of MPNNModel -- mirrors MPNNModel.forward() up to pooling."""
    def __init__(self, in_dim: int = 72, edge_dim: int = 6, hidden_dim: int = 128,
                 num_layers: int = 3, dropout: float = 0.2):
        super().__init__()
        self.num_layers = num_layers
        self.dropout = dropout

        self.convs = nn.ModuleList()
        self.bns = nn.ModuleList()
        for i in range(num_layers):
            input_dim = in_dim if i == 0 else hidden_dim
            edge_nn = nn.Sequential(
                nn.Linear(edge_dim, 32),
                nn.ReLU(),
                nn.Linear(32, input_dim * hidden_dim)
            )
            self.convs.append(NNConv(input_dim, hidden_dim, edge_nn, aggr='mean'))
            self.bns.append(nn.BatchNorm1d(hidden_dim))

    def forward(self, x, edge_index, edge_attr=None, batch=None):
        if batch is None:
            batch = torch.zeros(x.size(0), dtype=torch.long, device=x.device)

        h = x
        for i in range(self.num_layers):
            h = self.convs[i](h, edge_index, edge_attr)
            h = self.bns[i](h)
            h = F.relu(h)
            h = F.dropout(h, p=self.dropout, training=self.training)

        return global_mean_pool(h, batch)


def get_encoder(architecture: str = 'gin', in_dim: int = 72, edge_dim: int = 6,
                 hidden_dim: int = 128) -> nn.Module:
    """Factory function to instantiate encoder-only GNNs, mirroring get_model() in model.py."""
    arch = architecture.lower()
    if arch == 'gcn':
        return GCNEncoder(in_dim=in_dim, hidden_dim=hidden_dim)
    elif arch == 'gin':
        return GINEncoder(in_dim=in_dim, hidden_dim=hidden_dim)
    elif arch == 'mpnn':
        return MPNNEncoder(in_dim=in_dim, edge_dim=edge_dim, hidden_dim=hidden_dim)
    else:
        raise ValueError(f"Unknown architecture: {architecture}. Choose from ['gcn', 'gin', 'mpnn'].")


class DualEncoderDDI(nn.Module):
    """
    Bare-bones dual-encoder DDI model:
      molecule A -> shared encoder -> embedding A
      molecule B -> shared encoder -> embedding B
      [embedding A ; embedding B] -> MLP -> interaction prediction

    Start with num_outputs=1 (binary: interacts / doesn't) before moving to
    severity levels or multi-label side-effect prediction.
    """
    def __init__(self, arch: str = 'gin', in_dim: int = 72, edge_dim: int = 6,
                 hidden_dim: int = 128, num_outputs: int = 1, dropout: float = 0.2):
        super().__init__()

        self.arch = arch.lower()

        # Single shared encoder instance used for BOTH molecules (Siamese-style).
        # get_encoder() builds a standalone encoder-only module -- no dependency
        # on model.py's full models or their `head` attribute.
        self.encoder = get_encoder(self.arch, in_dim=in_dim, edge_dim=edge_dim, hidden_dim=hidden_dim)

        # Simplest possible interaction head: concat + MLP.
        self.interaction_head = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_outputs)
        )

    def forward(self, graph_a, graph_b):
        """
        graph_a, graph_b: objects with .x, .edge_index, .edge_attr, .batch
        (same shape as what you already pass into GCN/GIN/MPNN models).
        """
        edge_attr_a = getattr(graph_a, 'edge_attr', None) if self.arch == 'mpnn' else None
        edge_attr_b = getattr(graph_b, 'edge_attr', None) if self.arch == 'mpnn' else None

        emb_a = self.encoder(graph_a.x, graph_a.edge_index, edge_attr_a, graph_a.batch)
        emb_b = self.encoder(graph_b.x, graph_b.edge_index, edge_attr_b, graph_b.batch)

        combined = torch.cat([emb_a, emb_b], dim=-1)
        logits = self.interaction_head(combined)
        return logits


if __name__ == '__main__':
    # Sanity check with dummy pairs (mirrors the __main__ block in model.py).
    # This validates the plumbing BEFORE any real DDI data is wired in.
    dummy_x_a = torch.randn(10, 72)
    dummy_edge_index_a = torch.tensor([[0, 1, 2, 3, 4, 5, 6, 7], [1, 2, 3, 4, 5, 6, 7, 8]], dtype=torch.long)
    dummy_batch_a = torch.zeros(10, dtype=torch.long)

    dummy_x_b = torch.randn(8, 72)
    dummy_edge_index_b = torch.tensor([[0, 1, 2, 3, 4, 5], [1, 2, 3, 4, 5, 6]], dtype=torch.long)
    dummy_batch_b = torch.zeros(8, dtype=torch.long)

    class DummyGraph:
        def __init__(self, x, edge_index, batch, edge_attr=None):
            self.x = x
            self.edge_index = edge_index
            self.batch = batch
            self.edge_attr = edge_attr

    graph_a = DummyGraph(dummy_x_a, dummy_edge_index_a, dummy_batch_a)
    graph_b = DummyGraph(dummy_x_b, dummy_edge_index_b, dummy_batch_b)

    model = DualEncoderDDI(arch='gin', num_outputs=1)
    out = model(graph_a, graph_b)
    print(f"DualEncoderDDI output shape: {out.shape}")  # expect torch.Size([1, 1])

    # Dummy loss check to confirm gradients flow through both encoders.
    label = torch.tensor([[1.0]])
    loss_fn = nn.BCEWithLogitsLoss()
    loss = loss_fn(out, label)
    loss.backward()
    print(f"Dummy loss: {loss.item():.4f}")
    print("Dual-encoder shell test PASSED — gradients flow correctly.")