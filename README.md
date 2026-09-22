# Graph Neural Networks for Molecular Property Prediction
## A Complete Technical and Implementation Guide (Tox21 / Drug Discovery)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-2.x-orange)
![PyTorch Geometric](https://img.shields.io/badge/PyG-2.8-green)
![RDKit](https://img.shields.io/badge/RDKit-2026-teal)
![License](https://img.shields.io/badge/License-MIT-purple)

---

## 1. Project Overview

This repository provides an end-to-end, self-contained implementation of **Graph Neural Networks (GNNs)** for predicting molecular property endpoints — specifically toxicity across the **12 canonical Tox21 bioassays** — directly from chemical structure without hand-coded chemistry rules.

### Key Components Built:
1. **RDKit Featurization Pipeline (`src/featurize.py`)**: Converts SMILES strings into PyTorch Geometric graph representations (`Data` objects) with 72 atom-level features and 6 bond-level features.
2. **Scaffold Split Dataset (`src/dataset.py`)**: Automatic download of the Tox21 dataset with strict **Bemis-Murcko scaffold splitting** (80% train / 10% val / 10% test) to prevent structural data leakage.
3. **GNN Architecture Suite (`src/model.py`)**: Implementations of:
   - **GCN** (Graph Convolutional Network)
   - **GIN** (Graph Isomorphism Network - 1-WL expressiveness)
   - **MPNN** (Message Passing Neural Network with Edge Attributes)
   - **Morgan Fingerprint + Random Forest Baseline**
4. **Training & Loss Masking (`src/train.py`)**: Multi-task learning loop with missing target label masking (`NaNs`).
5. **Evaluation Suite (`src/evaluate.py`)**: Computes per-task and mean **ROC-AUC**, **PR-AUC**, **Sensitivity**, and **Specificity**, outputting `results/metrics.csv` and macro ROC curve figures.
6. **Gradient Atom Saliency (`src/visualize.py`)**: Atom-level importance attribution ($d(\text{logit})/dx$) highlighting toxicophore substructures on 2D RDKit renders.
7. **Interactive Web Dashboard (`src/app.py` + `public/`)**: Modern dark glassmorphic web UI for live molecular property inference and visualization.

---

## 2. Core Theoretical Concepts

### 2.1 SMILES & Molecules as Graphs
A molecule maps naturally to an undirected graph $G = (V, E)$:
- **Nodes ($V$)**: Represent individual atoms with feature vectors $\mathbf{x}_v \in \mathbb{R}^{72}$ (atomic number, formal charge, degree, total hydrogens, hybridization, aromaticity, ring membership).
- **Edges ($E$)**: Represent covalent bonds with feature vectors $\mathbf{e}_{u,v} \in \mathbb{R}^6$ (bond type: single, double, triple, aromatic; conjugation; ring membership).

### 2.2 Message Passing Scheme
At layer $k$, node states update via neighborhood aggregation:
$$\mathbf{h}_v^{(k+1)} = \text{UPDATE}\left( \mathbf{h}_v^{(k)}, \text{AGGREGATE}\left( \{ (\mathbf{h}_u^{(k)}, \mathbf{e}_{u,v}) : u \in \mathcal{N}(v) \} \right) \right)$$

Stacking $k$ message passing steps allows each atom to encode context from functional groups up to $k$ bonds away.

### 2.3 Readout & Multi-Task Head
Graph-level representation $\mathbf{h}_G$ is pooled via Global Mean or Sum Pooling:
$$\mathbf{h}_G = \text{READOUT}(\{\mathbf{h}_v^{(K)} : v \in V\})$$
$$\mathbf{\hat{y}} = \sigma(\text{MLP}(\mathbf{h}_G)) \in [0, 1]^{12}$$

---

## 3. The 12 Tox21 Bioassay Endpoints

| Endpoint | Target Description | Pathway |
| :--- | :--- | :--- |
| **NR-AR** | Androgen Receptor | Nuclear Receptor |
| **NR-AR-LBD** | Androgen Receptor Ligand Binding Domain | Nuclear Receptor |
| **NR-AhR** | Aryl Hydrocarbon Receptor | Nuclear Receptor |
| **NR-Aromatase**| Aromatase Enzyme Inhibitor | Nuclear Receptor |
| **NR-ER** | Estrogen Receptor | Nuclear Receptor |
| **NR-ER-LBD** | Estrogen Receptor Ligand Binding Domain | Nuclear Receptor |
| **NR-PPAR-gamma**| Peroxisome Proliferator-Activated Receptor Gamma | Nuclear Receptor |
| **SR-ARE** | Antioxidant Response Element | Stress Response |
| **SR-ATAD5** | ATAD5 DNA Damage Response | Stress Response |
| **SR-HSE** | Heat Shock Factor Response Element | Stress Response |
| **SR-MMP** | Mitochondrial Membrane Potential Disruption | Stress Response |
| **SR-p53** | p53 Tumor Suppressor Activation | Stress Response |

---

## 4. Installation & Environment Setup

```bash
# 1. Clone or navigate to the repository workspace
cd d:\C-FOOTPRINT

# 2. Install dependencies
pip install -r requirements.txt
```

---

## 5. Usage & Execution Guide

### 5.1 Step 1: Featurizer Self-Test
```bash
python -m src.featurize
```

### 5.2 Step 2: Download Dataset & Verify Scaffold Split
```bash
python -m src.dataset
```

### 5.3 Step 3: Train GNN Models (GCN / GIN / MPNN)
```bash
# Train Graph Convolutional Network (GCN)
python -m src.train --arch gcn --epochs 30 --batch_size 64

# Train Graph Isomorphism Network (GIN)
python -m src.train --arch gin --epochs 30 --batch_size 64

# Train Message Passing Neural Network with Bond Attributes (MPNN)
python -m src.train --arch mpnn --epochs 30 --batch_size 64
```

### 5.4 Step 4: Run Full Evaluation & Benchmark Comparison
```bash
python -m src.evaluate
```
This writes `results/metrics.csv` and generates high-resolution figures in `results/figures/roc_curves.png`.

### 5.5 Step 5: Launch Interactive Web Application Dashboard
```bash
python src/app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 6. Directory Structure

```
d:\C-FOOTPRINT\
├── data/
│   ├── raw/                      # Downloaded Tox21 raw dataset CSV
│   └── processed/                # Cached PyG molecular graph tensors
├── src/
│   ├── __init__.py
│   ├── featurize.py              # SMILES to Graph featurization (RDKit)
│   ├── dataset.py                # Tox21 dataset & Bemis-Murcko scaffold splitter
│   ├── model.py                  # GCN, GIN, MPNN & Morgan FP baseline
│   ├── train.py                  # Masked BCE loss training loop
│   ├── evaluate.py               # Per-task ROC-AUC, PR-AUC, Sensitivity & Specificity
│   ├── visualize.py              # Gradient atom saliency & 2D SVG renderer
│   └── app.py                    # Flask web application server
├── public/
│   ├── index.html                # Dark glassmorphic user interface
│   ├── styles.css                # Styling system & CSS variables
│   └── app.js                    # Client JS for real-time inference
├── notebooks/
│   └── exploration.ipynb         # Exploratory data analysis walkthrough notebook
├── results/
│   ├── metrics.csv               # Comparative evaluation results CSV
│   └── figures/                  # ROC curves and task metric plots
├── requirements.txt
└── README.md
```

---

## 7. License
This project is released under the **MIT License**.
