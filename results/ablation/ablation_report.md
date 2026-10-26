# DDI severity ablation report

## Setup

- **data source**: DDInter
- **unique pairs used**: 84151
- **seeds**: 0, 1, 2, 3, 4, 5, 6, 7
- **GNN architecture**: not run
- **profiler_mode**: crossfit
- **conformal alpha**: 0.1
- **note 1**: Drug identity by canonical molecule: 1537 names -> 1391 molecules (146 names merged).
- **note 2**: De-duplicated 43139 duplicate/self pairs (2168 had conflicting severities; the most severe was kept).
- **note 3**: Tox21 profiler mode: crossfit; 860/1391 molecules also appear in the Tox21 table.
- **note 4**: Dropped 0 pairs lacking a graph, profile or fingerprint for one drug (all models therefore see identical pairs).

## Models

- **Prior** - Always predicts the most common severity (floor)
- **DrugMean** - Per-drug average severity, no chemistry (tests 'is this drug just dangerous?')
- **RF_fp** - Fast tabular ablation: fingerprint forest (no toxicity features)
- **RF_fp+tox** - Fast tabular ablation: fingerprint forest + predicted Tox21 risk-fingerprint features
- **RF_fp+toxshuf** - CONTROL: fingerprint forest + risk profiles shuffled across drugs
- **RF_fp+ov** - Fingerprint forest + only the 4 scalar overlap features (dilution check)
- **RF_tox** - Forest on predicted Tox21 pair features ALONE (how much signal do they carry by themselves?)

## Results (mean ± std across seeds)

### S0: both drugs seen in training (~4134 test pairs)

| Model | Accuracy | Macro-F1 | Minor F1 | Moderate F1 | Major F1 | Seeds |
|---|---|---|---|---|---|---|
| Prior | 0.737 ± 0.011 | 0.283 ± 0.002 | 0.000 ± 0.000 | 0.848 ± 0.007 | 0.000 ± 0.000 | 8 |
| DrugMean | 0.699 ± 0.012 | 0.588 ± 0.012 | 0.336 ± 0.029 | 0.773 ± 0.012 | 0.654 ± 0.020 | 8 |
| RF_fp | 0.871 ± 0.008 | 0.780 ± 0.012 | 0.688 ± 0.028 | 0.917 ± 0.005 | 0.736 ± 0.023 | 8 |
| RF_fp+tox | 0.866 ± 0.009 | 0.761 ± 0.016 | 0.665 ± 0.036 | 0.915 ± 0.006 | 0.702 ± 0.030 | 8 |
| RF_fp+toxshuf | 0.852 ± 0.010 | 0.730 ± 0.017 | 0.616 ± 0.037 | 0.906 ± 0.006 | 0.669 ± 0.035 | 8 |
| RF_fp+ov | 0.874 ± 0.007 | 0.785 ± 0.012 | 0.699 ± 0.031 | 0.919 ± 0.005 | 0.737 ± 0.024 | 8 |
| RF_tox | 0.776 ± 0.009 | 0.495 ± 0.019 | 0.286 ± 0.040 | 0.866 ± 0.006 | 0.334 ± 0.035 | 8 |

### S1: one new drug (~23640 test pairs)

| Model | Accuracy | Macro-F1 | Minor F1 | Moderate F1 | Major F1 | Seeds |
|---|---|---|---|---|---|---|
| Prior | 0.738 ± 0.015 | 0.283 ± 0.003 | 0.000 ± 0.000 | 0.849 ± 0.010 | 0.000 ± 0.000 | 8 |
| DrugMean | 0.717 ± 0.019 | 0.540 ± 0.016 | 0.296 ± 0.016 | 0.811 ± 0.016 | 0.512 ± 0.024 | 8 |
| RF_fp | 0.806 ± 0.017 | 0.634 ± 0.025 | 0.525 ± 0.048 | 0.880 ± 0.011 | 0.497 ± 0.034 | 8 |
| RF_fp+tox | 0.799 ± 0.017 | 0.598 ± 0.028 | 0.467 ± 0.059 | 0.878 ± 0.011 | 0.451 ± 0.037 | 8 |
| RF_fp+toxshuf | 0.791 ± 0.017 | 0.570 ± 0.026 | 0.419 ± 0.050 | 0.874 ± 0.011 | 0.417 ± 0.032 | 8 |
| RF_fp+ov | 0.805 ± 0.017 | 0.630 ± 0.025 | 0.519 ± 0.050 | 0.880 ± 0.011 | 0.492 ± 0.035 | 8 |
| RF_tox | 0.753 ± 0.015 | 0.403 ± 0.012 | 0.156 ± 0.038 | 0.855 ± 0.010 | 0.199 ± 0.040 | 8 |

### S2: both drugs new (~3381 test pairs)

| Model | Accuracy | Macro-F1 | Minor F1 | Moderate F1 | Major F1 | Seeds |
|---|---|---|---|---|---|---|
| Prior | 0.741 ± 0.036 | 0.283 ± 0.008 | 0.000 ± 0.000 | 0.850 ± 0.024 | 0.000 ± 0.000 | 8 |
| DrugMean | 0.741 ± 0.036 | 0.283 ± 0.008 | 0.000 ± 0.000 | 0.850 ± 0.024 | 0.000 ± 0.000 | 8 |
| RF_fp | 0.747 ± 0.035 | 0.371 ± 0.022 | 0.172 ± 0.028 | 0.853 ± 0.023 | 0.088 ± 0.050 | 8 |
| RF_fp+tox | 0.746 ± 0.036 | 0.354 ± 0.024 | 0.143 ± 0.050 | 0.852 ± 0.024 | 0.068 ± 0.043 | 8 |
| RF_fp+toxshuf | 0.746 ± 0.036 | 0.342 ± 0.016 | 0.109 ± 0.030 | 0.853 ± 0.023 | 0.063 ± 0.041 | 8 |
| RF_fp+ov | 0.748 ± 0.034 | 0.370 ± 0.020 | 0.171 ± 0.038 | 0.853 ± 0.023 | 0.086 ± 0.047 | 8 |
| RF_tox | 0.735 ± 0.033 | 0.307 ± 0.011 | 0.033 ± 0.029 | 0.846 ± 0.022 | 0.041 ± 0.024 | 8 |

## Headline claim: do predicted-toxicity features help?

Supported only if the feature model beats BOTH the no-feature model and the shuffled-profile control.

- **S0** - NOT SUPPORTED (RF_fp+tox vs RF_fp and RF_fp+toxshuf): vs no-features: -0.020 (p=0.008); vs shuffled control: +0.030 (p=0.008)
- **S1** - NOT SUPPORTED (RF_fp+tox vs RF_fp and RF_fp+toxshuf): vs no-features: -0.036 (p=0.008); vs shuffled control: +0.028 (p=0.008)
- **S2** - NOT SUPPORTED (RF_fp+tox vs RF_fp and RF_fp+toxshuf): vs no-features: -0.017 (p=0.008); vs shuffled control: +0.013 (p=0.023)

## Key comparisons (paired by seed, macro-F1)

- RF_fp+tox vs RF_fp on S0 (macro_f1): -0.020, wins 0/8, p=0.008 -- RF_fp+tox is WORSE than RF_fp.
- RF_fp+tox vs RF_fp on S1 (macro_f1): -0.036, wins 0/8, p=0.008 -- RF_fp+tox is WORSE than RF_fp.
- RF_fp+tox vs RF_fp on S2 (macro_f1): -0.017, wins 0/8, p=0.008 -- RF_fp+tox is WORSE than RF_fp.
- RF_fp+tox vs RF_fp+toxshuf on S0 (macro_f1): +0.030, wins 8/8, p=0.008 -- RF_fp+tox IMPROVES on RF_fp+toxshuf.
- RF_fp+tox vs RF_fp+toxshuf on S1 (macro_f1): +0.028, wins 8/8, p=0.008 -- RF_fp+tox IMPROVES on RF_fp+toxshuf.
- RF_fp+tox vs RF_fp+toxshuf on S2 (macro_f1): +0.013, wins 7/8, p=0.023 -- RF_fp+tox IMPROVES on RF_fp+toxshuf.
- RF_fp vs DrugMean on S0 (macro_f1): +0.193, wins 8/8, p=0.008 -- RF_fp IMPROVES on DrugMean.
- RF_fp vs DrugMean on S1 (macro_f1): +0.095, wins 8/8, p=0.008 -- RF_fp IMPROVES on DrugMean.
- RF_fp vs DrugMean on S2 (macro_f1): +0.087, wins 8/8, p=0.008 -- RF_fp IMPROVES on DrugMean.
- RF_fp+ov vs RF_fp on S0 (macro_f1): +0.005, wins 7/8, p=0.023 -- RF_fp+ov IMPROVES on RF_fp.
- RF_fp+ov vs RF_fp on S1 (macro_f1): -0.004, wins 2/8, p=0.078 -- no reliable difference.
- RF_fp+ov vs RF_fp on S2 (macro_f1): -0.001, wins 4/8, p=0.641 -- no reliable difference.
- RF_fp vs RF_tox on S0 (macro_f1): +0.285, wins 8/8, p=0.008 -- RF_fp IMPROVES on RF_tox.
- RF_fp vs RF_tox on S1 (macro_f1): +0.231, wins 8/8, p=0.008 -- RF_fp IMPROVES on RF_tox.
- RF_fp vs RF_tox on S2 (macro_f1): +0.064, wins 8/8, p=0.008 -- RF_fp IMPROVES on RF_tox.
- RF_tox vs DrugMean on S0 (macro_f1): -0.093, wins 0/8, p=0.008 -- RF_tox is WORSE than DrugMean.
- RF_tox vs DrugMean on S1 (macro_f1): -0.137, wins 0/8, p=0.008 -- RF_tox is WORSE than DrugMean.
- RF_tox vs DrugMean on S2 (macro_f1): +0.023, wins 8/8, p=0.008 -- RF_tox IMPROVES on DrugMean.
- RF_fp vs Prior on S0 (macro_f1): +0.497, wins 8/8, p=0.008 -- RF_fp IMPROVES on Prior.
- RF_fp vs Prior on S1 (macro_f1): +0.351, wins 8/8, p=0.008 -- RF_fp IMPROVES on Prior.
- RF_fp vs Prior on S2 (macro_f1): +0.087, wins 8/8, p=0.008 -- RF_fp IMPROVES on Prior.
- DrugMean vs Prior on S0 (macro_f1): +0.305, wins 8/8, p=0.008 -- DrugMean IMPROVES on Prior.
- DrugMean vs Prior on S1 (macro_f1): +0.257, wins 8/8, p=0.008 -- DrugMean IMPROVES on Prior.
- DrugMean vs Prior on S2 (macro_f1): +0.000, wins 0/8 -- no reliable difference (test not applicable).

## Does shared predicted risk track severity? (model-free check)

Spearman correlations with true severity. "Additive" = each drug's own mean risk summed; "partial" = overlap after removing that additive effect.

| Scenario | rho (overlap) | rho (additive risk) | rho (overlap, given additive) | n pairs |
|---|---|---|---|---|
| S0 | 0.066 | 0.050 | 0.065 | 4031 |
| S1 | 0.092 | 0.063 | 0.110 | 23317 |
| S2 | 0.088 | 0.055 | 0.128 | 3381 |
| ALL | 0.081 | 0.065 | 0.068 | 84151 |

p-values are omitted on purpose: pairs share drugs, so standard tests badly overstate significance with tens of thousands of pairs. Judge by effect size. If the partial correlation is near zero, the overlap score adds nothing beyond how risky each drug is on its own.

## Abstain mode (split-conformal, calibrated on validation drugs)

| Model | Scenario | Target coverage | Coverage | Answer rate | Accuracy when answering | Accuracy if forced to answer all |
|---|---|---|---|---|---|---|
| Prior | S0 | 0.90 | 1.000 | 0.000 | nan | 0.737 |
| Prior | S1 | 0.90 | 1.000 | 0.000 | nan | 0.738 |
| Prior | S2 | 0.90 | 1.000 | 0.000 | nan | 0.741 |
| DrugMean | S0 | 0.90 | 0.864 | 0.275 | 0.614 | 0.699 |
| DrugMean | S1 | 0.90 | 0.897 | 0.174 | 0.545 | 0.717 |
| DrugMean | S2 | 0.90 | 0.949 | 0.000 | nan | 0.741 |
| RF_fp | S0 | 0.90 | 0.905 | 0.527 | 0.880 | 0.871 |
| RF_fp | S1 | 0.90 | 0.901 | 0.333 | 0.843 | 0.806 |
| RF_fp | S2 | 0.90 | 0.924 | 0.111 | 0.791 | 0.747 |
| RF_fp+tox | S0 | 0.90 | 0.912 | 0.497 | 0.885 | 0.866 |
| RF_fp+tox | S1 | 0.90 | 0.900 | 0.306 | 0.834 | 0.799 |
| RF_fp+tox | S2 | 0.90 | 0.918 | 0.105 | 0.764 | 0.746 |
| RF_fp+toxshuf | S0 | 0.90 | 0.908 | 0.492 | 0.877 | 0.852 |
| RF_fp+toxshuf | S1 | 0.90 | 0.901 | 0.305 | 0.830 | 0.791 |
| RF_fp+toxshuf | S2 | 0.90 | 0.925 | 0.095 | 0.763 | 0.746 |
| RF_fp+ov | S0 | 0.90 | 0.908 | 0.529 | 0.883 | 0.874 |
| RF_fp+ov | S1 | 0.90 | 0.901 | 0.332 | 0.841 | 0.805 |
| RF_fp+ov | S2 | 0.90 | 0.922 | 0.111 | 0.784 | 0.748 |
| RF_tox | S0 | 0.90 | 0.914 | 0.173 | 0.820 | 0.776 |
| RF_tox | S1 | 0.90 | 0.894 | 0.120 | 0.717 | 0.753 |
| RF_tox | S2 | 0.90 | 0.876 | 0.068 | 0.520 | 0.735 |

Coverage can fall below target on S1/S2 because new drugs break the exchangeability assumption.

## How to read this honestly

- Claims need at least 5 seeds; fewer is reported as inconclusive.
- Many comparisons are listed; at p < 0.05 roughly 1 in 20 null comparisons will look significant by chance. Treat isolated single-scenario wins with suspicion and trust the strict headline rule above.
- B beating A only supports the toxicity-fingerprint idea if B also beats **B_shuf** (same extra capacity, no real information). The same logic applies to RF_fp+tox versus RF_fp+toxshuf.
- A beating **DrugMean** on S1/S2 is what shows the GNN uses chemistry, not just drug identity.
- Numbers here are not comparable to papers reporting binary interaction detection on balanced positive/negative pairs; this is 3-class severity among known interactions.
