# Novelty, Evidence and Limits

## 1. The question this project answers

> **Does a drug's toxicity profile, predicted from its structure alone, help predict how severe its interaction with another drug will be, including for drugs the model has never seen?**

The project built a controlled way to answer it. **On the tabular evidence so far the answer is no** (section 6). That is a result, not a failure, and it shapes what can honestly be claimed (section 2).

## 2. Claims you may make, and claims you may not

### May claim (each is backed by a number in section 6 or a test in the repository)

1. **A leakage-safe severity benchmark for DDInter.** Drugs are identified by canonical molecule, not by name; pairs are de-duplicated; splits are by drug into S0 (both seen), S1 (one new), S2 (both new); and leakage is asserted on every split. *Measured finding:* 146 drug names were duplicates of other molecules (1,537 names became 1,391 molecules) and 2,168 duplicate pairs carried conflicting severities. Name-based splitting would have put the same molecule on both sides of the train/test boundary.
2. **Chemistry-free floors that new-drug claims must beat.** A majority-class floor and a per-drug-average baseline with an explicit back-off. On two new drugs (S2) structure gains only 0.088 macro-F1 over the floor and accuracy is 0.747 versus 0.741.
3. **A controlled negative result.** Predicted Tox21 risk profiles, made leak-free by cross-fitting, did **not** improve severity prediction for a fingerprint model on seen or unseen drugs: they lowered macro-F1 by 0.017 to 0.036 (0 of 8 seeds improved, each scenario). Controls show why: profiles beat a shuffled-profile control (so they carry real drug-specific information) but that information is redundant with fingerprints, and 4 summary overlap features made no reliable difference on new drugs.
4. **A method note on leakage in feature stacking.** Cross-fitted profiling (a drug is never profiled by a model trained on it) and a rule that an added feature must beat a shuffled control, not just a baseline, before it is claimed to help.
5. **A cautionary finding about correlation-based "mechanism" evidence.** Stress tests show a shared-risk association can pass similarity, popularity and class controls, and even a structure-matched permutation null, when the true cause is purely structural. Such an association is therefore *unconfirmed* until it passes a predictive test, which here it did not.
6. **Calibrated abstention that held on unseen drugs.** Conformal sets reached about 0.90 coverage on S0, S1 and S2 for the fingerprint model (target 0.90), at the cost of answering only 53%, 33% and 11% of pairs.

Phrase all of these as "to our knowledge" and cite the closest prior work (section 4) after running the literature checklist in section 7.

### May NOT claim

- That toxicity or CYP profiles improve DDI prediction (not supported).
- A shared-mechanism explanation for the small overlap association (unconfirmed, possibly structural).
- "First DDI model", "state of the art", "best accuracy", or any comparison to published scores on different data or labels.
- Anything about GNN performance until the GNN study has been run (section 8).
- Engineering items as research novelty: the order-independent head, the dashboard, atom saliency.

## 3. What is and is not new

| Element | Status |
|---|---|
| GNN dual-encoder DDI, atom saliency, Flask dashboard | Not novel |
| Conformal prediction for DDI | Exists in the literature; a safety feature here, not a contribution |
| Substructure / cross-attention interpretability | Exists; not implemented here |
| Mechanism-aware DDI from curated targets / enzymes / pathways | Exists; needs curated data that new drugs lack |
| Predicted Tox21 profiles as DDI-severity features, tested on unseen drugs | **No direct prior match found in a limited search; the result here is negative** |
| Alias-safe, severity-graded S0/S1/S2 benchmark with drug-only floors | Candidate contribution (rigor) |
| Shuffled-profile control plus strict "must beat both" rule | Methodological contribution |
| Cross-fitted profiles to prevent feature leakage | Methodological contribution |

## 4. Literature positioning

Found in a targeted search; abstracts or excerpts only, and several items are recent preprints that may not be peer reviewed. **Verify each before citing.**

- **DDInter 2.0** (data; severity-annotated records): https://academic.oup.com/nar/article/53/D1/D1356/7740584
- **SSI-DDI**, **GMPNN-CS** (substructure-level, co-attention DDI): https://academic.oup.com/bib/article/23/1/bbab441/6409692
- **ColdDDI** (2026 cold-start benchmark; difficulty tracks shared enzymes/transporters/targets): https://arxiv.org/pdf/2610.05590
- **MADRIGAL** (multimodal clinical-outcome model for drug combinations; binary outcomes, no severity grading): https://arxiv.org/pdf/2503.02781
- **Pharmacogenomic knowledge-graph augmentation for DDI** (2026 preprint; CYP flags; large AUC drop under drug-level splits): https://arxiv.org/pdf/2606.07698
- **MARD** (mechanism-level DDI): https://arxiv.org/pdf/2606.12578
- **WeightedCPDDI** (conformal prediction for DDI): https://scholars.cityu.edu.hk/en/publications/trustworthy-drug-drug-interaction-prediction-model-via-weighted-a/
- **HODDI** (higher-order interactions dataset): https://arxiv.org/pdf/2502.06274
- **Structure-only severity of drug-pair adverse reactions**: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC13610676/

## 5. How the evidence is produced

0. **A drug is its molecule, not its name.** Names are mapped to canonical molecule keys first.
1. **Pairs are de-duplicated** (unordered); conflicting severities keep the most severe label.
2. **Splits are by drug** over several seeds: S0 both seen (pair withheld), S1 exactly one new, S2 both new; validation uses separate drugs. `assert_no_leakage` runs on every split.
3. **Risk profiles are cross-fitted.** A drug in the labelled Tox21 table is profiled only by the fold model that never trained on it.
4. **All models see identical pairs and splits per seed.**
5. **Floors and controls:** Prior, DrugMean (with back-off), fingerprint forest, shuffled-profile control, a 4-feature overlap model, and a toxicity-only model.
6. **Headline rule (strict).** "Toxicity features help" is SUPPORTED for a scenario only if the with-features model beats **both** the no-features model and the shuffled control with a reliable paired improvement (Wilcoxon, at least 6 paired seeds).
7. **Overlap association** is tested with controls for own-risk, fingerprint similarity, class proxy and popularity, a drug-level bootstrap, and global plus structure-matched permutation nulls. A passing result is labelled **unconfirmed**, never supportive (section 2, item 5).

## 6. Results so far (tabular study, 8 seeds, after the molecule-identity fix)

DDInter: 84,151 unique pairs, 1,391 molecules; Tox21 profiler cross-fitted (mean held-out ROC-AUC 0.807; 860 of 1,391 molecules were in the Tox21 table).

| Model (macro-F1) | S0 | S1 | S2 |
|---|---|---|---|
| Prior (majority class) | 0.283 | 0.283 | 0.283 |
| DrugMean (no chemistry) | 0.588 | 0.540 | 0.283 |
| Fingerprint forest | 0.780 | 0.634 | 0.371 |
| + predicted Tox21 features | 0.761 | 0.598 | 0.354 |
| + shuffled-profile control | 0.730 | 0.570 | 0.342 |
| + 4 overlap features only | 0.785 | 0.630 | 0.370 |
| Tox21 features alone | 0.495 | 0.403 | 0.307 |

- Headline claim: **NOT SUPPORTED** in S0, S1 and S2.
- Tox21 features alone are below the DrugMean floor on seen drugs and barely above the prior on S2.
- The model-free overlap correlation with severity is small (rho 0.066, 0.092, 0.088 on S0, S1, S2) and survives removal of each drug's own risk (partial rho 0.065, 0.110, 0.128). Section 2 item 5 explains why this does not confirm a mechanism.
- Moving from the first run (before the identity fix) to this one lowered fingerprint-forest macro-F1 from 0.805 to 0.780 on S0 and from 0.639 to 0.634 on S1, consistent with some alias leakage in the first run.
- GNN variants (A, B, B_shuf) have **not** been run; the tabular result does not settle them.

## 7. Before you claim novelty

Run and document your own searches (Google Scholar, PubMed, arXiv), for example `Tox21 drug-drug interaction severity`, `predicted toxicity profile DDI cold-start`, `ADMET features DDI severity DDInter`, `molecule identity leakage DDInter`, `alias leakage drug-drug interaction benchmark`. Read MADRIGAL's supplement. Phrase claims as "to our knowledge" and name the closest prior work.

## 8. Remaining work before a final claim

1. Overlap analysis (`python -m src.overlap_analysis`): rules the association in or out against the controls.
2. GNN smoke test, then the GNN study (A, B, B_shuf). Report it whatever it shows.
3. Optional CYP features (needs the five TDC CYP files).

## 9. Limitations

- **Proxy signal.** Tox21 assays are cell-based screens, mostly on environmental chemicals; they are a proxy for biological stress, not a clinical interaction mechanism. The dashboard panel is labelled experimental.
- **No negatives.** DDInter lists known interactions only; the model ranks severity given an interaction and cannot say two drugs do not interact.
- **Label noise.** 2,168 duplicate pairs had conflicting severities (resolved to the most severe).
- **Name resolution loses drugs.** Drugs PubChem cannot resolve are dropped; all models see the same remaining pairs.
- **Two profile regimes.** Molecules in the Tox21 table get a single held-out fold model; others get an ensemble mean. The analysis reports both subsets separately.
- **Correlation cannot confirm a mechanism** (section 2, item 5).
- **Conformal coverage** assumes exchangeability; new-drug scenarios violate it somewhat (empirically it held at about 0.90 to 0.92).
- **Not medical advice.** This is a research prototype. Do not use it to make prescribing decisions.

## 10. Verification status

Tested in the build environment (no network, no torch, no RDKit): 80 unit and integration tests (splits, de-duplication, molecule-identity merge, leakage checks, risk features, overlap diagnostics, bootstrap and permutation machinery, conformal prediction, baselines with regression tests, fold balancing, cross-fit selection, statistics and verdict rules, report rendering, synthetic end-to-end runs) plus a stub-DOM test of the dashboard rendering (14 assertions).

Run on real data by the project owner: `crossfit --task tox21` and the tabular `run_ablation --no_gnn` (section 6).

**Never executed:** `SymmetricDDI` training and the GNN variants, `ddi_inference.py`, the patched Flask endpoints, CYP cross-fitting, and `overlap_analysis` on real data. `tests/test_ddi_torch.py` covers model-level properties once torch is installed.
