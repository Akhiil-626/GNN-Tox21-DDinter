"""
Torch-dependent tests: order independence of SymmetricDDI, extra-feature plumbing,
gradient flow, and the cross-fit / profiler wiring. Skipped automatically when torch or
torch_geometric is not installed.

Run:  python -m pytest tests/test_ddi_torch.py -q
"""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import torch
    import torch_geometric  # noqa: F401
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

pytestmark = pytest.mark.skipif(not HAS_TORCH, reason="torch / torch_geometric not installed")

if HAS_TORCH:
    from src.ddi_model import SymmetricDDI, DualEncoderDDI
    from src.ddi_features import PAIR_FEATURE_DIM


class G:
    """Minimal graph batch with the attributes the encoders read."""
    def __init__(self, n_atoms, seed, in_dim=72):
        g = torch.Generator().manual_seed(seed)
        self.x = torch.randn(n_atoms, in_dim, generator=g)
        src = torch.arange(0, n_atoms - 1)
        dst = torch.arange(1, n_atoms)
        self.edge_index = torch.stack([torch.cat([src, dst]), torch.cat([dst, src])])
        self.edge_attr = torch.randn(self.edge_index.size(1), 6, generator=g)
        self.batch = torch.zeros(n_atoms, dtype=torch.long)


@pytest.mark.parametrize('arch', ['gcn', 'gin'])
def test_symmetric_model_is_order_independent(arch):
    torch.manual_seed(0)
    model = SymmetricDDI(arch=arch, num_outputs=3).eval()
    a, b = G(9, 1), G(7, 2)
    with torch.no_grad():
        assert torch.allclose(model(a, b), model(b, a), atol=1e-6)


@pytest.mark.parametrize('arch', ['gcn', 'gin'])
def test_symmetric_model_with_extra_features_is_order_independent(arch):
    torch.manual_seed(0)
    model = SymmetricDDI(arch=arch, num_outputs=3, extra_dim=PAIR_FEATURE_DIM).eval()
    a, b = G(9, 3), G(6, 4)
    extra = torch.rand(1, PAIR_FEATURE_DIM)
    with torch.no_grad():
        assert torch.allclose(model(a, b, extra), model(b, a, extra), atol=1e-6)


def test_legacy_concat_model_is_not_order_independent():
    """Documents the flaw the symmetric head fixes."""
    torch.manual_seed(0)
    model = DualEncoderDDI(arch='gin', num_outputs=3).eval()
    a, b = G(9, 5), G(7, 6)
    with torch.no_grad():
        assert not torch.allclose(model(a, b), model(b, a), atol=1e-6)


def test_extra_features_are_required_when_model_expects_them():
    model = SymmetricDDI(arch='gcn', num_outputs=3, extra_dim=PAIR_FEATURE_DIM).eval()
    with pytest.raises(ValueError):
        model(G(5, 1), G(5, 2))


def test_extra_features_change_the_output():
    torch.manual_seed(0)
    model = SymmetricDDI(arch='gcn', num_outputs=3, extra_dim=PAIR_FEATURE_DIM).eval()
    a, b = G(8, 7), G(8, 8)
    with torch.no_grad():
        o1 = model(a, b, torch.zeros(1, PAIR_FEATURE_DIM))
        o2 = model(a, b, torch.arange(PAIR_FEATURE_DIM, dtype=torch.float).unsqueeze(0))
    assert not torch.allclose(o1, o2)


def test_gradients_reach_encoder_and_extra_projection():
    model = SymmetricDDI(arch='gin', num_outputs=3, extra_dim=PAIR_FEATURE_DIM)
    model.train()
    a, b = G(8, 9), G(8, 10)
    # batch of two identical graphs so BatchNorm has a variance to work with
    def dup(g):
        d = G(8, 0)
        d.x = torch.cat([g.x, g.x + 0.1]); d.batch = torch.cat([g.batch, g.batch + 1])
        d.edge_index = torch.cat([g.edge_index, g.edge_index + g.x.size(0)], dim=1)
        d.edge_attr = torch.cat([g.edge_attr, g.edge_attr])
        return d
    out = model(dup(a), dup(b), torch.rand(2, PAIR_FEATURE_DIM))
    out.sum().backward()
    assert model.extra_proj[1].weight.grad is not None and model.extra_proj[1].weight.grad.abs().sum() > 0
    first_conv_params = [p for p in model.encoder.parameters() if p.grad is not None]
    assert first_conv_params and any(p.grad.abs().sum() > 0 for p in first_conv_params)


def test_config_round_trip_rebuilds_same_architecture():
    m = SymmetricDDI(arch='gin', hidden_dim=64, num_outputs=3, extra_dim=40)
    cfg = m.config(in_dim=72, edge_dim=6, hidden_dim=64)
    m2 = SymmetricDDI(arch=cfg['arch'], in_dim=cfg['in_dim'], edge_dim=cfg['edge_dim'],
                      hidden_dim=cfg['hidden_dim'], num_outputs=cfg['num_outputs'], extra_dim=cfg['extra_dim'])
    m2.load_state_dict(m.state_dict())
