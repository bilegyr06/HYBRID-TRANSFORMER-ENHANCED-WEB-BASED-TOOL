"""Lightweight evaluation helpers for summary quality metrics.

The helper reports two distinct views of ROUGE:
- self_rouge_* compares the generated summary against the extracted source sentences
- reference_rouge_* compares the generated summary against an optional gold reference

This keeps the metric semantics explicit so callers do not confuse source overlap with
reference-based evaluation.
"""

from __future__ import annotations

from typing import Iterable, Optional

from rouge_score import rouge_scorer


def _concat_sentences(sentences: Iterable[str]) -> str:
    return " ".join(sentence.strip() for sentence in sentences if sentence and sentence.strip())


def compute_rouge_scores(
    abstractive_summary: str,
    extractive_sentences: Iterable[str],
    reference: Optional[str] = None,
) -> dict[str, float]:
    """Compute ROUGE against extracted source text and optional reference text."""

    summary_text = (abstractive_summary or "").strip()
    extractive_text = _concat_sentences(extractive_sentences)

    if not summary_text or not extractive_text:
        scores = {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}
        if reference:
            scores.update({"reference_rouge1": 0.0, "reference_rouge2": 0.0, "reference_rougeL": 0.0})
        return scores

    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    self_scores = scorer.score(extractive_text, summary_text)

    scores = {
        "self_rouge1": round(self_scores["rouge1"].fmeasure, 4),
        "self_rouge2": round(self_scores["rouge2"].fmeasure, 4),
        "self_rougeL": round(self_scores["rougeL"].fmeasure, 4),
        "rouge1": round(self_scores["rouge1"].fmeasure, 4),
        "rouge2": round(self_scores["rouge2"].fmeasure, 4),
        "rougeL": round(self_scores["rougeL"].fmeasure, 4),
    }

    if reference:
        reference_scores = scorer.score(reference, summary_text)
        scores.update(
            {
                "reference_rouge1": round(reference_scores["rouge1"].fmeasure, 4),
                "reference_rouge2": round(reference_scores["rouge2"].fmeasure, 4),
                "reference_rougeL": round(reference_scores["rougeL"].fmeasure, 4),
            }
        )

    return scores
