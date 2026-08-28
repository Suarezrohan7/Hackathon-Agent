"""Scoring for the Strategy Validation Agent.

Primary metric: verdict accuracy (predicted vs known label).
Secondary:      findings precision / recall / F1 over the allowed finding ids.
"""

from __future__ import annotations

from typing import Any

PRIMARY_METRIC = "verdict_correct"

_VERDICT_SYNONYMS = {
    "edge": "edge", "real": "edge", "genuine": "edge", "has edge": "edge", "real edge": "edge",
    "valid": "edge", "robust": "edge",
    "overfit": "overfit", "overfitting": "overfit", "over-fit": "overfit", "curve-fit": "overfit",
    "curvefit": "overfit", "curve fit": "overfit", "data-mined": "overfit", "data mined": "overfit",
    "lookahead": "overfit", "look-ahead": "overfit",
    "no_edge": "no_edge", "no edge": "no_edge", "none": "no_edge", "no-edge": "no_edge",
    "random": "no_edge", "luck": "no_edge", "lucky": "no_edge", "spurious": "no_edge",
    "not tradable": "no_edge", "no real edge": "no_edge",
}

_ALLOWED_FINDINGS = {
    "oos_collapse", "param_fragility", "lookahead_bias", "regime_dependence",
    "transaction_cost_sensitivity", "insufficient_trades", "robust_oos",
}


def _norm_verdict(v: Any) -> str:
    s = str(v or "").strip().lower()
    if s in _VERDICT_SYNONYMS:
        return _VERDICT_SYNONYMS[s]
    for key, val in _VERDICT_SYNONYMS.items():
        if key in s:
            return val
    return s or "(none)"


def _finding_ids(obj: Any) -> set[str]:
    out = set()
    for f in obj.get("findings", []) or []:
        fid = f.get("id") if isinstance(f, dict) else f
        fid = str(fid or "").strip().lower()
        if fid in _ALLOWED_FINDINGS:
            out.add(fid)
    return out


def score(prediction: dict[str, Any], ground_truth: dict[str, Any]) -> dict[str, Any]:
    pred_v = _norm_verdict(prediction.get("verdict"))
    true_v = _norm_verdict(ground_truth.get("verdict"))
    out: dict[str, Any] = {
        "verdict_correct": 1.0 if pred_v == true_v else 0.0,
        "pred_verdict": pred_v,
        "true_verdict": true_v,
    }

    pred_f, true_f = _finding_ids(prediction), _finding_ids(ground_truth)
    if true_f or pred_f:
        tp = len(pred_f & true_f)
        fp = len(pred_f - true_f)
        fn = len(true_f - pred_f)
        prec = tp / (tp + fp) if (tp + fp) else (1.0 if not true_f else 0.0)
        rec = tp / (tp + fn) if (tp + fn) else 1.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        out.update({"precision": round(prec, 3), "recall": round(rec, 3), "f1": round(f1, 3),
                    "findings_tp": tp, "findings_fp": fp, "findings_fn": fn})
    return out
