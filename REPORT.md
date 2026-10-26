# Scientific Audit and Verification Report: DDI Severity Extension

## Summary
This audit evaluated whether predicted 12-assay Tox21 toxicity profiles improve drug-drug interaction (DDI) severity prediction across seen and unseen drug scenarios. Re-run analysis over 8 seeds on 84,151 DDInter pairs confirms that adding predicted toxicity features slightly hurts macro-F1 across all three test splits compared to a structure-only fingerprint baseline (S0: 0.761 vs 0.780; S1: 0.598 vs 0.634; S2: 0.354 vs 0.371). A shared-risk score exhibits a small correlation with severity ($\rho = 0.042$ after controlling for confounders), but stress testing proves this residual association is reproducible under purely structural confounding and does not provide predictive utility. Product-level features, including an order-independent model, calibrated conformal prediction sets ("I'm not sure" mode), and an experimental shared-risk panel with an honesty caveat, were verified on the live application at 1440px and 375px viewports. The default served model remains strictly structure-only.

---

## Checklist Table

| # | Checklist Item | Status | Source File / Output | Proving Command |
|---|---|---|---|---|
| **1** | **Toxicity risk fingerprints**<br>12 predicted scores per drug as DDI input; reported no help, slight harm | **DONE-VERIFIED** | `results/ablation/ablation_summary.csv`<br>`results/ablation/ablation_runs.csv` | `python -m src.run_ablation --no_gnn --seeds 0,1,2,3,4,5,6,7 --out_dir results/ablation` |
| **2** | **Shared-risk score**<br>Two drugs flagged for same stress; tiny association, unconfirmed by correlation alone | **DONE-VERIFIED** | `results/overlap_analysis/overlap_analysis.csv`<br>`results/overlap_analysis/overlap_analysis.md` | `python -m src.overlap_analysis` |
| **3** | **CYP metabolism features**<br>Optional 2nd feature set; missing data files; reported as NOT TESTED | **NOT TESTED** | `src/run_ablation.py`<br>`docs/NOVELTY_AND_LIMITS.md` | `python -c "import os; assert not os.path.exists('data/tdc_cyp')"` |
| **4** | **Molecule identity**<br>Canonical structure instead of names; 146 names merged; no same-molecule leakage | **DONE-VERIFIED** | `results/ablation/run_meta.json`<br>`src/ddi_splits.py` | `python -m pytest tests/test_ddi_novelty.py -k "test_splits_have_no_leakage or test_name_based_split_leaks_aliased_molecules_but_identity_split_does_not"` |
| **5** | **Three test scenarios**<br>S0 (both seen), S1 (one new), S2 (both new) | **DONE-VERIFIED** | `results/ablation/ablation_summary.csv`<br>`src/ddi_splits.py` | `python -m pytest tests/test_ddi_novelty.py -k "test_splits_populate_every_scenario or test_splits_are_disjoint_index_sets"` |
| **6** | **Leak-free toxicity profiles**<br>Each drug scored by a model that never saw it (5-fold cross-fitting) | **DONE-VERIFIED** | `results/crossfit_tox21_gcn.csv`<br>`models/crossfit_tox21_gcn_folds.json` | `python -m pytest tests/test_ddi_novelty.py -k "test_crossfit_uses_held_out_model_for_known_molecules"` |
| **7** | **Baselines**<br>"Always predict Moderate" (Prior) and "per-drug average severity" (DrugMean) | **DONE-VERIFIED** | `results/ablation/ablation_summary.csv`<br>`src/ddi_baselines.py` | `python -m pytest tests/test_ddi_novelty.py -k "test_prior_baseline_predicts_majority or test_drug_mean"` |
| **8** | **Shuffled-profile control**<br>Profiles swapped between drugs (fixed-point-free permutation) | **DONE-VERIFIED** | `results/ablation/ablation_summary.csv`<br>`src/ddi_baselines.py` | `python -m pytest tests/test_ddi_novelty.py -k "test_shuffle_map_has_no_fixed_points_and_is_a_permutation"` |
| **9** | **Claim rule**<br>$\ge 5$ seeds; effect must beat BOTH baseline AND shuffled control, else "inconclusive" | **DONE-VERIFIED** | `results/ablation/ablation_report.md`<br>`src/ablation_report.py` | `python -m pytest tests/test_ddi_novelty.py -k "test_headline_supported_only_when_beating_baseline_and_shuffled_control or test_headline_rejects_gain_that_shuffled_control_also_gets"` |
| **10** | **Confounder tests**<br>Structural similarity, drug class, popularity, own risk; stress test shows it rules out but cannot confirm | **DONE-VERIFIED** | `results/overlap_analysis/overlap_analysis.md`<br>`tests/test_ddi_novelty.py` | `python -m pytest tests/test_ddi_novelty.py -k "test_overlap_that_is_only_a_proxy_for_drug_risk_does_not_survive_controls or test_KNOWN_LIMITATION_purely_structural_confounding_is_not_explained_away"` |
| **11** | **Order-independent model**<br>Swapping drug A and B gives identical answer | **IMPLEMENTED-NOW** | `src/app.py`<br>`src/ddi_model.py` (`SymmetricDDI`) | `python -m pytest tests/test_ddi_torch.py -k "test_symmetric_model_is_order_independent"` |
| **12** | **"I'm not sure" mode**<br>Shows set of possible severities, calibrated on new drugs too | **IMPLEMENTED-NOW** | `src/app.py`<br>`public/app.js`<br>`models/ddi_sym_A_gcn_conformal.json` | `python -m pytest tests/test_ddi_novelty.py -k "test_conformal_coverage_close_to_target or test_decide_label_only_when_answered"` |
| **13** | **Shared-risk panel**<br>Labelled experimental, states it did not improve predictions | **IMPLEMENTED-NOW** | `src/app.py`<br>`public/index.html`<br>`public/app.js`<br>`public/styles.css` | `python -c "from src.ddi_features import explain_shared_risk; r=explain_shared_risk([0.8]*12, [0.8]*12); assert 'Experimental' in r['caveat'] and 'did NOT improve' in r['caveat']"` |
| **14** | **Default served model**<br>Structure-only (Variant A), not toxicity-feature model | **DONE-VERIFIED** | `src/ddi_inference.py`<br>`models/ddi_sym_A_gcn.pt` | `python -c "from src.ddi_inference import find_available_variant; assert find_available_variant('gcn') == 'A'"` |

---

## Verified Results

### 1. Tabular Ablation Study (8 Seeds: 0, 1, 2, 3, 4, 5, 6, 7 on 84,151 DDInter Pairs)

Macro-F1 (mean $\pm$ std over 8 seeds) across evaluation scenarios:

| Model | S0: Both Drugs Seen | S1: One Drug New | S2: Both Drugs New | Parameter Notes |
|---|---|---|---|---|
| **Prior Baseline** | $0.2828 \pm 0.0024$ | $0.2832 \pm 0.0033$ | $0.2835 \pm 0.0079$ | Always predicts majority class (Moderate, ~74%) |
| **DrugMean Baseline** | $0.5877 \pm 0.0122$ | $0.5398 \pm 0.0164$ | $0.2835 \pm 0.0079$ | No chemistry; per-drug severity history; falls back to Prior on S2 |
| **RF_fp** (Fingerprint baseline) | **$0.7802 \pm 0.0118$** | **$0.6344 \pm 0.0248$** | **$0.3710 \pm 0.0218$** | 1024-dim Morgan fingerprints, 300 trees |
| **RF_fp+tox** (+ predicted Tox21) | $0.7607 \pm 0.0158$ | $0.5984 \pm 0.0285$ | $0.3542 \pm 0.0245$ | 1024-dim Morgan + 12 leak-free crossfit scores per drug |
| **RF_fp+toxshuf** (+ shuffled control) | $0.7302 \pm 0.0174$ | $0.5700 \pm 0.0260$ | $0.3416 \pm 0.0156$ | Negative control: deranged profile assignment |
| **RF_fp+ov** (+ 4 overlap features) | $0.7849 \pm 0.0120$ | $0.6303 \pm 0.0247$ | $0.3700 \pm 0.0205$ | Fingerprint + joint expected active & count features |
| **RF_tox** (Tox21 features alone) | $0.4951 \pm 0.0189$ | $0.4031 \pm 0.0120$ | $0.3067 \pm 0.0107$ | 24-dim profile only; below DrugMean floor on seen drugs |

Accuracy (mean $\pm$ std over 8 seeds):

| Model | S0 Accuracy | S1 Accuracy | S2 Accuracy |
|---|---|---|---|
| **Prior** | $0.7367 \pm 0.0106$ | $0.7384 \pm 0.0149$ | $0.7405 \pm 0.0358$ |
| **DrugMean** | $0.6992 \pm 0.0123$ | $0.7172 \pm 0.0192$ | $0.7405 \pm 0.0358$ |
| **RF_fp** | $0.8710 \pm 0.0076$ | $0.8057 \pm 0.0169$ | $0.7473 \pm 0.0351$ |
| **RF_fp+tox** | $0.8658 \pm 0.0092$ | $0.7988 \pm 0.0172$ | $0.7456 \pm 0.0359$ |
| **RF_fp+toxshuf** | $0.8523 \pm 0.0097$ | $0.7913 \pm 0.0170$ | $0.7463 \pm 0.0355$ |
| **RF_fp+ov** | $0.8736 \pm 0.0071$ | $0.8050 \pm 0.0166$ | $0.7476 \pm 0.0343$ |
| **RF_tox** | $0.7759 \pm 0.0091$ | $0.7534 \pm 0.0148$ | $0.7348 \pm 0.0327$ |

### 2. Paired Hypothesis Tests & Claim Rule Evaluation

Statistical tests on paired seeds ($N = 8$ seeds, Wilcoxon signed-rank test):

| Scenario | Comparison | Mean $\Delta$ Macro-F1 | Seeds Improved | Two-Tided $p$-value | Headline Verdict |
|---|---|---|---|---|---|
| **S0 (Both Seen)** | `RF_fp+tox` vs `RF_fp` | $-0.0196$ | 0 of 8 | $p = 0.00781$ | **NOT SUPPORTED / WORSE** |
| | `RF_fp+tox` vs `RF_fp+toxshuf` | $+0.0305$ | 8 of 8 | $p = 0.00781$ | Real profile beats noise control |
| **S1 (One New)** | `RF_fp+tox` vs `RF_fp` | $-0.0360$ | 0 of 8 | $p = 0.00781$ | **NOT SUPPORTED / WORSE** |
| | `RF_fp+tox` vs `RF_fp+toxshuf` | $+0.0284$ | 8 of 8 | $p = 0.00781$ | Real profile beats noise control |
| **S2 (Both New)** | `RF_fp+tox` vs `RF_fp` | $-0.0168$ | 0 of 8 | $p = 0.00781$ | **NOT SUPPORTED / WORSE** |
| | `RF_fp+tox` vs `RF_fp+toxshuf` | $+0.0126$ | 7 of 8 | $p = 0.02344$ | Real profile beats noise control |

*Conclusion*: Real profiles beat the shuffled profile control across all scenarios (demonstrating that the crossfit models encode genuine, drug-specific signal), but that signal is redundant with structure and consistently degrades predictive generalization when concatenated with Morgan fingerprints.

### 3. Confounder-Controlled Overlap Analysis (`results/overlap_analysis/`)

Evaluated on all 84,151 DDInter pairs with 300 drug-level bootstrap replicates and 300 structure-matched permutations:

| Subset | Pairs | Raw $\rho$ | Controlling Additive Risk | Controlling All Confounders | 95% Drug-Bootstrap CI | Status |
|---|---|---|---|---|---|---|
| **ALL Pairs** | 84,151 | $0.081$ | $0.068$ | $0.042$ | $[0.008, 0.077]$ | **NOT EXPLAINED AWAY (UNCONFIRMED)** |
| **Both in Tox21 Table** | 34,634 | $0.042$ | $0.089$ | $0.067$ | $[0.029, 0.104]$ | **NOT EXPLAINED AWAY (UNCONFIRMED)** |
| **$\ge 1$ Outside Table** | 49,517 | $0.095$ | $0.044$ | $0.015$ | $[-0.029, 0.058]$ | **EXPLAINED AWAY** |

Confounder correlation with severity (Spearman $\rho$ on ALL pairs):
- Additive risk: $0.065$
- Fingerprint Tanimoto similarity: $0.055$
- ATC therapeutic co-membership proxy: $0.132$
- Log popularity (product of drug interaction degrees): $0.200$

### 4. Leak-Free Cross-Fitting Performance (`results/crossfit_tox21_gcn.csv`)

5-fold cross-fitting across 12 Tox21 assays on 7,831 training compounds:
- Fold 0: ROC-AUC = $0.811$
- Fold 1: ROC-AUC = $0.803$
- Fold 2: ROC-AUC = $0.809$
- Fold 3: ROC-AUC = $0.804$
- Fold 4: ROC-AUC = $0.809$
- **Mean Held-Out ROC-AUC**: $0.8072 \pm 0.0036$

### 5. GNN Status
- **GNN full-scale run: pending** (The existing `results/ablation_gnn/` directory contains only an exploratory 2-seed run on 10,000 subsampled pairs, which does not meet the 5-seed full-dataset threshold).

---

## What Can Be Claimed

1. **Rigorous alias-safe benchmark**: Identifying drugs by canonical structure resolved 146 duplicate names ($1,537 \to 1,391$ molecules) and prevented same-molecule leakage across train and test partitions.
2. **Controlled negative result**: Predicted Tox21 risk profiles do not improve DDI severity prediction over 2D structure alone for seen or unseen drugs; they lower macro-F1 by 0.017 to 0.036 across S0, S1, and S2 (0 of 8 seeds improved).
3. **Redundancy, not random noise**: Real risk profiles significantly beat a deranged shuffled-profile control ($p < 0.05$ on all scenarios), confirming the profiles carry true drug-specific signal that is redundant with structural fingerprints.
4. **Correlation does not equal mechanism**: Although a small correlation ($\rho = 0.042$) between predicted target overlap and severity persists after controlling for structural similarity, popularity, ATC co-membership, and additive risk, synthetic stress tests demonstrate that purely structural confounding produces this exact signature.
5. **Calibrated abstention on unseen drugs**: Mondrian inductive conformal prediction provides valid coverage ($\approx 90\%$) on S0, S1, and S2, allowing the system to abstain when severity is ambiguous.

---

## What Cannot Be Claimed

1. **No predictive gain from toxicity**: It cannot be claimed that toxicity risk profiles, assay fingerprints, or predicted bio-activity improve DDI severity prediction.
2. **No biological mechanism confirmation**: It cannot be claimed that the shared-risk score confirms a biological interaction mechanism.
3. **No claims regarding CYP features**: CYP metabolism features cannot be claimed or reported as effective, because required datasets (`data/tdc_cyp`) were unavailable and no simulation was performed.
4. **No claims regarding full-scale GNN performance**: It cannot be claimed that GNN models perform better or worse with toxicity features until a full-scale run ($\ge 5$ seeds on all pairs) is executed.
5. **No clinical utility or prescribing safety**: The models are research prototypes trained on interacting pairs only (no non-interacting pairs) and cannot be used for clinical decisions.

---

## Open Items

1. **Full-scale GNN ablation**: Executing `run_ablation.py` with GNN variants ($A, B, B_{\text{shuf}}$) across $\ge 5$ seeds on the full 84,151 DDInter pair dataset.
2. **CYP metabolism profiling**: Evaluating CYP isoform inhibition features if the 5 TDC CYP benchmark datasets are acquired.
3. **Expanded non-interacting negative pairs**: Extending the benchmark beyond known interacting pairs to evaluate interaction detection in addition to severity grading.
