"""
ROUGE Metrics Calculator
Calculates ROUGE scores (ROUGE-1, ROUGE-2, ROUGE-L) for evaluation of abstractive summaries.
"""

from typing import Dict, List
from rouge_score import rouge_scorer
import logging

logger = logging.getLogger(__name__)


def calculate_rouge_scores(reference: str, candidate: str) -> Dict[str, float]:
    """
    Calculate ROUGE scores between reference and candidate texts.
    
    Args:
        reference: Original document text or reference summary
        candidate: Generated summary to evaluate
        
    Returns:
        Dictionary with rouge1, rouge2, rougeL F1 scores (0.0-1.0 range)
    """
    # Handle empty inputs
    if not reference or not candidate:
        return {
            "rouge1": 0.0,
            "rouge2": 0.0,
            "rougeL": 0.0
        }
    
    try:
        # Initialize scorer with stemming enabled
        scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
        
        # Calculate scores
        scores = scorer.score(reference, candidate)
        
        # Extract F1 scores and round to 3 decimal places
        return {
            "rouge1": round(scores['rouge1'].fmeasure, 3),
            "rouge2": round(scores['rouge2'].fmeasure, 3),
            "rougeL": round(scores['rougeL'].fmeasure, 3)
        }
    except Exception as e:
        logger.warning(f"Error calculating ROUGE scores: {str(e)}")
        return {
            "rouge1": 0.0,
            "rouge2": 0.0,
            "rougeL": 0.0
        }


def calculate_metrics_batch(results: List[Dict]) -> List[Dict]:
    """
    Calculate ROUGE metrics for a batch of results.
    
    Args:
        results: List of result dictionaries containing:
                - abstractive_summary: Generated summary text
                - (optional) original_text: Source document for reference
                
    Returns:
        List of result dictionaries with added 'metrics' field
    """
    for result in results:
        # Skip if no abstractive summary
        if not result.get('abstractive_summary'):
            result['metrics'] = {
                "rouge1": 0.0,
                "rouge2": 0.0,
                "rougeL": 0.0
            }
            continue
        
        # For reference, use original document text if available, otherwise use first key sentences
        reference_text = result.get('original_text', '')
        
        # Fallback: use key sentences as reference if original text not available
        if not reference_text and result.get('extractive', {}).get('key_sentences'):
            key_sentences = result['extractive']['key_sentences']
            reference_text = ' '.join([s.get('sentence', '') for s in key_sentences])
        
        # Calculate ROUGE scores
        metrics = calculate_rouge_scores(
            reference_text,
            result['abstractive_summary']
        )
        
        result['metrics'] = metrics
        logger.debug(f"Calculated metrics for {result.get('filename', 'unknown')}: {metrics}")
    
    return results
