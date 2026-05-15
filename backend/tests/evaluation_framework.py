"""
Evaluation Framework for Enhanced TextRank with Bias Components

This module provides:
1. ROUGE evaluation (automatic metric)
2. Qualitative comparison framework
3. Bias effect analysis
4. Performance testing utilities

ROUGE (Recall-Oriented Understudy for Gisting Evaluation):
- ROUGE-1: Unigram overlap (word-level)
- ROUGE-2: Bigram overlap (phrase-level)
- ROUGE-L: Longest common subsequence (syntax-aware)

Higher ROUGE scores indicate better overlap with reference summaries.
"""

import json
from typing import List, Dict, Any, Tuple
import numpy as np
from collections import Counter
import re


class ROUGEEvaluator:
    """Compute ROUGE metrics for extractive summaries."""

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple word tokenization."""
        return re.findall(r'\w+', text.lower())

    @staticmethod
    def _get_ngrams(tokens: List[str], n: int) -> Counter:
        """Extract n-grams from token list."""
        ngrams = Counter()
        for i in range(len(tokens) - n + 1):
            ngram = tuple(tokens[i:i+n])
            ngrams[ngram] += 1
        return ngrams

    @staticmethod
    def rouge_n(reference: str, candidate: str, n: int = 1) -> Dict[str, float]:
        """
        Compute ROUGE-N score.
        
        Args:
            reference: Reference summary (gold standard)
            candidate: Generated/extracted summary
            n: N-gram size (1, 2, 3, etc.)
            
        Returns:
            Dict with precision, recall, f1
        """
        ref_tokens = ROUGEEvaluator._tokenize(reference)
        cand_tokens = ROUGEEvaluator._tokenize(candidate)
        
        ref_ngrams = ROUGEEvaluator._get_ngrams(ref_tokens, n)
        cand_ngrams = ROUGEEvaluator._get_ngrams(cand_tokens, n)
        
        # Count overlapping n-grams
        overlap = Counter()
        for ngram in cand_ngrams:
            if ngram in ref_ngrams:
                overlap[ngram] = min(cand_ngrams[ngram], ref_ngrams[ngram])
        
        overlap_count = sum(overlap.values())
        ref_count = sum(ref_ngrams.values())
        cand_count = sum(cand_ngrams.values())
        
        # Compute metrics
        precision = overlap_count / cand_count if cand_count > 0 else 0.0
        recall = overlap_count / ref_count if ref_count > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "overlap_count": overlap_count,
            "ref_count": ref_count,
            "cand_count": cand_count
        }

    @staticmethod
    def rouge_l(reference: str, candidate: str) -> Dict[str, float]:
        """
        Compute ROUGE-L (Longest Common Subsequence).
        
        Captures sentence-level structure similarity.
        """
        ref_tokens = ROUGEEvaluator._tokenize(reference)
        cand_tokens = ROUGEEvaluator._tokenize(candidate)
        
        # Compute LCS length using dynamic programming
        m, n = len(ref_tokens), len(cand_tokens)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if ref_tokens[i-1] == cand_tokens[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        lcs_len = dp[m][n]
        
        # Compute metrics
        precision = lcs_len / n if n > 0 else 0.0
        recall = lcs_len / m if m > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "lcs_length": lcs_len
        }

    @staticmethod
    def evaluate_summary(reference: str, candidate: str) -> Dict[str, Any]:
        """
        Comprehensive ROUGE evaluation.
        
        Args:
            reference: Reference summary
            candidate: Generated summary
            
        Returns:
            Dictionary with ROUGE-1, ROUGE-2, ROUGE-L scores
        """
        return {
            "rouge_1": ROUGEEvaluator.rouge_n(reference, candidate, n=1),
            "rouge_2": ROUGEEvaluator.rouge_n(reference, candidate, n=2),
            "rouge_l": ROUGEEvaluator.rouge_l(reference, candidate),
            "reference_length": len(reference.split()),
            "candidate_length": len(candidate.split())
        }


class TextRankComparator:
    """Compare pure TextRank vs. biased TextRank outputs."""

    @staticmethod
    def compare_extractions(
        text: str,
        textrank_pure,  # TextRank service with bias_weight=0
        textrank_biased  # TextRank service with bias_weight > 0
    ) -> Dict[str, Any]:
        """
        Compare outputs from pure and biased TextRank.
        
        Args:
            text: Input abstract
            textrank_pure: Service instance configured for pure TextRank
            textrank_biased: Service instance configured with biases
            
        Returns:
            Detailed comparison including overlap, differences, and scores
        """
        pure_results = textrank_pure.extract_key_sentences(text, return_components=True)
        biased_results = textrank_biased.extract_key_sentences(text, return_components=True)
        
        # Extract sentences
        pure_sentences = set(r["sentence"] for r in pure_results)
        biased_sentences = set(r["sentence"] for r in biased_results)
        
        # Compute set operations
        overlap = pure_sentences & biased_sentences
        only_pure = pure_sentences - biased_sentences
        only_biased = biased_sentences - pure_sentences
        
        # Score comparison
        pure_scores = [r["score"] for r in pure_results]
        biased_scores = [r["score"] for r in biased_results]
        
        return {
            "pure_textrank": {
                "sentences": [r["sentence"] for r in pure_results],
                "scores": pure_scores,
                "components": [r.get("components", {}) for r in pure_results]
            },
            "biased_textrank": {
                "sentences": [r["sentence"] for r in biased_results],
                "scores": biased_scores,
                "components": [r.get("components", {}) for r in biased_results]
            },
            "overlap_analysis": {
                "overlap_count": len(overlap),
                "only_in_pure": len(only_pure),
                "only_in_biased": len(only_biased),
                "overlap_percentage": round(len(overlap) / len(pure_sentences) * 100, 2) if pure_sentences else 0
            },
            "score_statistics": {
                "pure_mean": round(np.mean(pure_scores), 6),
                "pure_std": round(np.std(pure_scores), 6),
                "biased_mean": round(np.mean(biased_scores), 6),
                "biased_std": round(np.std(biased_scores), 6)
            }
        }

    @staticmethod
    def analyze_bias_impact(text: str, textrank_service) -> Dict[str, Any]:
        """
        Analyze individual bias component impact.
        
        Shows how each bias affects sentence selection and scoring.
        """
        # Get diagnostics
        diagnostics = textrank_service.get_bias_diagnostics(text)
        
        if "error" in diagnostics:
            return diagnostics
        
        analysis = {
            "num_sentences": diagnostics["num_sentences"],
            "bias_configuration": {
                "position_bias_enabled": diagnostics["position_bias"]["enabled"],
                "structural_bias_enabled": diagnostics["structural_bias"]["enabled"],
                "keyword_bias_enabled": diagnostics["keyword_bias"]["enabled"],
                "length_penalty_enabled": diagnostics["length_penalty"]["enabled"],
                "overall_bias_weight": diagnostics["bias_weight"]
            },
            "bias_component_ranges": {
                "position_bias": {
                    "min": round(min(diagnostics["position_bias"]["values"]), 4),
                    "max": round(max(diagnostics["position_bias"]["values"]), 4),
                    "mean": round(np.mean(diagnostics["position_bias"]["values"]), 4)
                },
                "structural_bias": {
                    "min": round(min(diagnostics["structural_bias"]["values"]), 4),
                    "max": round(max(diagnostics["structural_bias"]["values"]), 4),
                    "mean": round(np.mean(diagnostics["structural_bias"]["values"]), 4)
                },
                "keyword_bias": {
                    "min": round(min(diagnostics["keyword_bias"]["values"]), 4),
                    "max": round(max(diagnostics["keyword_bias"]["values"]), 4),
                    "mean": round(np.mean(diagnostics["keyword_bias"]["values"]), 4)
                }
            },
            "pagerank_range": {
                "min": round(min(diagnostics["pagerank_scores"].values()), 4),
                "max": round(max(diagnostics["pagerank_scores"].values()), 4),
                "mean": round(np.mean(list(diagnostics["pagerank_scores"].values())), 4)
            }
        }
        
        return analysis


class QualitativeEvaluationGuide:
    """
    Guide for manual qualitative evaluation of extractions.
    
    Use these criteria to assess extraction quality beyond automatic metrics.
    """

    EVALUATION_CRITERIA = {
        "informativeness": {
            "description": "Does the summary convey the main contributions?",
            "scale": "1-5 (1=poor, 5=excellent)",
            "guidelines": [
                "1: Key information is missing or incorrect",
                "2: Some key information present but incomplete",
                "3: Main points covered adequately",
                "4: Comprehensive coverage with clear main ideas",
                "5: Excellent coverage; all key contributions evident"
            ]
        },
        "conciseness": {
            "description": "Is the summary appropriately brief (no redundancy)?",
            "scale": "1-5",
            "guidelines": [
                "1: Very redundant; many duplicate ideas",
                "2: Some redundancy present",
                "3: Acceptable; mostly non-redundant",
                "4: Good variety; minimal overlap",
                "5: Excellent diversity; no redundancy"
            ]
        },
        "coherence": {
            "description": "Does the summary flow logically and make sense?",
            "scale": "1-5",
            "guidelines": [
                "1: Incoherent or confusing",
                "2: Some logical flow but unclear",
                "3: Generally coherent but some gaps",
                "4: Clear and logical flow",
                "5: Excellent coherence and readability"
            ]
        },
        "structural_awareness": {
            "description": "Does summary reflect paper structure (objective→method→result)?",
            "scale": "1-5",
            "guidelines": [
                "1: No clear structure",
                "2: Structure partially evident",
                "3: Basic structure present",
                "4: Clear structure with logical progression",
                "5: Excellent structural representation"
            ]
        },
        "keyword_coverage": {
            "description": "Does summary include important domain terms?",
            "scale": "1-5",
            "guidelines": [
                "1: Few or no key terms",
                "2: Some key terms but important ones missing",
                "3: Most key terms covered",
                "4: Good coverage of domain-specific terms",
                "5: Excellent coverage; all important terms present"
            ]
        }
    }

    @staticmethod
    def create_evaluation_template(
        abstract: str,
        pure_summary: str,
        biased_summary: str
    ) -> Dict[str, Any]:
        """Create a template for manual evaluation comparison."""
        return {
            "abstract": abstract,
            "pure_textrank_summary": pure_summary,
            "biased_textrank_summary": biased_summary,
            "evaluation_guide": QualitativeEvaluationGuide.EVALUATION_CRITERIA,
            "pure_textrank_scores": {
                "informativeness": "___",
                "conciseness": "___",
                "coherence": "___",
                "structural_awareness": "___",
                "keyword_coverage": "___",
                "overall_quality": "___",
                "notes": "___"
            },
            "biased_textrank_scores": {
                "informativeness": "___",
                "conciseness": "___",
                "coherence": "___",
                "structural_awareness": "___",
                "keyword_coverage": "___",
                "overall_quality": "___",
                "notes": "___"
            },
            "comparison": {
                "which_is_better": "___",
                "key_differences": "___",
                "bias_impact_assessment": "___"
            }
        }


# ============= Example Usage =============
if __name__ == "__main__":
    # Example abstract (short for demonstration)
    sample_abstract = """
    We propose a novel graph-based text summarization algorithm that combines position
    bias and structural cues. Our method processes academic abstracts by identifying key
    sentences using a similarity graph. Results show significant improvements over baseline
    TextRank in both ROUGE metrics and qualitative evaluation. The approach effectively
    balances informativeness and conciseness.
    """
    
    # Example reference summary (what you'd compare against)
    reference_summary = """
    A novel graph-based algorithm for text summarization combines position bias and
    structural cues. Results demonstrate improvements over baseline TextRank in ROUGE
    metrics and qualitative evaluation.
    """
    
    # Test ROUGE evaluation
    evaluator = ROUGEEvaluator()
    results = evaluator.evaluate_summary(reference_summary, sample_abstract)
    print("ROUGE Evaluation Results:")
    print(json.dumps(results, indent=2))
    
    # Qualitative template
    print("\n\nQualitative Evaluation Template:")
    template = QualitativeEvaluationGuide.create_evaluation_template(
        sample_abstract,
        "pure textrank extracted summary",
        "biased textrank extracted summary"
    )
    print(json.dumps(template, indent=2))
