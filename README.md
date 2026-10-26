# Graph Neural Networks for Molecular Property Prediction

## A Complete Technical and Implementation Guide (Tox21 / Drug Discovery)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-2.x-orange)
![PyTorch Geometric](https://img.shields.io/badge/PyG-2.8-green)
![RDKit](https://img.shields.io/badge/RDKit-2026-teal)
![License](https://img.shields.io/badge/License-MIT-purple)

---

## 1. Project Overview

C-FOOTPRINT is an end-to-end pipeline for two related molecular safety tasks, both built on Graph Neural Networks operating directly on chemical structure rather than hand-coded descriptors:

Single-compound toxicity screening — predicts activity across the 12 canonical Tox21 bioassay endpoints from a SMILES string or a plain chemical name.
Drug–drug interaction (DDI) severity prediction — given two drugs, predicts interaction severity (Minor / Moderate / Major) using a dual-encoder GNN trained on DDInter, with an optional plain-language mechanism summary generated locally via Ollama from DDInter's own reported interaction categories.

Both are served through a single Flask dashboard with live inference, atom-level saliency visualization, chemical-name resolution via PubChem, and curated DDInter interaction records displayed beside model predictions.

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
7. **Interactive Web Dashboard (`src/app.py` + `public/`)**: Modern dark glassmorphic web UI for live molecular property inference, visualization, pairwise comparison with curated DDInter records, and a multi-drug **Prescription Checker** for screening 2 to 5 drugs with relation network graphs, severity distributions, and structural analogue analysis.
8. **DDInter Structure Lookup (`src/ddinter_lookup.py`)**: Fast structure-canonicalized indexing of DDInter bulk datasets for verifying predicted DDIs against curated literature, computing partner severity distributions, and identifying structurally similar drug analogues.

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

| Endpoint          | Target Description                               | Pathway          |
| :---------------- | :----------------------------------------------- | :--------------- |
| **NR-AR**         | Androgen Receptor                                | Nuclear Receptor |
| **NR-AR-LBD**     | Androgen Receptor Ligand Binding Domain          | Nuclear Receptor |
| **NR-AhR**        | Aryl Hydrocarbon Receptor                        | Nuclear Receptor |
| **NR-Aromatase**  | Aromatase Enzyme Inhibitor                       | Nuclear Receptor |
| **NR-ER**         | Estrogen Receptor                                | Nuclear Receptor |
| **NR-ER-LBD**     | Estrogen Receptor Ligand Binding Domain          | Nuclear Receptor |
| **NR-PPAR-gamma** | Peroxisome Proliferator-Activated Receptor Gamma | Nuclear Receptor |
| **SR-ARE**        | Antioxidant Response Element                     | Stress Response  |
| **SR-ATAD5**      | ATAD5 DNA Damage Response                        | Stress Response  |
| **SR-HSE**        | Heat Shock Factor Response Element               | Stress Response  |
| **SR-MMP**        | Mitochondrial Membrane Potential Disruption      | Stress Response  |
| **SR-p53**        | p53 Tumor Suppressor Activation                  | Stress Response  |

---

## 4. Installation & Environment Setup

```bash
# 1. Clone or navigate to the repository workspace
cd C-FOOTPRINT

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

### 5.6 Step 6: Mechanism-Aware DDI Study (research extension)

This extension asks one question and answers it with controls: **do toxicity "risk fingerprints" predicted from structure alone help predict DDI severity, especially for drugs the model has never seen?** See [`docs/NOVELTY_AND_LIMITS.md`](docs/NOVELTY_AND_LIMITS.md) for the exact claim, what is and is not novel, and how to read the results honestly.

What was added:

| Piece | File | Purpose |
|---|---|---|
| Order-independent DDI model | `src/ddi_model.py` (`SymmetricDDI`) | `f(A,B) == f(B,A)`; the original concat head did not satisfy this |
| Risk fingerprints | `src/risk_profile.py`, `src/ddi_features.py` | 12 predicted Tox21 scores per drug; symmetric pair features; shared-risk explanation |
| Leak-free profiles | `src/crossfit.py` | K-fold scaffold cross-fitting so a drug is never profiled by a model that trained on it |
| S0 / S1 / S2 evaluation | `src/ddi_splits.py` | both drugs seen / one new / both new; de-duplicates pairs; leakage assertions |
| Baselines | `src/ddi_baselines.py` | Prior, per-drug mean ("is it just a dangerous drug?"), fingerprint forests |
| Ablation + report | `src/run_ablation.py`, `src/ablation_report.py` | multi-seed study, shuffled-profile control, strict rule-based verdicts |
| Overlap-lead analysis | `src/overlap_analysis.py` | tests whether the shared-risk association survives similarity / class / popularity / own-risk controls (can rule an effect out, cannot confirm one) |
| Abstain mode | `src/ddi_conformal.py` | split-conformal prediction sets; the app says "uncertain" instead of guessing |
| Dashboard | `public/`, `src/app.py`, `src/ddi_inference.py` | shared-risk panel (labelled experimental), uncertainty banner, `/api/pair-risk` |

```bash
# 1. Honest risk-fingerprint models (K fold models per task; ~K x a normal Tox21 training run)
python -m src.crossfit --task tox21 --arch gcn --folds 5 --epochs 25

# 1b. Optional metabolism features: put the five TDC CYP files (Veith) in data/cyp/ first
python -m src.crossfit --task cyp --arch gcn --folds 5 --epochs 25 --cyp_dir data/cyp

# 2. Fast tabular study (no GNN training; minutes on CPU). Run this first.
python -m src.run_ablation --no_gnn --seeds 0 1 2 3 4 5 6 7

# 3. Overlap-lead analysis (no training; minutes). Rules the association out or leaves it unconfirmed.
python -m src.overlap_analysis --profiler_arch gcn --n_boot 300 --n_perm 300

# 4. GNN smoke test (tiny; run before the full study and fix anything it reports)
python -m src.run_ablation --max_pairs 3000 --epochs 3 --seeds 0 1 --variants A B B_shuf --no_tabular --out_dir results/ablation_smoke

# 5. Full GNN study (A = structure only, B = + Tox21 profile, B_shuf = shuffled control).
#    Separate out_dir so the tabular results in results/ablation/ are kept.
python -m src.run_ablation --arch gcn --variants A B B_shuf --seeds 0 1 2 3 4 --no_tabular --save_models --out_dir results/ablation_gnn

# 6. Dashboard. Serves the structure-only model (variant A) by default;
#    DDI_VARIANT=B|C|D overrides it, and should only be set if that variant earned it in step 5.
python src/app.py
```

Outputs land in `results/ablation/` (tabular), `results/ablation_gnn/` (GNN) and `results/overlap_analysis/`: `ablation_report.md` (read this), `ablation_summary.csv`, `ablation_runs.csv`, `conformal.csv`, `overlap_correlation.csv`, `figures/ablation_macro_f1.png`.

Self-test without any data or GPU (fabricated data, **never report these numbers**): `python -m src.run_ablation --synthetic --no_gnn`.

Tests: `python -m pytest tests -q` (torch tests skip automatically if torch is absent).


### Limitations & Data Requirements

- The DDInter record lookup and Prescription Checker need the local DDInter CSVs (`data/raw/ddinter_downloads_code_{A,B,D,H,L,P,R,V}.csv`) and the SMILES cache (`data/raw/ddinter_smiles_cache.json`), which are not in the repository because `data/raw` is gitignored. Without them, the record row and prescription checker panel hide themselves in the UI. Run `python -m src.ddi_dataset` first to download the files and build the cache.
- **Mechanism and management text & ATC-based alternatives**: These clinical details are not included in DDInter's bulk download files; the UI links out directly to DDInter drug detail pages (`https://ddinter.scbdd.com/ddinter/drug-detail/<id>/`) instead.
- **Structural analogue inference**: The similar-drug view uses Morgan-fingerprint (radius 2, 2048 bits) Tanimoto similarity as a rough proxy. Any interactions shown for analogues are an inference based on structural similarity, not confirmed pharmacological evidence.

---

## Research findings at a glance

A controlled evaluation of whether predicted toxicity profiles improve drug-drug interaction (DDI) severity prediction yielded a clear negative finding: stacking predicted Tox21 risk fingerprints consistently lowers macro-F1 over molecular structure alone across seen and novel drug scenarios. For an in-depth analysis of traditional DDI benchmark failure modes, confounding stress tests, and methodological contributions, see the full research document: [docs/RESEARCH_GAPS.md](docs/RESEARCH_GAPS.md).

### Baseline Ladder Across Inductive Scenarios
Adding predicted toxicity features (`+ predicted Tox21 profile`, 0.761 / 0.598 / 0.354) consistently underperforms 2D structure alone (`Fingerprint forest`, 0.780 / 0.634 / 0.371) across S0 (both seen), S1 (one new), and S2 (both new) on 84,151 DDInter pairs over 8 seeds.

![Figure 1: Baseline Ladder](results/study_figures/fig1_baseline_ladder.png)

### Scenario Collapse under Inductive Generalization
All models experience severe performance collapse as evaluation moves from transductive pairs (S0) to novel compounds (S2), demonstrating that transductive benchmarks overestimate real-world novel drug generalization by > 0.40 macro-F1.

![Figure 4: Scenario Collapse](results/study_figures/fig4_scenario_collapse.png)

### C-FOOTPRINT Research Gap Map
A systematic audit comparing traditional DDI benchmark practices with C-FOOTPRINT evidence-first methodology across data leakage, baselines, feature stacking, mechanism claims, and order symmetry.

![Figure 10: Research Gap Map](results/study_figures/fig10_gap_map.png)

---

## 6. Directory Structure

```
C-FOOTPRINT/
├── data/
│   ├── raw/                      # Downloaded Tox21 raw dataset CSV & DDInter data
│   └── processed/                # Cached PyG molecular graph tensors
├── docs/
│   └── NOVELTY_AND_LIMITS.md     # Claim, literature positioning, honest limits
├── landing/                      # React + Vite + Tailwind landing page
├── models/                       # GNN checkpoints, crossfit folds, conformal calibrations
├── public/
│   ├── index.html                # Interactive screening dashboard UI
│   ├── masthead.css              # Top bar styling
│   ├── styles.css                # Base dashboard styling system
│   ├── app.js                    # Client JS for real-time inference
│   └── landing/                  # Compiled production landing page build
├── src/
│   ├── __init__.py
│   ├── featurize.py              # SMILES to Graph featurization (RDKit)
│   ├── dataset.py                # Tox21 dataset & Bemis-Murcko scaffold splitter
│   ├── ddi_dataset.py            # DDInter dataset loader & SMILES cache builder
│   ├── ddinter_lookup.py         # DDInter canonical SMILES pair index & record lookup
│   ├── model.py                  # GCN, GIN, MPNN & Morgan FP baseline
│   ├── ddi_model.py              # DualEncoderDDI + SymmetricDDI (order-independent)
│   ├── ddi_features.py           # Risk-fingerprint pair features & shared-risk explanation
│   ├── ddi_splits.py             # S0/S1/S2 drug-level splits, pair de-duplication, leakage checks
│   ├── ddi_baselines.py          # Prior / per-drug-mean / fingerprint-forest baselines
│   ├── ddi_conformal.py          # Split-conformal prediction sets & abstain rule
│   ├── ddi_inference.py          # Serving glue for the dashboard
│   ├── risk_profile.py           # RiskProfiler (cross-fit aware)
│   ├── crossfit.py               # K-fold cross-fitted Tox21 / CYP models
│   ├── chem_utils.py             # Canonical molecule keys, balanced scaffold folds
│   ├── run_ablation.py           # Full multi-seed study runner
│   ├── ablation_report.py        # Statistics, strict verdict rules, markdown report
│   ├── overlap_analysis.py       # Confounding controls analysis
│   ├── controlled_overlap_test.py# Controlled synthetic overlap test
│   ├── ddi_synthetic.py          # Fabricated data for pipeline self-tests only
│   ├── train.py                  # Masked BCE loss training loop
│   ├── train_ddi.py              # Cold-start DDI training loop
│   ├── evaluate.py               # Per-task ROC-AUC, PR-AUC, Sensitivity & Specificity
│   ├── evaluate_ddi.py           # DDI evaluation metrics & confusion matrix
│   ├── visualize.py              # Gradient atom saliency & 2D SVG renderer
│   └── app.py                    # Flask web application server
├── tests/
│   ├── test_ddinter_lookup.py    # Unit tests for lookup and cache
│   ├── test_ddi_novelty.py       # Unit tests for leakage assertions and crossfit
│   └── test_ddi_torch.py         # Unit tests for equivariance and conformal prediction
├── notebooks/
│   └── exploration.ipynb         # Exploratory data analysis walkthrough notebook
├── results/
│   ├── metrics.csv               # Comparative evaluation results CSV
│   ├── ddi_metrics.csv           # DDInter evaluation metrics CSV
│   ├── ablation/                 # Tabular ablation study report and summary
│   ├── ablation_gnn/             # GNN ablation study report and summary
│   ├── overlap_analysis/         # Overlap analysis report and correlation results
│   ├── controlled_overlap/       # Controlled synthetic overlap report
│   └── figures/                  # ROC curves, training curves, saliency renders
├── requirements.txt
└── README.md
```

---

## 7. License

This project is released under the **MIT License**.
