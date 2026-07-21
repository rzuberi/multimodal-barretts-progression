#!/usr/bin/env python
"""Frozen-expert Mixture-of-Experts: a cheap router over already-trained OOF.

The end-to-end MoE (``src/moe.py``) trains gate + experts jointly and lands
mid-pack at n~150 (over-parameterised — see SUMMARY finding #3). This is the
sanity-comparison the handoff (§11.3) asks for: instead of learning experts, it
takes the FROZEN per-fold OOF predictions of the already-trained image_only,
cnv_only and multimodal experts and learns only a small gate to weight them.

Leakage safety (the whole point):
  * Experts are the frozen OOF predictions — each row's expert score was already
    produced by a model that never saw that row (nested-CV OOF).
  * The gate is fit PER OUTER FOLD on the OTHER folds' OOF rows only, then applied
    to the held-out fold. The gate never sees the fold it scores. Result: the
    combined prediction for every row is still fully out-of-sample, so it is
    directly comparable to the frozen baselines on the identical rows/folds.

Two gate variants (both tiny, both honest):
  * ``logistic`` — multinomial-ish soft gate: a logistic regression on the expert
    logits predicts y, and its per-expert responsibilities (softmax of the
    contribution) weight the expert probabilities. Falls back gracefully.
  * ``static`` — no per-sample gate; the single best convex blend of experts is
    chosen on the training folds (grid over simplex) and applied to the test fold.
    A genuinely frozen, non-adaptive baseline.

Expert set defaults to (image_only, cnv_only, multimodal=late_mean's inputs are
image+cnv; we use intermediate_fusion as the multimodal expert so all three are
distinct trained models). Output mirrors the other families' OOF schema so
make_results.py / paired_comparison pick it up unchanged.

Usage:
    python multitask_moe/scripts/frozen_expert_moe.py --task ever_progress \
        --backbone uni2 --gate logistic
Writes <BASE>/<task>/train/<backbone>/oof/frozen_moe_oof_predictions.csv (+ a
routing report) and prints a patient-level metric line.
"""
from __future__ import annotations

import argparse
import json
import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score

BASE = Path("/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/"
            "analysis/multitask_moe_20260721")
EXPERTS = ("image_only", "cnv_only", "intermediate_fusion")
KEY = "row_key"
EPS = 1e-6


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, EPS, 1 - EPS)
    return np.log(p / (1 - p))


def _load_experts(oof_dir: Path, experts) -> pd.DataFrame:
    """Wide frame: one row per biopsy, expert prob columns + y_true + outer_fold."""
    base = None
    for fam in experts:
        path = oof_dir / f"{fam}_oof_predictions.csv"
        if not path.exists():
            raise SystemExit(f"missing expert OOF: {path}")
        df = pd.read_csv(path, dtype={KEY: str})[[KEY, "patient_id", "outer_fold", "y_true", "y_prob"]]
        df = df.rename(columns={"y_prob": f"p_{fam}"})
        if base is None:
            base = df
        else:
            base = base.merge(df[[KEY, f"p_{fam}"]], on=KEY, how="inner", validate="one_to_one")
    return base


def _patient_max(df: pd.DataFrame, prob="y_prob") -> pd.DataFrame:
    return df.groupby(["patient_id", "outer_fold"], as_index=False).agg(
        y_true=("y_true", "max"), y_prob=(prob, "max"))


def _metrics(df: pd.DataFrame) -> dict:
    pat = _patient_max(df)
    return {"auprc": float(average_precision_score(pat.y_true, pat.y_prob)),
            "roc_auc": float(roc_auc_score(pat.y_true, pat.y_prob)),
            "n_patients": int(pat.patient_id.nunique() if "patient_id" in pat else len(pat))}


def _fit_logistic_gate(train: pd.DataFrame, test: pd.DataFrame, experts):
    """Per-sample soft gate. Returns (test_prob, gate_weights[test, n_experts])."""
    Xtr = np.column_stack([_logit(train[f"p_{e}"].to_numpy()) for e in experts])
    Xte = np.column_stack([_logit(test[f"p_{e}"].to_numpy()) for e in experts])
    ytr = train["y_true"].to_numpy().astype(int)
    if len(np.unique(ytr)) < 2:
        # degenerate training fold -> fall back to uniform blend
        w = np.full((len(test), len(experts)), 1.0 / len(experts))
        prob = np.column_stack([test[f"p_{e}"].to_numpy() for e in experts]).mean(1)
        return prob, w
    lr = LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced")
    lr.fit(Xtr, ytr)
    coef = lr.coef_.ravel()  # per-expert weight on its logit
    # Gate responsibility = softmax of |coef|*|expert-logit contribution|, per sample.
    contrib = np.abs(Xte * coef)  # [n_test, n_experts]
    w = contrib / np.clip(contrib.sum(1, keepdims=True), EPS, None)
    probs = np.column_stack([test[f"p_{e}"].to_numpy() for e in experts])
    blended = (w * probs).sum(1)
    return blended, w


def _fit_static_gate(train: pd.DataFrame, test: pd.DataFrame, experts, grid=11):
    """Single convex blend chosen on train folds by patient-level AUPRC."""
    simplex = [w for w in product(np.linspace(0, 1, grid), repeat=len(experts))
               if abs(sum(w) - 1.0) < 1e-9]
    ptr = {e: train[f"p_{e}"].to_numpy() for e in experts}
    best_w, best_ap = None, -np.inf
    tr = train.copy()
    for w in simplex:
        tr["y_prob"] = sum(wi * ptr[e] for wi, e in zip(w, experts))
        ap = average_precision_score(*(_patient_max(tr)[["y_true", "y_prob"]].to_numpy().T))
        if ap > best_ap:
            best_ap, best_w = ap, w
    pte = {e: test[f"p_{e}"].to_numpy() for e in experts}
    blended = sum(wi * pte[e] for wi, e in zip(best_w, experts))
    w_mat = np.tile(best_w, (len(test), 1))
    return blended, w_mat, best_w


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--task", required=True)
    ap.add_argument("--backbone", required=True)
    ap.add_argument("--gate", choices=["logistic", "static"], default="logistic")
    ap.add_argument("--experts", default=",".join(EXPERTS))
    args = ap.parse_args()

    experts = tuple(args.experts.split(","))
    oof_dir = BASE / args.task / "train" / args.backbone / "oof"
    wide = _load_experts(oof_dir, experts)
    folds = sorted(wide["outer_fold"].unique())

    out_rows, routing_rows, static_weights = [], [], {}
    for fold in folds:
        test = wide[wide["outer_fold"] == fold].copy()
        train = wide[wide["outer_fold"] != fold].copy()
        if args.gate == "logistic":
            prob, w = _fit_logistic_gate(train, test, experts)
        else:
            prob, w, best_w = _fit_static_gate(train, test, experts)
            static_weights[int(fold)] = {e: round(float(x), 3) for e, x in zip(experts, best_w)}
        test["y_prob"] = prob
        for i, e in enumerate(experts):
            test[f"w_{e}"] = w[:, i]
        test["routed_expert"] = np.array(experts)[w.argmax(1)]
        out_rows.append(test)
        for e in experts:
            routing_rows.append({"outer_fold": int(fold), "expert": e,
                                 "mean_gate_weight": round(float(test[f"w_{e}"].mean()), 3),
                                 "pct_argmax": round(100.0 * float((test["routed_expert"] == e).mean()), 1)})

    combined = pd.concat(out_rows, ignore_index=True)
    combined["model_family"] = f"frozen_moe_{args.gate}"
    keep = [KEY, "patient_id", "outer_fold", "y_true", "y_prob", "model_family",
            *[f"w_{e}" for e in experts], "routed_expert"]
    out_path = oof_dir / f"frozen_moe_{args.gate}_oof_predictions.csv"
    combined[keep].sort_values(["outer_fold", KEY]).to_csv(out_path, index=False)

    metrics = _metrics(combined)
    report = {"task": args.task, "backbone": args.backbone, "gate": args.gate,
              "experts": list(experts), **metrics,
              "routing": routing_rows}
    if static_weights:
        report["static_weights_per_fold"] = static_weights
    (oof_dir / f"frozen_moe_{args.gate}_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("task", "backbone", "gate", "auprc", "roc_auc", "n_patients")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
