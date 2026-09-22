"""
GNN Model Architectures for Molecular Property Prediction
Includes GCN (Graph Convolutional Network), GIN (Graph Isomorphism Network), 
MPNN (Message Passing Neural Network), and Morgan Fingerprint Random Forest Baseline.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

try:
    from torch_geometric.nn import GCNConv, GINConv, NNConv, GATv2Conv, global_mean_pool, global_add_pool, global_max_pool
    HAS_PYG_NN = True
except ImportError:
    HAS_PYG_NN = False


class GCNModel(nn.Module):
    """
    Graph Convolutional Network (GCN) for Molecular Property Prediction.
    Stack of k GCNConv layers with BatchNorm, ReLU, Dropout, and Global Pooling.
    """
    def __init__(self, in_dim: int = 72, hidden_dim: int = 128, num_layers: int = 3, 
                 num_tasks: int = 12, dropout: float = 0.2, pooling: str = 'mean'):
        super().__init__()
        self.num_layers = num_layers
        self.dropout = dropout
        self.pooling = pooling
        
        self.convs = nn.ModuleList()
        self.bns = nn.ModuleList()
        
        # Input layer
        self.convs.append(GCNConv(in_dim, hidden_dim))
        self.bns.append(nn.BatchNorm1d(hidden_dim))
        
        # Hidden layers
        for _ in range(num_layers - 1):
            self.convs.append(GCNConv(hidden_dim, hidden_dim))
            self.bns.append(nn.BatchNorm1d(hidden_dim))
            
        # Multi-task Classifier Head
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, num_tasks)
        )

    def forward(self, x, edge_index, batch=None, return_node_feats=False):
        if batch is None:
            batch = torch.zeros(x.size(0), dtype=torch.long, device=x.device)
            
        h = x
        for i in range(self.num_layers):
            h = self.convs[i](h, edge_index)
            h = self.bns[i](h)
            h = F.relu(h)
            h = F.dropout(h, p=self.dropout, training=self.training)
            
        node_feats = h
        
        # Global Graph Readout / Pooling
        if self.pooling == 'sum':
            graph_feat = global_add_pool(h, batch)
        elif self.pooling == 'max':
            graph_feat = global_max_pool(h, batch)
        else:
            graph_feat = global_mean_pool(h, batch)
            
        logits = self.head(graph_feat)
        
        if return_node_feats:
            return logits, node_feats
        return logits


class GINModel(nn.Module):
    """
    Graph Isomorphism Network (GIN) for Molecular Property Prediction.
    Maximally expressive 1-WL GNN architecture using MLPs for neighbor aggregation.
    """
    def __init__(self, in_dim: int = 72, hidden_dim: int = 128, num_layers: int = 3, 
                 num_tasks: int = 12, dropout: float = 0.2):
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
            
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, num_tasks)
        )

    def forward(self, x, edge_index, batch=None, return_node_feats=False):
        if batch is None:
            batch = torch.zeros(x.size(0), dtype=torch.long, device=x.device)
            
        h = x
        for i in range(self.num_layers):
            h = self.convs[i](h, edge_index)
            h = self.bns[i](h)
            h = F.relu(h)
            h = F.dropout(h, p=self.dropout, training=self.training)
            
        node_feats = h
        graph_feat = global_add_pool(h, batch)
        logits = self.head(graph_feat)
        
        if return_node_feats:
            return logits, node_feats
        return logits


class MPNNModel(nn.Module):
    """
    Message Passing Neural Network (MPNN) with Edge Attributes.
    Uses edge features (bond type, ring membership, conjugation) to condition message passing.
    """
    def __init__(self, in_dim: int = 72, edge_dim: int = 6, hidden_dim: int = 128, 
                 num_layers: int = 3, num_tasks: int = 12, dropout: float = 0.2):
        super().__init__()
        self.num_layers = num_layers
        self.dropout = dropout
        
        self.convs = nn.ModuleList()
        self.bns = nn.ModuleList()
        
        for i in range(num_layers):
            input_dim = in_dim if i == 0 else hidden_dim
            # Neural network mapping edge features to transformation matrix (input_dim x hidden_dim)
            edge_nn = nn.Sequential(
                nn.Linear(edge_dim, 32),
                nn.ReLU(),
                nn.Linear(32, input_dim * hidden_dim)
            )
            self.convs.append(NNConv(input_dim, hidden_dim, edge_nn, aggr='mean'))
            self.bns.append(nn.BatchNorm1d(hidden_dim))
            
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, num_tasks)
        )

    def forward(self, x, edge_index, edge_attr=None, batch=None, return_node_feats=False):
        if batch is None:
            batch = torch.zeros(x.size(0), dtype=torch.long, device=x.device)
            
        h = x
        for i in range(self.num_layers):
            h = self.convs[i](h, edge_index, edge_attr)
            h = self.bns[i](h)
            h = F.relu(h)
            h = F.dropout(h, p=self.dropout, training=self.training)
            
        node_feats = h
        graph_feat = global_mean_pool(h, batch)
        logits = self.head(graph_feat)
        
        if return_node_feats:
            return logits, node_feats
        return logits


def get_model(architecture: str = 'gcn', in_dim: int = 72, edge_dim: int = 6, hidden_dim: int = 128, num_tasks: int = 12) -> nn.Module:
    """Factory function to instantiate GNN models."""
    arch = architecture.lower()
    if arch == 'gcn':
        return GCNModel(in_dim=in_dim, hidden_dim=hidden_dim, num_tasks=num_tasks)
    elif arch == 'gin':
        return GINModel(in_dim=in_dim, hidden_dim=hidden_dim, num_tasks=num_tasks)
    elif arch == 'mpnn':
        return MPNNModel(in_dim=in_dim, edge_dim=edge_dim, hidden_dim=hidden_dim, num_tasks=num_tasks)
    else:
        raise ValueError(f"Unknown architecture: {architecture}. Choose from ['gcn', 'gin', 'mpnn'].")


if __name__ == '__main__':
    # Test model instantiation and dummy forward pass
    dummy_x = torch.randn(10, 72)
    dummy_edge_index = torch.tensor([[0, 1, 2, 3, 4, 5, 6, 7], [1, 2, 3, 4, 5, 6, 7, 8]], dtype=torch.long)
    dummy_edge_attr = torch.randn(8, 6)
    dummy_batch = torch.tensor([0, 0, 0, 0, 0, 1, 1, 1, 1, 1], dtype=torch.long)
    
    gcn = get_model('gcn')
    gin = get_model('gin')
    mpnn = get_model('mpnn')
    
    out_gcn = gcn(dummy_x, dummy_edge_index, dummy_batch)
    out_gin = gin(dummy_x, dummy_edge_index, dummy_batch)
    out_mpnn = mpnn(dummy_x, dummy_edge_index, dummy_edge_attr, dummy_batch)
    
    print(f"GCN Output Shape: {out_gcn.shape}")
    print(f"GIN Output Shape: {out_gin.shape}")
    print(f"MPNN Output Shape: {out_mpnn.shape}")
    print("Model architecture module test PASSED!")
