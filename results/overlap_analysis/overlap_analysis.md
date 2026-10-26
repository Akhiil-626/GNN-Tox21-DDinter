# Overlap-lead analysis

Question: does the shared-predicted-toxicity score track DDI severity **beyond** structural similarity, therapeutic-class closeness, drug popularity and each drug's own risk?

## Setup

- **data source**: DDInter
- **profiler_mode**: crossfit
- **bootstrap replicates**: 300
- **permutations**: 300
- **controls**: additive risk, fingerprint Tanimoto, ATC-file co-membership (proxy), log popularity
- **note 1**: Drug identity by canonical molecule: 1537 names -> 1391 molecules (146 names merged).
- **note 2**: De-duplicated 43139 duplicate/self pairs (2168 had conflicting severities; the most severe was kept).
- **note 3**: Tox21 profiler mode: crossfit; 860/1391 molecules also appear in the Tox21 table.
- **note 4**: Dropped 0 pairs lacking a graph, profile or fingerprint for one drug (all models therefore see identical pairs).

## Results

| Subset | Pairs | rho overlap | rho (controlling additive risk) | rho (controlling ALL) | 95% drug-bootstrap CI | Global null p95 | Structure-matched null p95 | Null retention | Status |
|---|---|---|---|---|---|---|---|---|---|
| ALL | 84151 | 0.081 | 0.068 | 0.042 | [0.008, 0.077] | 0.034 | 0.034 | 0.47 | **NOT EXPLAINED AWAY (UNCONFIRMED)** |
| BOTH_IN_TOX21_TABLE | 34634 | 0.042 | 0.089 | 0.067 | [0.029, 0.104] | 0.037 | 0.059 | 0.45 | **NOT EXPLAINED AWAY (UNCONFIRMED)** |
| AT_LEAST_ONE_OUTSIDE_TABLE | 49517 | 0.095 | 0.044 | 0.015 | [-0.029, 0.058] | 0.043 | 0.028 | 0.47 | **EXPLAINED AWAY** |

### How strongly do the controls themselves track severity? (Spearman rho)

| Subset | additive risk | fingerprint similarity | ATC co-membership | log popularity |
|---|---|---|---|---|
| ALL | 0.065 | 0.055 | 0.132 | 0.200 |
| BOTH_IN_TOX21_TABLE | 0.016 | 0.029 | 0.133 | 0.165 |
| AT_LEAST_ONE_OUTSIDE_TABLE | 0.086 | 0.078 | 0.124 | 0.222 |

## Reading this honestly

- On all pairs a small association remains after the controls (partial rho 0.042, about 0.2% of rank variance). **This does not confirm a profile-specific effect.** Stress tests show that purely structural confounding produces this same result, because fingerprints are noisy proxies for what the risk profiles encode. Only a predictive test can support the claim: check whether adding the profiles improves held-out severity prediction (the ablation).
- "Null retention" is how much of the real overlap score's structure the matched shuffle keeps.
- Controls are imperfect proxies. In stress tests a purely structure-driven association still passed every control and both nulls, so a passing result is unconfirmed, never supportive on its own.
- The ATC co-membership proxy is coarse (a drug also appears in the files of its partners' classes).
- Pairs share drugs, so intervals come from resampling drugs, not pairs.
- This is association only. It is not a clinical statement and not a causal claim.
