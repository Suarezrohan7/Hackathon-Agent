"""Scoring — domain-agnostic default, swap in a domain scorer once locked.

A prediction and a ground_truth are both dicts. The default scorer handles the
two shapes the appendix examples use:

  - a single categorical `verdict`  -> exact-match accuracy
  - a list of `findings` (by `id`)  -> precision / recall / F1

`score()` returns a flat dict of numbers; the harness aggregates the means.
"""

from __future__ import annotations

from typing import Any


def score(prediction: dict[str, Any], ground_truth: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}

    if "verdict" in ground_truth:
        pred_v = str(prediction.get("verdict", "")).strip().lower()
        true_v = str(ground_truth["verdict"]).strip().lower()
        out["verdict_correct"] = 1.0 if pred_v == true_v else 0.0
        out["pred_verdict"] = pred_v or "(none)"
        out["true_verdict"] = true_v

    if "findings" in ground_truth:
        pred_ids = {str(f.get("id", f)) for f in prediction.get("findings", [])}
        true_ids = {str(f.get("id", f)) for f in ground_truth["findings"]}
        tp = len(pred_ids & true_ids)
        fp = len(pred_ids - true_ids)
        fn = len(true_ids - pred_ids)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        out.update({"precision": prec, "recall": rec, "f1": f1,
                    "true_positives": tp, "false_positives": fp, "false_negatives": fn})

    if not out:
        out["exact_match"] = 1.0 if prediction == ground_truth else 0.0

    return out


PRIMARY_METRIC = "verdict_correct"   # what the headline table reports; set per domain
