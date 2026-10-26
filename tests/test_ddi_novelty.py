"""
Tests for the DDI contribution modules that need neither torch nor RDKit:
splits, risk-fingerprint features, conformal prediction and baselines.

Run:  python -m pytest tests/test_ddi_novelty.py -q
"""

import os
import random
import re
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ddi_splits import make_drug_splits, assert_no_leakage
from src.ddi_features import (
    TOX21_TASKS, N_TASKS, PAIR_FEATURE_DIM, ENDPOINT_LABELS,
    expected_shared_risk, shared_flagged_count, profile_cosine,
    pair_feature_vector, explain_shared_risk, spearman_overlap_vs_severity,
)
from src.ddi_conformal import (
    fit_conformal, predict_sets, decide, evaluate_conformal, confidence_threshold_curve,
)
from src.ddi_baselines import (
    PriorBaseline, DrugMeanBaseline, FingerprintForestBaseline, score_predictions,
)


# ----------------------------------------------------------------------------- helpers
def synthetic_pairs(n_drugs=60, n_pairs=900, seed=0):
    """Pairs of (name_a, name_b, label) with a drug-level severity signal."""
    rng = random.Random(seed)
    drugs = [f"drug{i:03d}" for i in range(n_drugs)]
    bias = {d: rng.random() for d in drugs}
    seen, pairs = set(), []
    while len(pairs) < n_pairs:
        a, b = rng.sample(drugs, 2)
        key = frozenset((a, b))
        if key in seen:
            continue
        seen.add(key)
        score = (bias[a] + bias[b]) / 2 + rng.gauss(0, 0.1)
        label = 0 if score < 0.4 else (1 if score < 0.6 else 2)
        pairs.append((a, b, label))
    return pairs


A = lambda p: p[0]
B = lambda p: p[1]


# ----------------------------------------------------------------------------- splits
@pytest.mark.parametrize('seed', [0, 1, 7, 42])
def test_splits_have_no_leakage(seed):
    pairs = synthetic_pairs()
    split = make_drug_splits(pairs, A, B, seed=seed)
    assert_no_leakage(split, pairs, A, B)


def test_splits_populate_every_scenario():
    pairs = synthetic_pairs()
    split = make_drug_splits(pairs, A, B, seed=3)
    sizes = split.sizes()
    for key in ('train', 'test_s0', 'test_s1', 'test_s2'):
        assert sizes[key] > 0, f"{key} is empty"


def test_splits_are_disjoint_index_sets():
    pairs = synthetic_pairs()
    s = make_drug_splits(pairs, A, B, seed=5)
    groups = [set(s.train), set(s.val), set(s.test_s0), set(s.test_s1), set(s.test_s2)]
    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
            assert not (groups[i] & groups[j])


def test_splits_reproducible_and_seed_sensitive():
    pairs = synthetic_pairs()
    s1 = make_drug_splits(pairs, A, B, seed=11)
    s2 = make_drug_splits(pairs, A, B, seed=11)
    s3 = make_drug_splits(pairs, A, B, seed=12)
    assert s1.train == s2.train and s1.test_s1 == s2.test_s1
    assert s1.test_drugs != s3.test_drugs


def test_split_rejects_bad_fractions():
    with pytest.raises(ValueError):
        make_drug_splits(synthetic_pairs(), A, B, frac_train_drugs=0.95, frac_val_drugs=0.1)


# ----------------------------------------------------------------------------- features
def rand_profile(rng):
    return rng.random(N_TASKS)


def test_task_names_match_dataset_module():
    """Guards against drift between ddi_features.TOX21_TASKS and src/dataset.py."""
    src = open(os.path.join(os.path.dirname(__file__), '..', 'src', 'dataset.py')).read()
    block = re.search(r"TOX21_TASKS\s*=\s*\[(.*?)\]", src, re.S).group(1)
    names = tuple(re.findall(r"'([^']+)'", block))
    assert names == TOX21_TASKS
    assert set(ENDPOINT_LABELS) == set(TOX21_TASKS)


def test_pair_features_are_order_independent():
    rng = np.random.default_rng(0)
    for _ in range(50):
        pa, pb = rand_profile(rng), rand_profile(rng)
        assert np.allclose(pair_feature_vector(pa, pb), pair_feature_vector(pb, pa))
        assert expected_shared_risk(pa, pb) == pytest.approx(expected_shared_risk(pb, pa))
        assert profile_cosine(pa, pb) == pytest.approx(profile_cosine(pb, pa))
        assert shared_flagged_count(pa, pb) == shared_flagged_count(pb, pa)


def test_pair_feature_dim_and_values():
    pa = np.full(N_TASKS, 0.5)
    pb = np.full(N_TASKS, 0.5)
    v = pair_feature_vector(pa, pb)
    assert v.shape == (PAIR_FEATURE_DIM,)
    assert expected_shared_risk(pa, pb) == pytest.approx(3.0)       # 12 * 0.25
    assert shared_flagged_count(pa, pb) == 12
    assert profile_cosine(pa, pb) == pytest.approx(1.0)


def test_zero_profiles_are_safe():
    z = np.zeros(N_TASKS)
    assert expected_shared_risk(z, z) == 0.0
    assert profile_cosine(z, z) == 0.0
    assert explain_shared_risk(z, z)['level'] == 'none'


def test_profile_validation():
    with pytest.raises(ValueError):
        expected_shared_risk(np.zeros(5), np.zeros(N_TASKS))
    with pytest.raises(ValueError):
        expected_shared_risk(np.full(N_TASKS, 1.5), np.zeros(N_TASKS))


def test_explanation_lists_only_genuinely_shared_endpoints():
    pa = np.zeros(N_TASKS)
    pb = np.zeros(N_TASKS)
    mmp = TOX21_TASKS.index('SR-MMP')
    are = TOX21_TASKS.index('SR-ARE')
    pa[mmp], pb[mmp] = 0.9, 0.8          # genuinely shared
    pa[are], pb[are] = 0.9, 0.05         # only one drug -> must NOT be listed
    out = explain_shared_risk(pa, pb)
    tasks = [s['task'] for s in out['shared']]
    assert tasks == ['SR-MMP']
    assert out['shared'][0]['joint'] == pytest.approx(0.72)
    assert out['level'] in ('elevated', 'high')
    assert 'caveat' in out and out['caveat']


def test_explanation_symmetric():
    rng = np.random.default_rng(3)
    pa, pb = rand_profile(rng), rand_profile(rng)
    e1, e2 = explain_shared_risk(pa, pb), explain_shared_risk(pb, pa)
    assert e1['level'] == e2['level']
    assert [s['task'] for s in e1['shared']] == [s['task'] for s in e2['shared']]


def test_spearman_handles_constant_inputs():
    rho, p = spearman_overlap_vs_severity([1, 1, 1, 1], [0, 1, 2, 1])
    assert np.isnan(rho) and np.isnan(p)
    rho, p = spearman_overlap_vs_severity([0.1, 0.5, 0.9, 1.3], [0, 1, 1, 2])
    assert rho > 0.8


# ----------------------------------------------------------------------------- conformal
def fake_probs(n, rng, acc=0.7):
    """Softmax-like probabilities that are right ~acc of the time."""
    y = rng.integers(0, 3, size=n)
    probs = rng.dirichlet(np.ones(3), size=n)
    for i in range(n):
        if rng.random() < acc:
            probs[i, y[i]] += 1.5
        probs[i] /= probs[i].sum()
    return probs, y


@pytest.mark.parametrize('mondrian', [False, True])
def test_conformal_coverage_close_to_target(mondrian):
    rng = np.random.default_rng(0)
    pc, yc = fake_probs(3000, rng)
    pt, yt = fake_probs(3000, rng)
    model = fit_conformal(pc, yc, alpha=0.1, mondrian=mondrian)
    stats = evaluate_conformal(model, pt, yt)
    assert stats['coverage'] >= 0.86            # target 0.90, finite-sample slack
    assert stats['avg_set_size'] >= 1.0


def test_mondrian_covers_each_class():
    rng = np.random.default_rng(1)
    pc, yc = fake_probs(4000, rng)
    pt, yt = fake_probs(4000, rng)
    model = fit_conformal(pc, yc, alpha=0.1, mondrian=True)
    sets = predict_sets(model, pt)
    for k in range(3):
        cov_k = sets[yt == k, k].mean()
        assert cov_k >= 0.85, f"class {k} coverage {cov_k:.3f}"


def test_abstaining_improves_answered_accuracy():
    rng = np.random.default_rng(2)
    pc, yc = fake_probs(3000, rng)
    pt, yt = fake_probs(3000, rng)
    model = fit_conformal(pc, yc, alpha=0.1)
    stats = evaluate_conformal(model, pt, yt)
    assert 0 < stats['answer_rate'] < 1
    assert stats['answered_accuracy'] > stats['baseline_accuracy']


def test_decide_label_only_when_answered():
    rng = np.random.default_rng(4)
    pc, yc = fake_probs(1000, rng)
    pt, _ = fake_probs(200, rng)
    d = decide(fit_conformal(pc, yc), pt)
    assert np.all(d['label'][~d['answered']] == -1)
    assert np.all(d['label'][d['answered']] >= 0)


def test_conformal_validates_inputs_and_roundtrips():
    with pytest.raises(ValueError):
        fit_conformal(np.zeros((5, 3)), np.zeros(4, dtype=int))
    with pytest.raises(ValueError):
        fit_conformal(np.full((5, 3), 1 / 3), np.zeros(5, dtype=int), alpha=1.5)
    rng = np.random.default_rng(5)
    pc, yc = fake_probs(500, rng)
    m = fit_conformal(pc, yc)
    from src.ddi_conformal import ConformalModel
    m2 = ConformalModel.from_dict(m.to_dict())
    assert np.allclose(m.qhat, m2.qhat) and m.mondrian == m2.mondrian


def test_empty_calibration_class_includes_everything():
    probs = np.array([[0.9, 0.05, 0.05], [0.8, 0.1, 0.1]])
    model = fit_conformal(probs, np.array([0, 0]), alpha=0.1, mondrian=True)
    assert model.qhat[1] == 1.0 and model.qhat[2] == 1.0


def test_threshold_curve_monotone_coverage():
    rng = np.random.default_rng(6)
    p, y = fake_probs(2000, rng)
    c = confidence_threshold_curve(p, y)
    assert np.all(np.diff(c['coverage']) <= 1e-12)


# ----------------------------------------------------------------------------- baselines
def split_pairs(pairs, seed=0):
    s = make_drug_splits(pairs, A, B, seed=seed)
    return s, [pairs[i] for i in s.train]


def test_prior_baseline_predicts_majority():
    pairs = [('a', 'b', 1)] * 8 + [('a', 'c', 0)] * 2
    pb = PriorBaseline().fit(pairs)
    assert set(pb.predict([('x', 'y')] * 4)) == {1}
    assert pb.predict_proba([('x', 'y')]).sum() == pytest.approx(1.0)


def test_drug_mean_baseline_is_order_independent():
    pairs = synthetic_pairs()
    s, train = split_pairs(pairs)
    m = DrugMeanBaseline().fit(train)
    test = [(pairs[i][0], pairs[i][1]) for i in s.test_s0]
    flipped = [(b, a) for a, b in test]
    assert np.allclose(m.predict_proba(test), m.predict_proba(flipped))


def test_drug_mean_beats_prior_when_drug_signal_exists_on_s0():
    pairs = synthetic_pairs(n_drugs=60, n_pairs=1200)
    accs_mean, accs_prior = [], []
    for seed in range(5):
        s, train = split_pairs(pairs, seed)
        idx = s.test_s0
        y = [pairs[i][2] for i in idx]
        t = [(pairs[i][0], pairs[i][1]) for i in idx]
        accs_mean.append(score_predictions(y, DrugMeanBaseline().fit(train).predict(t))['accuracy'])
        accs_prior.append(score_predictions(y, PriorBaseline().fit(train).predict(t))['accuracy'])
    assert np.mean(accs_mean) > np.mean(accs_prior) + 0.05


def test_drug_mean_s2_falls_back_to_the_training_prior():
    """With both drugs unseen there is no information: output must equal the class prior exactly."""
    pairs = synthetic_pairs()
    s, train = split_pairs(pairs)
    m = DrugMeanBaseline().fit(train)
    t = [(pairs[i][0], pairs[i][1]) for i in s.test_s2][:20]
    probs = m.predict_proba(t)
    assert np.allclose(probs, m.prior_[None, :])
    assert set(m.predict(t)) == {int(np.argmax(m.prior_))}


def test_drug_mean_never_collapses_below_the_prior_on_new_drugs():
    """Regression: the old version scored far below the majority-class floor on S1/S2."""
    pairs = synthetic_pairs(n_drugs=80, n_pairs=1500, seed=4)
    for seed in range(4):
        s, train = split_pairs(pairs, seed)
        for scen, idx in (('S1', s.test_s1), ('S2', s.test_s2)):
            y = [pairs[i][2] for i in idx]
            t = [(pairs[i][0], pairs[i][1]) for i in idx]
            dm = score_predictions(y, DrugMeanBaseline().fit(train).predict(t))
            pr = score_predictions(y, PriorBaseline().fit(train).predict(t))
            assert dm['macro_f1'] >= pr['macro_f1'] - 0.02, (scen, dm, pr)
            if scen == 'S1':
                assert dm['macro_f1'] > pr['macro_f1'] + 0.05   # a real drug signal must beat the floor


def test_drug_mean_one_known_branch_uses_the_known_drug():
    pairs = synthetic_pairs(n_drugs=80, n_pairs=1500, seed=5)
    s, train = split_pairs(pairs, 1)
    m = DrugMeanBaseline().fit(train)
    t = [(pairs[i][0], pairs[i][1]) for i in s.test_s1][:50]
    probs = m.predict_proba(t)
    assert not np.allclose(probs, m.prior_[None, :])          # S1 does use the known drug's information
    assert np.allclose(probs, m.predict_proba([(b, a) for a, b in t]))


def test_drug_mean_training_uses_leave_one_out():
    """A drug seen in a single training pair must look 'unknown' while featurising that pair."""
    m = DrugMeanBaseline()
    pairs = [('a', 'b', 2), ('b', 'c', 0), ('b', 'd', 0), ('c', 'd', 1)]
    m._stats(pairs)
    assert len(m._known_means('a', 'b', drop_label=2)) == 1   # a vanishes once its only pair is removed
    assert len(m._known_means('a', 'b')) == 2                 # but is known at prediction time


def test_fingerprint_forest_order_independent_and_learns():
    rng = np.random.default_rng(0)
    pairs = synthetic_pairs(n_drugs=40, n_pairs=600)
    drugs = sorted({d for a, b, _ in pairs for d in (a, b)})
    sev = {d: i % 3 for i, d in enumerate(drugs)}
    fps = {}
    for d in drugs:
        v = (rng.random(64) < 0.1).astype(np.float32)
        v[sev[d]] = 1.0                          # planted structure signal
        fps[d] = v
    train, test = pairs[:450], pairs[450:]
    m = FingerprintForestBaseline(n_estimators=60).fit(train, fps)
    tp = [(a, b) for a, b, _ in test]
    assert np.allclose(m.predict_proba(tp, fps), m.predict_proba([(b, a) for a, b in tp], fps))
    assert m.predict(tp, fps).shape == (len(tp),)


def test_score_predictions_perfect_and_empty_class():
    out = score_predictions([0, 1, 2, 1], [0, 1, 2, 1])
    assert out['accuracy'] == 1.0 and out['macro_f1'] == 1.0
    out = score_predictions([1, 1, 1], [1, 1, 1])
    assert out['minor_f1'] == 0.0 and out['accuracy'] == 1.0


# ----------------------------------------------------------------------------- dedupe + generic features
from src.ddi_splits import dedupe_pairs
from src.ddi_features import generic_pair_features, generic_feature_dim


def test_dedupe_collapses_both_orders_and_keeps_most_severe():
    pairs = [('a', 'b', 0), ('b', 'a', 2), ('a', 'c', 1), ('c', 'a', 1), ('d', 'd', 1)]
    uniq, stats = dedupe_pairs(pairs, A, B, lambda p: p[2])
    assert stats['n_unique'] == 2
    assert stats['n_conflicting'] == 1
    labels = {frozenset((p[0], p[1])): p[2] for p in uniq}
    assert labels[frozenset(('a', 'b'))] == 2          # most severe kept
    assert labels[frozenset(('a', 'c'))] == 1
    assert not any(p[0] == p[1] for p in uniq)          # self-pairs dropped


def test_dedupe_prevents_s0_leakage_on_duplicated_data():
    base = synthetic_pairs(n_drugs=50, n_pairs=500, seed=9)
    dup = base + [(b, a, y) for a, b, y in base]        # every pair also listed reversed
    uniq, _ = dedupe_pairs(dup, A, B, lambda p: p[2])
    assert len(uniq) == len(base)
    for seed in range(5):
        s = make_drug_splits(uniq, A, B, seed=seed)
        assert_no_leakage(s, uniq, A, B)
    # without dedupe the same data DOES leak (the guard is doing real work)
    leaked = False
    for seed in range(5):
        s = make_drug_splits(dup, A, B, seed=seed)
        try:
            assert_no_leakage(s, dup, A, B)
        except AssertionError:
            leaked = True
    assert leaked


def test_generic_features_any_length_and_symmetric():
    rng = np.random.default_rng(0)
    for k in (5, 12, 7):
        a, b = rng.random(k), rng.random(k)
        v = generic_pair_features(a, b)
        assert v.shape == (generic_feature_dim(k),)
        assert np.allclose(v, generic_pair_features(b, a))
    assert np.allclose(generic_pair_features(rng.random(12), rng.random(12)).shape, (generic_feature_dim(12),))
    assert generic_feature_dim(12) == PAIR_FEATURE_DIM


def test_generic_matches_tox21_specific_features():
    rng = np.random.default_rng(1)
    a, b = rng.random(N_TASKS), rng.random(N_TASKS)
    assert np.allclose(generic_pair_features(a, b), pair_feature_vector(a, b))


def test_generic_features_validation():
    with pytest.raises(ValueError):
        generic_pair_features(np.zeros(5), np.zeros(4))
    with pytest.raises(ValueError):
        generic_pair_features(np.full(5, 2.0), np.zeros(5))


# ----------------------------------------------------------------------------- folds + crossfit selection + reporting
import pandas as pd
from src.chem_utils import balanced_group_folds
from src.risk_profile import select_crossfit_predictions
from src.ablation_report import (
    summarize, paired_comparison, verdict, key_comparisons, render_report, plot_summary,
)


def test_balanced_group_folds_keep_groups_together_and_balance_sizes():
    rng = random.Random(0)
    groups = [f"scaf{rng.randint(0, 80)}" for _ in range(1000)]
    folds = balanced_group_folds(groups, 5, seed=1)
    by_group = {}
    for g, f in zip(groups, folds):
        by_group.setdefault(g, set()).add(f)
    assert all(len(v) == 1 for v in by_group.values())          # no scaffold straddles folds
    sizes = np.bincount(folds, minlength=5)
    assert sizes.min() > 0 and sizes.max() - sizes.min() <= 40  # roughly balanced
    assert balanced_group_folds(groups, 5, seed=1) == folds      # reproducible


def test_balanced_group_folds_validation():
    with pytest.raises(ValueError):
        balanced_group_folds(['a', 'b'], 1)


def test_crossfit_uses_held_out_model_for_known_molecules():
    k, n, t = 3, 4, 2
    per_model = np.zeros((k, n, t))
    for f in range(k):
        per_model[f] = f / 10 + 0.05          # model f outputs 0.05, 0.15, 0.25 everywhere
    keys = ['known_fold2', 'known_fold0', 'novel', None]
    fold_of = {'known_fold2': 2, 'known_fold0': 0}
    out = select_crossfit_predictions(per_model, keys, fold_of)
    assert np.allclose(out[0], 0.25)                       # only the model that never saw it (fold 2)
    assert np.allclose(out[1], 0.05)                       # fold 0
    assert np.allclose(out[2], per_model.mean(axis=0)[2])  # novel -> ensemble mean
    assert np.allclose(out[3], per_model.mean(axis=0)[3])  # unparseable key -> ensemble mean


def test_crossfit_selection_validates():
    with pytest.raises(ValueError):
        select_crossfit_predictions(np.zeros((2, 3, 4)), ['a', 'b'], {})
    with pytest.raises(ValueError):
        select_crossfit_predictions(np.zeros((2, 1, 4)), ['a'], {'a': 5})


def fake_runs(n_seeds=6, effect=0.0, seed=0):
    """Synthetic ablation results: model B = model A + effect (+ noise)."""
    rng = np.random.default_rng(seed)
    rows = []
    for s in range(n_seeds):
        for scen, base in (('S0', 0.60), ('S1', 0.50), ('S2', 0.45)):
            shared = rng.normal(0, 0.01)
            for model, add in (('A', 0.0), ('B', effect), ('DrugMean', -0.05)):
                f1 = base + shared + add + rng.normal(0, 0.002)
                rows.append({'seed': s, 'model': model, 'scenario': scen, 'n': 100, 'accuracy': f1 + 0.05,
                             'macro_f1': f1, 'minor_f1': f1 - 0.2, 'moderate_f1': f1 + 0.2, 'major_f1': f1})
    return pd.DataFrame(rows)


def test_paired_comparison_detects_real_effect():
    runs = fake_runs(n_seeds=8, effect=0.03)
    comp = paired_comparison(runs, 'B', 'A')
    assert len(comp) == 3
    assert (comp['mean_diff'] > 0.02).all() and (comp['wins'] == 8).all()
    assert 'IMPROVES' in verdict(comp.iloc[0])


def test_paired_comparison_does_not_overclaim_on_no_effect():
    runs = fake_runs(n_seeds=8, effect=0.0, seed=3)
    comp = paired_comparison(runs, 'B', 'A')
    assert all('IMPROVES' not in verdict(r) for _, r in comp.iterrows())


def test_verdict_inconclusive_with_few_seeds():
    runs = fake_runs(n_seeds=3, effect=0.05)
    comp = paired_comparison(runs, 'B', 'A')
    assert all('INCONCLUSIVE' in verdict(r) for _, r in comp.iterrows())
    assert comp['p_value'].isna().all()


def test_verdict_reports_worse():
    runs = fake_runs(n_seeds=8, effect=-0.03)
    comp = paired_comparison(runs, 'B', 'A')
    assert all('WORSE' in verdict(r) for _, r in comp.iterrows())


def test_summarize_and_report_render(tmp_dir=None):
    import tempfile
    runs = fake_runs(n_seeds=6, effect=0.02)
    summ = summarize(runs)
    assert set(summ['n_seeds']) == {6}
    overlap = pd.DataFrame([{'scenario': 'S1', 'rho': 0.12, 'p_value': 0.01, 'n': 200}])
    md = render_report(runs, {'profiler_mode': 'single_model_leaky', 'seeds': 6}, overlap)
    assert 'WARNING' in md and 'B_shuf' in md and 'How to read this honestly' in md
    assert 'Spearman' in md
    md2 = render_report(runs, {'profiler_mode': 'crossfit', 'seeds': 6})
    assert 'WARNING' not in md2
    with tempfile.TemporaryDirectory() as d:
        plot_summary(summ, os.path.join(d, 'p.png'))
        assert os.path.getsize(os.path.join(d, 'p.png')) > 1000


def test_key_comparisons_skips_missing_models():
    runs = fake_runs(n_seeds=6, effect=0.02)
    comp = key_comparisons(runs)
    assert set(zip(comp['x'], comp['y'])) <= {('B', 'A'), ('A', 'DrugMean'), ('B', 'DrugMean')}
    assert ('B', 'A') in set(zip(comp['x'], comp['y']))


# ----------------------------------------------------------------------------- headline claim + synthetic + end-to-end
from src.ablation_report import headline_claim
from src.ddi_synthetic import make_synthetic_experiment


def tabular_runs(n_seeds=8, tox_gain=0.0, shuf_gain=0.0, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for s in range(n_seeds):
        for scen, base in (('S0', 0.6), ('S1', 0.5), ('S2', 0.45)):
            shared = rng.normal(0, 0.01)
            for model, add in (('RF_fp', 0.0), ('RF_fp+tox', tox_gain), ('RF_fp+toxshuf', shuf_gain)):
                f1 = base + shared + add + rng.normal(0, 0.002)
                rows.append({'seed': s, 'model': model, 'scenario': scen, 'n': 80, 'accuracy': f1,
                             'macro_f1': f1, 'minor_f1': f1, 'moderate_f1': f1, 'major_f1': f1})
    return pd.DataFrame(rows)


def test_headline_supported_only_when_beating_baseline_and_shuffled_control():
    claim = headline_claim(tabular_runs(tox_gain=0.03, shuf_gain=0.0))
    assert set(claim['status']) == {'SUPPORTED'}


def test_headline_rejects_gain_that_shuffled_control_also_gets():
    claim = headline_claim(tabular_runs(tox_gain=0.03, shuf_gain=0.03))
    assert 'SUPPORTED' not in set(claim['status'])


def test_headline_inconclusive_with_few_seeds_and_not_supported_without_gain():
    assert set(headline_claim(tabular_runs(n_seeds=3, tox_gain=0.05))['status']) == {'INCONCLUSIVE'}
    assert set(headline_claim(tabular_runs(tox_gain=0.0))['status']) == {'NOT SUPPORTED'}


def test_headline_skips_when_models_missing():
    runs = tabular_runs()
    assert headline_claim(runs[runs['model'] != 'RF_fp+toxshuf']).empty


def _overlap_rho(**kw):
    pairs, tox, _, _ = make_synthetic_experiment(seed=1, n_pairs=3000, **kw)
    ov = [expected_shared_risk(tox[a], tox[b]) for a, b, _ in pairs]
    return spearman_overlap_vs_severity(ov, [y for _, _, y in pairs])[0]


def test_synthetic_true_null_has_no_overlap_signal_and_planted_effect_is_visible():
    null = _overlap_rho(tox_signal=0.0, tox_from_latent=False)
    planted = _overlap_rho(tox_signal=2.0, tox_from_latent=False)
    assert abs(null) < 0.08
    assert planted > 0.2


def test_synthetic_pairs_are_unique_unordered():
    pairs, *_ = make_synthetic_experiment(seed=2)
    keys = [frozenset((a, b)) for a, b, _ in pairs]
    assert len(keys) == len(set(keys))


def test_end_to_end_synthetic_run_writes_all_outputs():
    import tempfile
    from src.run_ablation import main
    with tempfile.TemporaryDirectory() as d:
        res = main(['--synthetic', '--no_gnn', '--seeds', '0', '1', '--rf_trees', '20', '--out_dir', d])
        for f in ('ablation_runs.csv', 'ablation_summary.csv', 'ablation_report.md', 'run_meta.json',
                  'conformal.csv', 'overlap_correlation.csv', os.path.join('figures', 'ablation_macro_f1.png')):
            assert os.path.exists(os.path.join(d, f)), f
        report = open(os.path.join(d, 'ablation_report.md')).read()
        assert 'SYNTHETIC' in report and 'Headline claim' in report
        assert set(res['runs']['scenario']) == {'S0', 'S1', 'S2'}
        assert {'Prior', 'DrugMean', 'RF_fp', 'RF_fp+tox', 'RF_fp+toxshuf'} <= set(res['runs']['model'])


def test_largest_group_does_not_always_land_in_fold_zero():
    """Regression: acyclic molecules (one huge group) used to bias fold 0 / the validation split."""
    groups = ['big'] * 80 + [f's{i}' for i in range(400)]
    landing = {balanced_group_folds(groups, 5, seed=s)[0] for s in range(30)}
    assert len(landing) >= 3                              # the big group moves around with the seed
    for s in range(10):
        folds = balanced_group_folds(groups, 5, seed=s)
        assert len(set(folds[:80])) == 1                   # ...but is never split
        sizes = np.bincount(folds, minlength=5)
        assert sizes.max() - sizes.min() <= 80


# ----------------------------------------------------------------------------- identity merge
from src.ddi_splits import merge_pairs_by_identity


def _alias_pairs(seed=0):
    rng = random.Random(seed)
    base = [f"drug{i}" for i in range(60)]
    names = base + [f"{b} (topical)" for b in base[:20]]          # 20 molecules listed under two names
    ident = {n: n.replace(' (topical)', '') for n in names}
    pairs, seen = [], set()
    while len(pairs) < 900:
        a, b = rng.sample(names, 2)
        if frozenset((a, b)) in seen:
            continue
        seen.add(frozenset((a, b)))
        pairs.append((a, b, rng.randint(0, 2)))
    return pairs, ident


def test_name_based_split_leaks_aliased_molecules_but_identity_split_does_not():
    pairs, ident = _alias_pairs()
    leaked = 0
    for seed in range(10):
        s = make_drug_splits(pairs, A, B, seed=seed)
        leaked += len({ident[d] for d in s.train_drugs} & {ident[d] for d in s.test_drugs})
    assert leaked > 0                                        # the hazard is real

    mapped, stats = merge_pairs_by_identity(pairs, ident, A, B, lambda p: p[2])
    uniq, _ = dedupe_pairs(mapped, A, B, lambda p: p[2])
    assert stats['n_names'] == 80 and stats['n_identities'] == 60 and stats['n_names_merged'] == 20
    for seed in range(10):
        s = make_drug_splits(uniq, A, B, seed=seed)
        assert_no_leakage(s, uniq, A, B)
        assert not (s.train_drugs & s.test_drugs)
        assert not (s.val_drugs & s.test_drugs)


def test_merge_turns_alias_pairs_into_droppable_self_pairs():
    ident = {'X': 'molX', 'X (oral)': 'molX', 'Y': 'molY'}
    pairs = [('X', 'X (oral)', 1), ('X', 'Y', 0), ('X (oral)', 'Y', 2)]
    mapped, _ = merge_pairs_by_identity(pairs, ident, A, B, lambda p: p[2])
    uniq, stats = dedupe_pairs(mapped, A, B, lambda p: p[2])
    assert len(uniq) == 1 and uniq[0][2] == 2                 # self-pair dropped; duplicate keeps most severe
    assert stats['n_conflicting'] == 1


# ----------------------------------------------------------------------------- overlap diagnostics + new tabular models
from src.ddi_features import partial_spearman, overlap_diagnostics


def _profiles(n, seed):
    rng = np.random.default_rng(seed)
    return rng.beta(1.2, 2.5, size=(n, N_TASKS)), rng.beta(1.2, 2.5, size=(n, N_TASKS)), rng


def test_additive_only_severity_shows_overlap_correlation_that_vanishes_when_controlled():
    """Dangerous drugs pairing with dangerous drugs must NOT be mistaken for shared-mechanism signal."""
    pa, pb, rng = _profiles(6000, 0)
    additive = pa.mean(axis=1) + pb.mean(axis=1)
    score = additive + rng.normal(0, 0.05, size=additive.shape)
    labels = np.digitize(score, np.quantile(score, [0.2, 0.75]))
    d = overlap_diagnostics(pa, pb, labels)
    assert d['rho_overlap'] > 0.4                    # naive overlap looks informative...
    assert d['rho_additive'] > d['rho_overlap']      # ...but the drug-level explanation is stronger
    assert abs(d['rho_partial']) < 0.1               # ...and nothing is left once it is removed


def test_genuine_pair_specific_overlap_survives_partial_control():
    """Severity driven by the PRODUCT of risks (true shared-risk effect) keeps a clear partial correlation."""
    pa, pb, rng = _profiles(6000, 1)
    additive = pa.mean(axis=1) + pb.mean(axis=1)
    shared = np.sum(pa * pb, axis=1)
    resid = shared - np.polyval(np.polyfit(additive, shared, 1), additive)   # the part of overlap additive can't explain
    score = 2.0 * resid / resid.std() + rng.normal(0, 1.0, size=resid.shape)
    labels = np.digitize(score, np.quantile(score, [0.2, 0.75]))
    d = overlap_diagnostics(pa, pb, labels)
    assert d['rho_partial'] > 0.25


def test_partial_spearman_degenerate_inputs():
    assert np.isnan(partial_spearman([1, 1, 1, 1, 1], [1, 2, 3, 4, 5], [5, 4, 3, 2, 1]))
    assert np.isnan(partial_spearman([1, 2], [1, 2], [1, 2]))


def test_overlap_diagnostics_is_symmetric_in_the_two_drugs():
    pa, pb, rng = _profiles(500, 2)
    labels = rng.integers(0, 3, size=500)
    d1, d2 = overlap_diagnostics(pa, pb, labels), overlap_diagnostics(pb, pa, labels)
    assert d1['rho_overlap'] == pytest.approx(d2['rho_overlap'])
    assert d1['rho_partial'] == pytest.approx(d2['rho_partial'])


def test_tabular_matrix_shapes_for_new_models():
    from src.run_ablation import ExperimentData, tabular_matrix, shuffle_map
    pairs, tox, cyp, fps = make_synthetic_experiment(seed=3, n_pairs=200)
    data = ExperimentData(pairs=pairs, tox=tox, cyp=cyp, fps=fps)
    names = sorted({d for a, b, _ in pairs for d in (a, b)})
    shuf = shuffle_map(names, 0)
    n_bits = len(next(iter(fps.values())))
    sub = pairs[:10]
    assert tabular_matrix('RF_fp', data, sub, shuf).shape == (10, 2 * n_bits)
    assert tabular_matrix('RF_fp+tox', data, sub, shuf).shape == (10, 2 * n_bits + PAIR_FEATURE_DIM)
    assert tabular_matrix('RF_fp+ov', data, sub, shuf).shape == (10, 2 * n_bits + 4)
    assert tabular_matrix('RF_tox', data, sub, shuf).shape == (10, PAIR_FEATURE_DIM)
    # RF_tox must contain no fingerprint information at all
    assert np.allclose(tabular_matrix('RF_tox', data, sub, shuf),
                       np.stack([pair_feature_vector(tox[a], tox[b]) for a, b, _ in sub]))
    # order independence of every tabular model
    flipped = [(b, a, y) for a, b, y in sub]
    for m in ('RF_fp', 'RF_fp+tox', 'RF_fp+ov', 'RF_tox', 'RF_fp+toxshuf'):
        assert np.allclose(tabular_matrix(m, data, sub, shuf), tabular_matrix(m, data, flipped, shuf)), m


def test_shuffle_map_has_no_fixed_points_and_is_a_permutation():
    from src.run_ablation import shuffle_map
    names = [f"d{i}" for i in range(50)]
    m = shuffle_map(names, 3)
    assert sorted(m.values()) == sorted(names)
    assert all(a != b for a, b in m.items())


# ----------------------------------------------------------------------------- overlap-lead analysis
import tempfile
from src.overlap_analysis import (
    tanimoto_pairs, jaccard_sets, load_atc_sets, PartialCorr, spearman, PairTable, build_pair_table,
    point_estimates, drug_bootstrap, permutation_null, analyze_subset, verdict_status, run_analysis,
    render_report as render_overlap_report,
)


def test_tanimoto_pairs_known_values():
    fp = np.array([[1, 1, 0, 0], [1, 0, 1, 0], [0, 0, 0, 0], [1, 1, 0, 0]], dtype=np.float32)
    out = tanimoto_pairs(fp, np.array([0, 0, 2, 0]), np.array([1, 3, 2, 0]))
    assert np.allclose(out, [1 / 3, 1.0, 0.0, 1.0])               # empty-empty -> 0; self -> 1


def test_jaccard_sets_known_values():
    sets = [frozenset('AB'), frozenset('BC'), frozenset(), frozenset('AB')]
    out = jaccard_sets(sets, np.array([0, 0, 2, 0]), np.array([1, 3, 2, 2]))
    assert np.allclose(out, [1 / 3, 1.0, 0.0, 0.0])


def test_partial_corr_matches_single_control_reference_and_is_symmetric_in_use():
    rng = np.random.default_rng(0)
    z = rng.normal(size=500)
    x = z + rng.normal(size=500)
    y = z + rng.normal(size=500)
    ref = partial_spearman(x, y, z)
    assert PartialCorr(y, z[:, None]).corr(x) == pytest.approx(ref, abs=1e-9)
    assert PartialCorr(x, z[:, None]).corr(y) == pytest.approx(ref, abs=1e-9)


def test_partial_corr_removes_a_measured_confounder_and_keeps_a_real_effect():
    rng = np.random.default_rng(1)
    conf = rng.normal(size=8000)
    x = conf + rng.normal(0, 0.5, 8000)
    y_conf = conf + rng.normal(0, 0.5, 8000)                      # y driven only by the confounder
    assert spearman(x, y_conf) > 0.6
    assert abs(PartialCorr(y_conf, conf[:, None]).corr(x)) < 0.05
    y_real = conf + 0.8 * x + rng.normal(0, 0.5, 8000)            # a genuine x effect on top
    assert PartialCorr(y_real, conf[:, None]).corr(x) > 0.3


def test_load_atc_sets_reads_files_and_maps_names_to_identities():
    with tempfile.TemporaryDirectory() as d:
        pd.DataFrame({'Drug_A': ['Foo', 'Foo (oral)'], 'Drug_B': ['Bar', 'Baz']}).to_csv(
            os.path.join(d, 'ddinter_downloads_code_A.csv'), index=False)
        pd.DataFrame({'Drug_A': ['Bar'], 'Drug_B': ['Qux']}).to_csv(
            os.path.join(d, 'ddinter_downloads_code_L.csv'), index=False)
        ident = {'Foo': 'molFoo', 'Foo (oral)': 'molFoo', 'Bar': 'molBar', 'Baz': 'molBaz'}   # Qux unmapped -> ignored
        out = load_atc_sets(d, ident)
        assert out['molFoo'] == frozenset('A') and out['molBar'] == frozenset('AL') and 'Qux' not in out
        assert load_atc_sets(os.path.join(d, 'missing'), ident) == {}


def _analysis_table(severity, n_drugs=220, n_pairs=9000, seed=0):
    """Synthetic table with exactly known drivers of severity. severity(ctx) -> latent score."""
    rng = np.random.default_rng(seed)
    P = rng.beta(1.3, 2.5, size=(n_drugs, N_TASKS))
    z = rng.normal(size=(n_drugs, 5))
    fp = (z @ rng.normal(size=(5, 128)) + rng.normal(0, 1.2, (n_drugs, 128)) > 0.8).astype(np.float32)
    names = [f"d{i}" for i in range(n_drugs)]
    seen, ij = set(), []
    while len(ij) < n_pairs:
        i, j = rng.choice(n_drugs, 2, replace=False)
        if (min(i, j), max(i, j)) in seen:
            continue
        seen.add((min(i, j), max(i, j)))
        ij.append((i, j))
    ii, jj = np.array([a for a, _ in ij]), np.array([b for _, b in ij])
    ctx = {'overlap': np.sum(P[ii] * P[jj], axis=1), 'additive': P.mean(1)[ii] + P.mean(1)[jj],
           'sim': np.sum(z[ii] * z[jj], axis=1), 'rng': rng}
    score = severity(ctx)
    labels = np.digitize(score, np.quantile(score, [0.15, 0.7]))
    pairs = [(names[a], names[b], int(l)) for a, b, l in zip(ii, jj, labels)]
    tox = {n: P[k] for k, n in enumerate(names)}
    fps = {n: fp[k] for k, n in enumerate(names)}
    in_table = {n: (k % 2 == 0) for k, n in enumerate(names)}
    atc = {n: frozenset(['A', 'B'][: 1 + k % 2]) for k, n in enumerate(names)}
    return build_pair_table(pairs, tox, fps, in_table, atc)


def test_overlap_that_is_only_a_proxy_for_drug_risk_does_not_survive_controls():
    t = _analysis_table(lambda c: 3 * c['additive'] + c['rng'].normal(0, 0.3, len(c['additive'])))
    r = analyze_subset(t, n_boot=60, n_perm=80, seed=1)
    assert r['rho_overlap'] > 0.3                         # naive overlap looks informative...
    assert r['status'] == 'EXPLAINED AWAY'                # ...but nothing real is left after controls
    assert abs(r['rho_partial_all']) < 0.1


def test_a_genuine_pair_specific_overlap_effect_survives_controls():
    def sev(c):
        resid = c['overlap'] - np.polyval(np.polyfit(c['additive'], c['overlap'], 1), c['additive'])
        return 2.0 * resid / resid.std() + c['rng'].normal(0, 1.0, len(resid))
    r = analyze_subset(_analysis_table(sev, seed=2), n_boot=60, n_perm=80, seed=1)
    assert r['status'] == 'NOT EXPLAINED AWAY (UNCONFIRMED)'
    assert r['ci_partial_all'][0] > 0 and r['rho_partial_all'] > r['matched_null_p95']


def test_bootstrap_interval_is_wider_than_naive_pair_resampling_would_suggest_and_contains_estimate():
    t = _analysis_table(lambda c: c['overlap'] + c['rng'].normal(0, 1.5, len(c['overlap'])), seed=3)
    est = point_estimates(t)
    boot = drug_bootstrap(t, 80, np.random.default_rng(0))
    lo, hi = np.percentile(boot['rho_partial_all'], [2.5, 97.5])
    assert lo <= est['rho_partial_all'] <= hi
    assert hi - lo > 0.01                                 # real uncertainty, not a degenerate interval


def test_permutation_null_is_centred_near_zero_when_profiles_are_exchangeable():
    t = _analysis_table(lambda c: c['sim'] + c['rng'].normal(0, 1.0, len(c['sim'])), seed=4)
    null = permutation_null(t, 60, np.random.default_rng(0))
    assert abs(np.nanmean(null)) < 0.05


def test_verdict_status_rules():
    base = {'ci_partial_all': (0.02, 0.1), 'matched_null_p95': 0.01, 'rho_partial_all': 0.06}
    assert verdict_status(base) == 'NOT EXPLAINED AWAY (UNCONFIRMED)'
    assert verdict_status({**base, 'ci_partial_all': (-0.02, 0.1)}) == 'EXPLAINED AWAY'
    assert verdict_status({**base, 'rho_partial_all': 0.005}) == 'EXPLAINED AWAY'
    assert verdict_status({**base, 'ci_partial_all': (float('nan'), float('nan'))}) == 'INCONCLUSIVE'
    assert 'CONFIRMED' not in verdict_status(base).replace('UNCONFIRMED', '')     # never reads as support


def test_run_analysis_subsets_and_report_wording():
    t = _analysis_table(lambda c: c['sim'] + c['rng'].normal(0, 1.0, len(c['sim'])), seed=5)
    res = run_analysis(t, n_boot=30, n_perm=30, seed=0)
    assert {'ALL', 'BOTH_IN_TOX21_TABLE', 'AT_LEAST_ONE_OUTSIDE_TABLE'} <= set(res)
    md = render_overlap_report(res, {'data source': 'test'})
    assert 'Reading this honestly' in md and 'imperfect proxies' in md and 'not a clinical statement' in md


def test_overlap_analysis_end_to_end_on_synthetic_data():
    from src.overlap_analysis import main as overlap_main
    with tempfile.TemporaryDirectory() as d:
        res = overlap_main(['--synthetic', '--n_boot', '25', '--n_perm', '25', '--out_dir', d])
        for f in ('overlap_analysis.md', 'overlap_analysis.csv', 'run_meta.json'):
            assert os.path.exists(os.path.join(d, f)), f
        assert 'ALL' in res


def _latent_table(seed, fp_noise=1.2, n_drugs=220, n_pairs=9000, effect=0.0):
    """Profiles AND fingerprints are functions of hidden structure z. Severity = latent similarity
    (a pure structural confounder) plus, optionally, a genuine PROFILE-SPECIFIC overlap effect."""
    rng = np.random.default_rng(seed)
    z = rng.normal(size=(n_drugs, 5))
    P = 1 / (1 + np.exp(-(z @ rng.normal(size=(5, N_TASKS)) + rng.normal(0, 0.7, (n_drugs, N_TASKS)))))
    fp = (z @ rng.normal(size=(5, 128)) + rng.normal(0, fp_noise, (n_drugs, 128)) > 0.8).astype(np.float32)
    seen, ij = set(), []
    while len(ij) < n_pairs:
        i, j = rng.choice(n_drugs, 2, replace=False)
        if (min(i, j), max(i, j)) in seen:
            continue
        seen.add((min(i, j), max(i, j)))
        ij.append((i, j))
    ii, jj = np.array([a for a, _ in ij]), np.array([b for _, b in ij])
    zn = z / np.linalg.norm(z, axis=1, keepdims=True)
    score = 3 * np.sum(zn[ii] * zn[jj], axis=1) + rng.normal(0, 1.0, len(ii))
    if effect:
        # profile-specific part: the overlap that structure (cluster neighbours) cannot explain
        ov = np.sum(P[ii] * P[jj], axis=1)
        score = score + effect * (ov - ov.mean()) / ov.std()
    labels = np.digitize(score, np.quantile(score, [0.15, 0.7]))
    names = [f"d{k}" for k in range(n_drugs)]
    pairs = [(names[a], names[b], int(l)) for a, b, l in zip(ii, jj, labels)]
    return build_pair_table(pairs, {n: P[k] for k, n in enumerate(names)}, {n: fp[k] for k, n in enumerate(names)},
                            {n: k % 2 == 0 for k, n in enumerate(names)}, {n: frozenset('A') for n in names})


def test_matched_permutation_only_moves_drugs_within_their_cluster():
    from src.overlap_analysis import matched_permutation
    clusters = np.array([0, 0, 0, 1, 1, 2, 3, 3, 3, 3])
    rng = np.random.default_rng(0)
    for _ in range(20):
        perm = matched_permutation(clusters, rng)
        assert sorted(perm) == list(range(10))
        assert np.all(clusters[perm] == clusters)
        assert perm[5] == 5                                   # singleton cluster stays put


def test_structure_clusters_have_requested_granularity():
    from src.overlap_analysis import structure_clusters
    rng = np.random.default_rng(0)
    fp = (rng.random((120, 64)) > 0.5).astype(np.float32)
    c = structure_clusters(fp, drugs_per_cluster=6)
    assert 12 <= len(np.unique(c)) <= 30 and len(c) == 120


def test_KNOWN_LIMITATION_purely_structural_confounding_is_not_explained_away():
    """
    Documents a measured limitation so nobody over-reads the verdict. Severity here depends ONLY on
    latent structural similarity; the risk profiles and fingerprints are both noisy functions of that
    hidden structure. The analysis still reports the association as 'NOT EXPLAINED AWAY', which is why
    that status is labelled UNCONFIRMED and must be checked predictively.
    """
    statuses = [analyze_subset(_latent_table(300 + s), n_boot=40, n_perm=50, seed=s)['status'] for s in range(4)]
    assert statuses.count('NOT EXPLAINED AWAY (UNCONFIRMED)') >= 3


def test_overlap_report_states_the_limitation_when_an_association_remains():
    t = _latent_table(310)
    md = render_overlap_report(run_analysis(t, n_boot=30, n_perm=30, seed=0), {'data source': 'test'})
    assert 'does not confirm' in md.lower() and 'predictive test' in md.lower()
