from transformers import pipeline  # type: ignore
from typing import List, Dict
import logging
import torch  # type: ignore

# Configure logging
logger = logging.getLogger(__name__)

# Configuration constants
MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
MAX_PROMPT_LENGTH = 3000
MIN_SUMMARY_LENGTH = 50
DEFAULT_MAX_LENGTH = 200
NUM_BEAMS = 4

PROMPT_TEMPLATE = (
    "Summarize the following key insights from multiple academic papers "
    "in a coherent, concise paragraph focusing on main themes and findings:\n\n{}"
)

_summarizer_instance = None

class SummarizerService:
    """Abstractive text summarization service using BART-CNN model.
    
    Uses a singleton pattern to load the model once and reuse across requests.
    Implements device detection for GPU/CPU optimization.
    """
    
    def __init__(self) -> None:
        """Initialize the summarizer with model loading and device detection.
        
        Uses a global singleton pattern to ensure the model is loaded only once
        in memory, reducing overhead for multiple summarization requests.
        Automatically selects GPU if available, falls back to CPU.
        """
        global _summarizer_instance
        if _summarizer_instance is None:
            try:
                device = 0 if torch.cuda.is_available() else -1  # type: ignore
                device_name = "GPU (CUDA)" if device == 0 else "CPU"
                logger.info(f"Initializing summarizer on {device_name}...")
                
                _summarizer_instance = pipeline(
                    "summarization",
                    model=MODEL_NAME,
                    device=device,
                    torch_dtype=torch.float16 if device == 0 else None  # type: ignore
                )
                logger.info(f"Summarizer loaded successfully on {device_name}")
            except RuntimeError as e:
                logger.error(f"Failed to initialize summarizer: {str(e)}")
                raise
        self.summarizer = _summarizer_instance
    
    def generate_summary(
        self,
        key_sentences: List[Dict],
        max_length: int = DEFAULT_MAX_LENGTH
    ) -> str:
        """Generate abstractive summary from ranked sentences.
        
        Combines ranked key sentences into a coherent abstractive summary using
        the BART-CNN model. Implements intelligent truncation and validation to
        ensure robust summarization across varying input sizes.
        
        Args:
            key_sentences: List of dictionaries with "sentence" key containing
                          text to summarize. Typically output from TextRankService.
            max_length: Maximum length of generated summary in tokens.
                       Defaults to 200. Must be > MIN_SUMMARY_LENGTH.
        
        Returns:
            Abstractive summary string. Returns informative error message if
            summarization fails or input is invalid.
        
        Raises:
            ValueError: If max_length is invalid (not > min_length).
            
        Examples:
            >>> service = SummarizerService()
            >>> sentences = [{"sentence": "Earth orbits the sun."}, ...]
            >>> summary = service.generate_summary(sentences, max_length=150)
            >>> print(summary)  # Formatted abstractive summary
        """
        # Validate inputs
        if not key_sentences:
            logger.warning("Empty key_sentences list provided to summarizer")
            return "No key content available for summarization."
        
        if max_length <= MIN_SUMMARY_LENGTH:
            error_msg = f"max_length ({max_length}) must be > min_length ({MIN_SUMMARY_LENGTH})"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validate key_sentences structure
        try:
            combined_text = " ".join(
                [s.get("sentence", "") for s in key_sentences if s.get("sentence")]
            )
            if not combined_text.strip():
                logger.warning("No valid sentences found in key_sentences")
                return "No valid sentences available for summarization."
        except (TypeError, AttributeError) as e:
            logger.error(f"Invalid key_sentences format: {str(e)}")
            return f"Invalid input format: {str(e)}"
        
        # Build prompt with template
        prompt = PROMPT_TEMPLATE.format(combined_text)
        
        # Truncate if too long (BART max ~1024 tokens, add buffer)
        if len(prompt) > MAX_PROMPT_LENGTH:
            logger.debug(
                f"Prompt truncated from {len(prompt)} to {MAX_PROMPT_LENGTH} characters"
            )
            prompt = prompt[:MAX_PROMPT_LENGTH] + "..."
        
        try:
            logger.debug(f"Generating summary (max_length={max_length})...")
            summary = self.summarizer(
                prompt,
                max_length=max_length,
                min_length=MIN_SUMMARY_LENGTH,
                do_sample=False,  # Deterministic output for consistency
                num_beams=NUM_BEAMS,
                early_stopping=True
            )[0]['summary_text']
            
            result = summary.strip()
            logger.info(f"Successfully generated summary ({len(result)} characters)")
            return result
            
        except RuntimeError as e:
            error_msg = f"Model error during summarization: {str(e)}"
            logger.error(error_msg)
            return f"Summarization failed: {error_msg}"
        except (KeyError, IndexError) as e:
            error_msg = f"Unexpected model output format: {str(e)}"
            logger.error(error_msg)
            return f"Summarization failed: {error_msg}"
        except Exception as e:
            logger.error(f"Unexpected error during summarization: {str(e)}")
            return f"Summarization failed: {str(e)}"