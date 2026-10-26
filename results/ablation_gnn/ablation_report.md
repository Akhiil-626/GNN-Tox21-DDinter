# DDI severity ablation report

## Setup

- **data source**: DDInter
- **unique pairs used**: 10000
- **seeds**: 0, 1
- **GNN architecture**: gcn
- **profiler_mode**: crossfit
- **conformal alpha**: 0.1
- **note 1**: Drug identity by canonical molecule: 1537 names -> 1391 molecules (146 names merged).
- **note 2**: De-duplicated 43139 duplicate/self pairs (2168 had conflicting severities; the most severe was kept).
- **note 3**: Tox21 profiler mode: crossfit; 860/1391 molecules also appear in the Tox21 table.
- **note 4**: Dropped 0 pairs lacking a graph, profile or fingerprint for one drug (all models therefore see identical pairs).

## Models

- **Prior** - Always predicts the most common severity (floor)
- **DrugMean** - Per-drug average severity, no chemistry (tests 'is this drug just dangerous?')
- **A** - GNN, structure only (order-independent head)
- **B** - A + predicted Tox21 risk-fingerprint features
- **B_shuf** - CONTROL: B with risk profiles shuffled across drugs (same capacity, no information)

## Results (mean ± std across seeds)

### S0: both drugs seen in training (~501 test pairs)

| Model | Accuracy | Macro-F1 | Minor F1 | Moderate F1 | Major F1 | Seeds |
|---|---|---|---|---|---|---|
| Prior | 0.732 ± 0.001 | 0.282 ± 0.000 | 0.000 ± 0.000 | 0.845 ± 0.001 | 0.000 ± 0.000 | 2 |
| DrugMean | 0.613 ± 0.022 | 0.507 ± 0.024 | 0.292 ± 0.054 | 0.707 ± 0.027 | 0.520 ± 0.009 | 2 |
| A | 0.592 ± 0.082 | 0.473 ± 0.011 | 0.284 ± 0.052 | 0.696 ± 0.103 | 0.440 ± 0.018 | 2 |
| B | 0.582 ± 0.048 | 0.477 ± 0.017 | 0.318 ± 0.101 | 0.681 ± 0.073 | 0.430 ± 0.022 | 2 |
| B_shuf | 0.593 ± 0.027 | 0.470 ± 0.003 | 0.275 ± 0.039 | 0.711 ± 0.028 | 0.425 ± 0.003 | 2 |

### S1: one new drug (~2716 test pairs)

| Model | Accuracy | Macro-F1 | Minor F1 | Moderate F1 | Major F1 | Seeds |
|---|---|---|---|---|---|---|
| Prior | 0.717 ± 0.010 | 0.278 ± 0.002 | 0.000 ± 0.000 | 0.835 ± 0.007 | 0.000 ± 0.000 | 2 |
| DrugMean | 0.665 ± 0.007 | 0.503 ± 0.003 | 0.245 ± 0.008 | 0.768 ± 0.008 | 0.496 ± 0.008 | 2 |
| A | 0.549 ± 0.087 | 0.434 ± 0.051 | 0.207 ± 0.060 | 0.661 ± 0.094 | 0.435 ± 0.002 | 2 |
| B | 0.573 ± 0.049 | 0.453 ± 0.028 | 0.234 ± 0.018 | 0.674 ± 0.068 | 0.452 ± 0.002 | 2 |
| B_shuf | 0.548 ± 0.044 | 0.428 ± 0.029 | 0.202 ± 0.029 | 0.666 ± 0.049 | 0.414 ± 0.010 | 2 |

### S2: both drugs new (~388 test pairs)

| Model | Accuracy | Macro-F1 | Minor F1 | Moderate F1 | Major F1 | Seeds |
|---|---|---|---|---|---|---|
| Prior | 0.691 ± 0.013 | 0.272 ± 0.003 | 0.000 ± 0.000 | 0.817 ± 0.009 | 0.000 ± 0.000 | 2 |
| DrugMean | 0.691 ± 0.013 | 0.272 ± 0.003 | 0.000 ± 0.000 | 0.817 ± 0.009 | 0.000 ± 0.000 | 2 |
| A | 0.513 ± 0.089 | 0.423 ± 0.065 | 0.255 ± 0.136 | 0.616 ± 0.107 | 0.396 ± 0.046 | 2 |
| B | 0.552 ± 0.020 | 0.424 ± 0.042 | 0.182 ± 0.129 | 0.652 ± 0.034 | 0.437 ± 0.036 | 2 |
| B_shuf | 0.527 ± 0.047 | 0.406 ± 0.034 | 0.189 ± 0.077 | 0.650 ± 0.051 | 0.378 ± 0.026 | 2 |

## Headline claim: do predicted-toxicity features help?

Supported only if the feature model beats BOTH the no-feature model and the shuffled-profile control.

- **S0** - INCONCLUSIVE (B vs A and B_shuf): vs no-features: +0.003 (p=nan); vs shuffled control: +0.006 (p=nan)
- **S1** - INCONCLUSIVE (B vs A and B_shuf): vs no-features: +0.019 (p=nan); vs shuffled control: +0.026 (p=nan)
- **S2** - INCONCLUSIVE (B vs A and B_shuf): vs no-features: +0.001 (p=nan); vs shuffled control: +0.018 (p=nan)

## Key comparisons (paired by seed, macro-F1)

- B vs A on S0 (macro_f1): +0.003 over 2 seed(s) -- INCONCLUSIVE (need >= 5 seeds before claiming anything).
- B vs A on S1 (macro_f1): +0.019 over 2 seed(s) -- INCONCLUSIVE (need >= 5 seeds before claiming anything).
- B vs A on S2 (macro_f1): +0.001 over 2 seed(s) -- INCONCLUSIVE (need >= 5 seeds before claiming anything).
- B vs B_shuf on S0 (macro_f1): +0.006 over 2 seed(s) -- INCONCLUSIVE (need >= 5 seeds before claiming anything).
- B vs B_shuf on S1 (macro_f1): +0.026 over 2 seed(s) -- INCONCLUSIVE (need >= 5 seeds before claiming anything).
- B vs B_shuf on S2 (macro_f1): +0.018 over 2 seed(s) -- INCONCLUSIVE (need >= 5 seeds before claiming anything).
- A vs DrugMean on S0 (macro_f1): -0.033 over 2 seed(s) -- INCONCLUSIVE (need >= 5 seeds before claiming anything).
- A vs DrugMean on S1 (macro_f1): -0.069 over 2 seed(s) -- INCONCLUSIVE (need >= 5 seeds before claiming anything).
- A vs DrugMean on S2 (macro_f1): +0.150 over 2 seed(s) -- INCONCLUSIVE (need >= 5 seeds before claiming anything).
- B vs DrugMean on S0 (macro_f1): -0.030 over 2 seed(s) -- INCONCLUSIVE (need >= 5 seeds before claiming anything).
- B vs DrugMean on S1 (macro_f1): -0.050 over 2 seed(s) -- INCONCLUSIVE (need >= 5 seeds before claiming anything).
- B vs DrugMean on S2 (macro_f1): +0.151 over 2 seed(s) -- INCONCLUSIVE (need >= 5 seeds before claiming anything).
- DrugMean vs Prior on S0 (macro_f1): +0.225 over 2 seed(s) -- INCONCLUSIVE (need >= 5 seeds before claiming anything).
- DrugMean vs Prior on S1 (macro_f1): +0.225 over 2 seed(s) -- INCONCLUSIVE (need >= 5 seeds before claiming anything).
- DrugMean vs Prior on S2 (macro_f1): +0.000 over 2 seed(s) -- INCONCLUSIVE (need >= 5 seeds before claiming anything).

## Does shared predicted risk track severity? (model-free check)

Spearman correlations with true severity. "Additive" = each drug's own mean risk summed; "partial" = overlap after removing that additive effect.

| Scenario | rho (overlap) | rho (additive risk) | rho (overlap, given additive) | n pairs |
|---|---|---|---|---|
| S0 | 0.053 | 0.039 | 0.057 | 494 |
| S1 | 0.062 | 0.047 | 0.062 | 2748 |
| S2 | 0.143 | 0.094 | 0.173 | 389 |
| ALL | 0.094 | 0.075 | 0.081 | 10000 |

p-values are omitted on purpose: pairs share drugs, so standard tests badly overstate significance with tens of thousands of pairs. Judge by effect size. If the partial correlation is near zero, the overlap score adds nothing beyond how risky each drug is on its own.

## Abstain mode (split-conformal, calibrated on validation drugs)

| Model | Scenario | Target coverage | Coverage | Answer rate | Accuracy when answering | Accuracy if forced to answer all |
|---|---|---|---|---|---|---|
| Prior | S0 | 0.90 | 1.000 | 0.000 | nan | 0.732 |
| Prior | S1 | 0.90 | 1.000 | 0.000 | nan | 0.717 |
| Prior | S2 | 0.90 | 1.000 | 0.000 | nan | 0.691 |
| DrugMean | S0 | 0.90 | 0.881 | 0.197 | 0.560 | 0.613 |
| DrugMean | S1 | 0.90 | 0.925 | 0.142 | 0.556 | 0.665 |
| DrugMean | S2 | 0.90 | 0.951 | 0.000 | nan | 0.691 |
| A | S0 | 0.90 | 0.933 | 0.126 | 0.558 | 0.592 |
| A | S1 | 0.90 | 0.892 | 0.133 | 0.450 | 0.549 |
| A | S2 | 0.90 | 0.892 | 0.129 | 0.403 | 0.513 |
| B | S0 | 0.90 | 0.918 | 0.165 | 0.615 | 0.582 |
| B | S1 | 0.90 | 0.901 | 0.172 | 0.553 | 0.573 |
| B | S2 | 0.90 | 0.886 | 0.161 | 0.510 | 0.552 |
| B_shuf | S0 | 0.90 | 0.920 | 0.102 | 0.508 | 0.593 |
| B_shuf | S1 | 0.90 | 0.894 | 0.106 | 0.346 | 0.548 |
| B_shuf | S2 | 0.90 | 0.885 | 0.107 | 0.276 | 0.527 |

Coverage can fall below target on S1/S2 because new drugs break the exchangeability assumption.

## How to read this honestly

- Claims need at least 5 seeds; fewer is reported as inconclusive.
- Many comparisons are listed; at p < 0.05 roughly 1 in 20 null comparisons will look significant by chance. Treat isolated single-scenario wins with suspicion and trust the strict headline rule above.
- B beating A only supports the toxicity-fingerprint idea if B also beats **B_shuf** (same extra capacity, no real information). The same logic applies to RF_fp+tox versus RF_fp+toxshuf.
- A beating **DrugMean** on S1/S2 is what shows the GNN uses chemistry, not just drug identity.
- Numbers here are not comparable to papers reporting binary interaction detection on balanced positive/negative pairs; this is 3-class severity among known interactions.
