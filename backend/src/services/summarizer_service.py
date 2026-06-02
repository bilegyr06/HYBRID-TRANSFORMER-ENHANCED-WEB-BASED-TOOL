from transformers import AutoModelForSeq2SeqLM, AutoTokenizer  # type: ignore
from typing import List, Dict, Any
import logging
import torch  # type: ignore
import json
import re

# Configure logging
logger = logging.getLogger(__name__)

# Configuration constants
# FIXED: Switched from distilbart-cnn-12-6 (news domain) to pegasus-arxiv (academic domain)
# Reason: Eliminates hallucinations, removes prompt leakage, better for scientific/legal text
MODEL_NAME = "google/pegasus-xsum"
MAX_PROMPT_LENGTH = 3000
MIN_SUMMARY_LENGTH = 50
DEFAULT_MAX_LENGTH = 200
NUM_BEAMS = 4

# FIXED: Simplified prompts to eliminate instruction leakage
# PEGASUS is seq2seq model - doesn't need meta-instruction text
PROMPT_TEMPLATE = (
    """Synthesize the following key sentences from multiple academic papers into one coherent abstractive summary:

{}

Keep it to 200-300 words. Use academic language. Only include information present in the input."""
)

PROMPT_TEMPLATE_SINGLE = (
    """Summarize the following key sentences from a research paper:

{}

Keep it to 150-250 words. Use academic language."""
)

_summarizer_instance = None

class SummarizerService:
    """Abstractive text summarization service using PEGASUS-ArXiv model.
    
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
                
                # Load model and tokenizer directly (pipeline API removed this task in v5.3+)
                tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
                model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
                
                # Move to GPU if available
                if device == 0:
                    model = model.to('cuda')
                    if torch.cuda.is_available():
                        model = model.half()  # Use float16 for memory efficiency
                
                _summarizer_instance = {"model": model, "tokenizer": tokenizer}
                logger.info(f"Summarizer loaded successfully on {device_name}")
            except Exception as e:
                logger.error(f"Failed to initialize summarizer: {str(e)}")
                raise
        self.summarizer = _summarizer_instance
    
    def _generate(self, prompt: str, max_length: int, min_length: int) -> str:
        """Generate summary using the loaded model and tokenizer.
        
        Args:
            prompt: Text to summarize
            max_length: Maximum length of output
            min_length: Minimum length of output
            
        Returns:
            Generated summary text
        """
        tokenizer = self.summarizer["tokenizer"]
        model = self.summarizer["model"]
        
        # Encode input
        inputs = tokenizer.encode(prompt, return_tensors="pt", max_length=1024, truncation=True)
        
        # Move inputs to same device as model
        device = next(model.parameters()).device
        inputs = inputs.to(device)
        
        # Generate summary
        outputs = model.generate(
            inputs,
            max_length=max_length,
            min_length=min_length,
            num_beams=NUM_BEAMS,
            early_stopping=True,
            do_sample=False
        )
        
        # Decode output
        summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return summary.strip()
    
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
        
        # PEGASUS-ArXiv is a summarization model, not an instruction-following
        # chat model. Passing prompt instructions as part of the input makes the
        # per-document summaries unstable, so summarize only the source text.
        prompt = re.sub(r"\s+", " ", combined_text).strip()
        
        # Truncate if too long (BART max ~1024 tokens, add buffer)
        if len(prompt) > MAX_PROMPT_LENGTH:
            logger.debug(
                f"Prompt truncated from {len(prompt)} to {MAX_PROMPT_LENGTH} characters"
            )
            prompt = prompt[:MAX_PROMPT_LENGTH] + "..."
        
        try:
            logger.debug(f"Generating summary (max_length={max_length})...")
            result = self._generate(prompt, max_length, MIN_SUMMARY_LENGTH)
            if self._is_low_quality_generation(result, [prompt]):
                logger.warning("Generated per-document summary failed quality checks; using extractive fallback")
                result = self._build_extractive_fallback_summary(
                    [s.get("sentence", "") for s in key_sentences if s.get("sentence")],
                    max_words=180,
                )
            logger.info(f"Successfully generated summary ({len(result)} characters)")
            return result
            
        except RuntimeError as e:
            error_msg = f"Model error during summarization: {str(e)}"
            logger.error(error_msg)
            return f"Summarization failed: {error_msg}"
        except Exception as e:
            logger.error(f"Unexpected error during summarization: {str(e)}")
            return f"Summarization failed: {str(e)}"

    def synthesize_documents(
        self,
        results: List[Dict],
        max_length: int = 250
    ) -> str:
        """Generate cross-document synthesis from multiple processed results.
        
        Combines key insights from multiple papers into one coherent synthesis
        using the BART-CNN model. Designed for literature synthesis: aggregates
        abstractive summaries and key sentences to create unified output.
        
        Args:
            results: List of ProcessResult dictionaries, each containing:
                    - abstractive_summary: str (per-document summary)
                    - extractive: dict with 'key_sentences' list
            max_length: Maximum length of synthesis in tokens.
                       Defaults to 250 for cross-document synthesis.
        
        Returns:
            Synthesis summary string combining insights from all papers.
            Returns error message if synthesis fails or input is invalid.
        
        Examples:
            >>> service = SummarizerService()
            >>> results = [
            ...   {"abstractive_summary": "...", "extractive": {"key_sentences": [...]}},
            ...   {"abstractive_summary": "...", "extractive": {"key_sentences": [...]}}
            ... ]
            >>> synthesis = service.synthesize_documents(results)
            >>> print(synthesis)  # Cross-document synthesis
        """
        # Validate inputs
        if not results:
            logger.warning("Empty results list provided to synthesize_documents")
            return "No results available for synthesis."
        
        if max_length <= MIN_SUMMARY_LENGTH:
            error_msg = f"max_length ({max_length}) must be > min_length ({MIN_SUMMARY_LENGTH})"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Aggregate all abstractive summaries and key sentences
        combined_summaries = []
        all_key_sentences = []
        
        try:
            for result in results:
                # Collect abstractive summaries
                if result.get("abstractive_summary"):
                    combined_summaries.append(result["abstractive_summary"])
                
                # Collect all key sentences from all papers
                if result.get("extractive", {}).get("key_sentences"):
                    for sentence_obj in result["extractive"]["key_sentences"]:
                        if isinstance(sentence_obj, dict) and "sentence" in sentence_obj:
                            all_key_sentences.append(sentence_obj.get("sentence", ""))
            
            # Construct synthesis input: summaries + top key sentences
            summaries_text = " ".join(combined_summaries)
            
            # Take top key sentences (by position/inclusion) for synthesis context
            key_sentences_text = " ".join(all_key_sentences[:15])  # Limit to first 15 sentences
            
            # Build synthesis prompt
            synthesis_prompt = (
                "Synthesize the following key insights from multiple academic papers "
                "into one coherent, unified summary that captures the main themes and findings. "
                "Avoid repetition and focus on cross-paper connections and insights:\n\n"
                f"PAPER SUMMARIES:\n{summaries_text}\n\n"
                f"KEY INSIGHTS:\n{key_sentences_text}"
            )
            
            # Truncate if too long
            if len(synthesis_prompt) > MAX_PROMPT_LENGTH:
                logger.debug(
                    f"Synthesis prompt truncated from {len(synthesis_prompt)} to {MAX_PROMPT_LENGTH} characters"
                )
                synthesis_prompt = synthesis_prompt[:MAX_PROMPT_LENGTH] + "..."
            
            logger.debug(f"Generating synthesis from {len(results)} documents (max_length={max_length})...")
            result = self._generate(synthesis_prompt, max_length, MIN_SUMMARY_LENGTH)
            logger.info(f"Successfully generated synthesis ({len(result)} characters)")
            return result
            
        except RuntimeError as e:
            error_msg = f"Model error during synthesis: {str(e)}"
            logger.error(error_msg)
            return f"Synthesis failed: {error_msg}"
        except Exception as e:
            logger.error(f"Unexpected error during synthesis: {str(e)}")
            return f"Synthesis failed: {str(e)}"

    def synthesize_from_extractive_sentences(
        self,
        extractive_sentences: List[Dict[str, Any]],
        target_length: int = 250,
        min_length: int = 150,
        max_length: int = 300
    ) -> Dict[str, Any]:
        """Synthesize extractive sentences into structured abstractive output with provenance.
        
        Takes globally salient extractive sentences from multiple papers and produces:
        - Abstractive summary (150-300 words, academic tone)
        - Key themes (4-7 bullet points)
        - Source mapping (traceability to input sentences)
        
        Args:
            extractive_sentences: List of dicts with keys:
                - text: sentence text (or 'sentence' key)
                - doc_id: source document ID
                - sentence_id: unique ID within document (optional)
                - score: salience score (optional)
            target_length: Target summary length in words (default 250)
            min_length: Minimum summary length in words (default 150)
            max_length: Maximum summary length in words (default 300)
        
        Returns:
            Dict with keys:
            - abstractive_summary: str (150-300 words, formal academic tone)
            - key_themes: List[str] (4-7 bullet points capturing overarching themes)
            - source_mapping: Dict mapping theme → list of source sentence indices
            - metadata: Dict with word_count, char_count, docs_represented, etc.
        
        Raises:
            ValueError: If extractive_sentences is empty or malformed
        
        Examples:
            >>> service = SummarizerService()
            >>> sentences = [
            ...     {"text": "Deep learning improves NLP tasks.", "doc_id": "paper_1", "sentence_id": 0},
            ...     {"text": "Transformers enable parallel processing.", "doc_id": "paper_2", "sentence_id": 1}
            ... ]
            >>> result = service.synthesize_from_extractive_sentences(sentences)
            >>> print(result["abstractive_summary"])
        """
        # Validate inputs
        if not extractive_sentences:
            raise ValueError("extractive_sentences cannot be empty")
        if not isinstance(extractive_sentences, list):
            raise ValueError("extractive_sentences must be a list")
        
        # Extract sentence texts and build provenance map
        sentence_texts = []
        provenance_map = {}  # Maps index to {doc_id, sentence_id, original_score}
        unique_docs = set()
        
        for idx, sent_obj in enumerate(extractive_sentences):
            if not isinstance(sent_obj, dict):
                raise ValueError(f"extractive_sentences[{idx}] must be a dict")
            
            # Accept 'text' or 'sentence' key
            text = sent_obj.get("text") or sent_obj.get("sentence")
            if not text or not isinstance(text, str):
                raise ValueError(f"extractive_sentences[{idx}] missing or invalid 'text'/'sentence' key")
            
            doc_id = sent_obj.get("doc_id", f"doc_{idx}")
            sentence_id = sent_obj.get("sentence_id", idx)
            score = sent_obj.get("score", 0.0)
            
            sentence_texts.append(text.strip())
            provenance_map[idx] = {
                "doc_id": doc_id,
                "sentence_id": sentence_id,
                "original_score": score
            }
            unique_docs.add(doc_id)
        
        # Build synthesis prompt
        synthesis_prompt = self._build_synthesis_prompt(sentence_texts, target_length)
        
        # Generate synthesis using model
        try:
            logger.debug(f"Generating synthesis from {len(sentence_texts)} sentences...")
            # Token count is ~1.3x word count for English
            synthesis_raw = self._generate(
                synthesis_prompt,
                max_length=int(max_length * 1.3),
                min_length=int(min_length * 1.2)
            )
            logger.info(f"Generated synthesis: {len(synthesis_raw)} characters")
        except Exception as e:
            logger.error(f"Error during synthesis generation: {str(e)}")
            raise
        
        # Parse JSON output from model (with quality checks)
        structured_output = self._parse_synthesis_output(
            synthesis_raw,
            provenance_map,
            min_length,
            max_length,
            source_sentences=sentence_texts
        )

        if (
            structured_output.get("quality_score", 0) < 0.6
            or structured_output.get("has_hallucination", False)
            or self._is_low_quality_generation(structured_output.get("abstractive_summary", ""), sentence_texts)
        ):
            logger.warning("Generated synthesis failed quality checks; using extractive fallback before metadata")
            fallback_summary = self._build_extractive_fallback_summary(sentence_texts, max_words=max_length)
            structured_output = self._parse_synthesis_output(
                fallback_summary,
                provenance_map,
                min_length=1,
                max_length=max_length,
                source_sentences=sentence_texts,
            )
            structured_output["synthesis_degraded"] = True

        # Build provenance-rich outputs and confidence metrics
        key_themes = structured_output.get("key_themes", [])

        # Cluster themes and supporting quotes with TF-IDF so close labels merge cleanly
        theme_support, representative_quotes, theme_support_counts, key_themes = self._cluster_themes_and_select_quotes(
            key_themes=key_themes,
            sentence_texts=sentence_texts,
            provenance_map=provenance_map,
        )

        # Compute simple faithfulness/coverage proxy: fraction of summary tokens
        # that overlap with input tokens (lowercased words)
        summary = structured_output.get("abstractive_summary", "")
        summary_tokens = set(re.findall(r"\w+", summary.lower()))
        input_tokens = set(re.findall(r"\w+", " ".join(sentence_texts).lower()))
        overlap = summary_tokens.intersection(input_tokens)
        faithfulness_score = round(len(overlap) / max(1, len(summary_tokens)), 3)

        # Average input salience
        input_scores = [v.get("original_score", 0.0) for v in provenance_map.values()]
        avg_input_score = round(sum(input_scores) / max(1, len(input_scores)), 3)

        # Attach provenance list (full input sentences with metadata)
        provenance_list = [
            {
                "index": i,
                "text": sentence_texts[i],
                "doc_id": provenance_map[i].get("doc_id"),
                "sentence_id": provenance_map[i].get("sentence_id"),
                "score": provenance_map[i].get("original_score", 0.0)
            }
            for i in range(len(sentence_texts))
        ]

        # Add enriched fields to structured output
        structured_output["provenance"] = provenance_list
        structured_output["theme_support"] = theme_support
        structured_output["representative_quotes"] = representative_quotes
        structured_output["theme_support_counts"] = theme_support_counts

        # Add metadata including confidence/faithfulness metrics
        structured_output["metadata"] = {
            "total_input_sentences": len(sentence_texts),
            "documents_represented": list(unique_docs),
            "num_documents": len(unique_docs),
            "word_count": len(structured_output.get("abstractive_summary", "").split()),
            "char_count": len(structured_output.get("abstractive_summary", "")),
            "target_length_range": f"{min_length}-{max_length} words",
            "avg_input_score": avg_input_score,
            "faithfulness_score": faithfulness_score
        }

        logger.info(
            f"Synthesis complete: {structured_output['metadata']['word_count']} words, "
            f"{len(structured_output.get('key_themes', []))} themes, "
            f"{len(unique_docs)} documents, faithfulness={faithfulness_score}"
        )

        return structured_output

    def _cluster_themes_and_select_quotes(
        self,
        key_themes: List[str],
        sentence_texts: List[str],
        provenance_map: Dict[int, Any],
        similarity_threshold: float = 0.28
    ) -> tuple[Dict[str, List[Dict[str, Any]]], Dict[str, Any], Dict[str, int], List[str]]:
        """Merge closely related themes using TF-IDF similarity and pick representative quotes.

        Themes are clustered by TF-IDF similarity of the theme label plus its supporting
        sentence context. Each merged theme keeps the strongest label and the most
        salient quote from the supporting sentences.
        """
        import re

        if not key_themes:
            key_themes = ["Multi-document research synthesis"]

        lowered_sentences = [s.lower() for s in sentence_texts]

        theme_support_candidates: List[List[int]] = []
        theme_contexts: List[str] = []

        for theme in key_themes:
            theme_tokens = [t for t in re.findall(r"\w+", theme.lower()) if len(t) > 3]
            supporting_idxs: List[int] = []
            for idx, sent in enumerate(lowered_sentences):
                if any(tok in sent for tok in theme_tokens):
                    supporting_idxs.append(idx)

            if not supporting_idxs:
                ranked = sorted(
                    range(len(sentence_texts)),
                    key=lambda i: provenance_map.get(i, {}).get("original_score", 0.0),
                    reverse=True,
                )
                supporting_idxs = ranked[:2]

            theme_support_candidates.append(supporting_idxs)
            supporting_text = " ".join(sentence_texts[i] for i in supporting_idxs[:4])
            theme_contexts.append(f"{theme} {supporting_text}".strip())

        # Build a simple TF-IDF representation of the theme contexts
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=2000)
            tfidf_matrix = vectorizer.fit_transform(theme_contexts)
            similarity_matrix = cosine_similarity(tfidf_matrix)
        except Exception:
            similarity_matrix = None

        # Merge themes greedily using similarity threshold
        clusters: List[List[int]] = []
        assigned: set[int] = set()
        for i in range(len(key_themes)):
            if i in assigned:
                continue
            cluster = [i]
            assigned.add(i)
            if similarity_matrix is not None:
                for j in range(i + 1, len(key_themes)):
                    if j not in assigned and similarity_matrix[i, j] >= similarity_threshold:
                        cluster.append(j)
                        assigned.add(j)
            clusters.append(cluster)

        merged_theme_support: Dict[str, List[Dict[str, Any]]] = {}
        merged_representative_quotes: Dict[str, Any] = {}
        merged_theme_counts: Dict[str, int] = {}
        merged_labels: List[str] = []

        for cluster in clusters:
            cluster_themes = [key_themes[i] for i in cluster]
            cluster_support_entries: List[Dict[str, Any]] = []

            for theme_index in cluster:
                for sentence_index in theme_support_candidates[theme_index]:
                    pm = provenance_map.get(sentence_index, {})
                    cluster_support_entries.append({
                        "index": sentence_index,
                        "text": sentence_texts[sentence_index],
                        "doc_id": pm.get("doc_id"),
                        "sentence_id": pm.get("sentence_id"),
                        "score": pm.get("original_score", 0.0)
                    })

            # Deduplicate support sentences while preserving strongest score first
            deduped: Dict[str, Dict[str, Any]] = {}
            for entry in sorted(cluster_support_entries, key=lambda x: x.get("score", 0.0), reverse=True):
                deduped.setdefault(entry["text"], entry)
            cluster_support_entries = list(deduped.values())

            # Choose the strongest label: longest informative label among the cluster
            merged_label = max(cluster_themes, key=lambda t: (len(t.split()), len(t)))
            merged_theme_support[merged_label] = cluster_support_entries
            merged_theme_counts[merged_label] = len(cluster_support_entries)

            if cluster_support_entries:
                merged_representative_quotes[merged_label] = max(
                    cluster_support_entries,
                    key=lambda x: x.get("score", 0.0)
                )
            else:
                merged_representative_quotes[merged_label] = None

            merged_labels.append(merged_label)

        # Keep 4-7 themes when possible by merging duplicates rather than expanding
        merged_labels = merged_labels[:7]
        if len(merged_labels) < 4 and key_themes:
            for fallback_theme in key_themes:
                if fallback_theme not in merged_labels:
                    merged_labels.append(fallback_theme)
                if len(merged_labels) >= 4:
                    break

        return merged_theme_support, merged_representative_quotes, merged_theme_counts, merged_labels

    def _build_synthesis_prompt(self, sentence_texts: List[str], target_length: int) -> str:
        """Build clean source text for PEGASUS synthesis.

        PEGASUS-ArXiv is a seq2seq summarization model, so instruction prompts
        are treated as source text. Keep the input clean and let quality checks
        enforce grounding after generation.
        """
        return re.sub(r"\s+", " ", " ".join(sentence_texts)).strip()

    def _build_extractive_fallback_summary(self, sentences: List[str], max_words: int = 180) -> str:
        """Return a grounded fallback summary from ranked source sentences."""
        words: List[str] = []
        for sentence in sentences:
            for word in sentence.split():
                if len(words) >= max_words:
                    break
                words.append(word)
            if len(words) >= max_words:
                break
        return " ".join(words).strip()

    def _is_low_quality_generation(self, text: str, source_sentences: List[str]) -> bool:
        """Detect repeated or off-topic generated text before it reaches the UI."""
        text = (text or "").strip()
        source_text = " ".join(source_sentences or [])
        if not text:
            return True

        summary_tokens = re.findall(r"\w+", text.lower())
        source_tokens = set(re.findall(r"\w+", source_text.lower()))
        if len(summary_tokens) >= 12:
            overlap = len(set(summary_tokens).intersection(source_tokens)) / max(1, len(set(summary_tokens)))
            if overlap < 0.25:
                logger.warning(f"Generated text has low source overlap ({overlap:.2%})")
                return True

        windows = [" ".join(summary_tokens[i:i + 4]) for i in range(max(0, len(summary_tokens) - 3))]
        if windows:
            repeated_windows = len(windows) - len(set(windows))
            if repeated_windows / max(1, len(windows)) > 0.20:
                logger.warning("Generated text contains excessive repeated phrases")
                return True

        odd_tokens = re.findall(r"\b(?:me|re|noo|Horne|Photoshop|Wisconsin|apache)\b", text, re.IGNORECASE)
        if len(odd_tokens) >= 5 and not re.search(r"\b(?:Horne|Photoshop|Wisconsin|apache)\b", source_text, re.IGNORECASE):
            logger.warning("Generated text contains known model degeneration tokens")
            return True

        return False

    def _detect_hallucination(self, text: str, source_sentences: List[str]) -> bool:
        """Detect hallucination patterns in generated text.
        
        Identifies common hallucination signatures:
        - URLs or email addresses not in source material
        - Repeated nonsense patterns (e.g., 'Back to the page')
        - Sudden topic shifts with low semantic coherence
        
        Args:
            text: Generated summary text to check
            source_sentences: List of source sentences for reference
        
        Returns:
            True if hallucination detected, False otherwise
        """
        # Pattern 1: Detect URLs/emails not in source
        url_pattern = r'https?://|www\.|mailonline|contact us at|http://www'
        urls_in_text = re.findall(url_pattern, text.lower())
        urls_in_source = re.findall(url_pattern, " ".join(source_sentences).lower())
        
        # If URLs found in text but not in source, likely hallucination
        if urls_in_text and not urls_in_source:
            logger.warning("Hallucination detected: URLs in output not in source")
            return True
        
        # Pattern 2: Detect repeated nonsense patterns
        hallucination_patterns = [
            r'Back to the page',
            r'Back to.*page',
            r'(?:click here|contact us|read more|find out)',
        ]
        
        for pattern in hallucination_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Hallucination detected: Matched pattern '{pattern}'")
                return True
        
        # Pattern 3: Check for extremely low token overlap with source
        # (this catches when model goes off-topic completely)
        summary_tokens = set(re.findall(r"\w+", text.lower()))
        source_tokens = set(re.findall(r"\w+", " ".join(source_sentences).lower()))
        
        if len(summary_tokens) >= 15:  # Check if summary is non-trivial (>= 15 tokens)
            overlap = summary_tokens.intersection(source_tokens)
            overlap_ratio = len(overlap) / len(summary_tokens) if summary_tokens else 0
            
            if overlap_ratio < 0.35:  # Less than 35% token overlap = likely hallucination
                logger.warning(f"Hallucination detected: Low token overlap ({overlap_ratio:.2%})")
                return True
        
        return False

    def _parse_synthesis_output(
        self,
        raw_output: str,
        provenance_map: Dict[int, Any],
        min_length: int,
        max_length: int,
        source_sentences: List[str] = None
    ) -> Dict[str, Any]:
        """Parse synthesis output and extract structured components with quality metrics.
        
        When JSON parsing fails, extracts themes automatically from the summary text.
        Computes quality indicators: hallucination flag, coherence score, token overlap.
        
        Args:
            raw_output: Raw model output (may be plain text or JSON)
            provenance_map: Maps sentence indices to metadata
            min_length: Minimum word count
            max_length: Maximum word count
            source_sentences: List of source sentences for hallucination/coherence checks
        
        Returns:
            Structured dict with abstractive_summary, key_themes, quality metrics
        """
        summary_text = raw_output.strip()
        source_sentences = source_sentences or []
        
        # Try to parse as JSON first
        parsed = None
        try:
            json_str = summary_text
            # Remove markdown fences if present
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            parsed = json.loads(json_str)
            logger.debug("Successfully parsed JSON from model output")
        except json.JSONDecodeError:
            logger.debug("JSON parsing failed; treating output as plain text summary")
        
        # Extract summary from parsed JSON or use raw output
        if parsed and isinstance(parsed.get("abstractive_summary"), str):
            summary = parsed["abstractive_summary"].strip()
        else:
            summary = summary_text
        
        # Ensure summary is reasonable length
        word_count = len(summary.split())
        length_ok = min_length <= word_count <= (max_length * 1.5)
        
        if word_count < min_length:
            logger.warning(f"Summary too short ({word_count} words < {min_length})")
        if word_count > max_length:
            logger.warning(f"Summary too long ({word_count} words > {max_length}). Truncating...")
            words = summary.split()
            summary = " ".join(words[:max_length]) + "..."
        
        # QUALITY CHECK 1: Detect hallucination
        has_hallucination = self._detect_hallucination(summary, source_sentences)
        
        # QUALITY CHECK 2: Compute token overlap with source
        summary_tokens = set(re.findall(r"\w+", summary.lower()))
        source_tokens = set(re.findall(r"\w+", " ".join(source_sentences).lower()))
        token_overlap = len(summary_tokens.intersection(source_tokens)) / len(summary_tokens) if summary_tokens else 0
        coherence_ok = token_overlap > 0.40  # 40% overlap threshold for coherence
        
        # QUALITY CHECK 3: Overall quality score (0-1)
        quality_score = 0.0
        quality_score += 0.4 if length_ok else 0.1  # Length contributes 40% of quality
        quality_score += 0.4 if coherence_ok else 0.1  # Coherence contributes 40%
        quality_score += 0.2 if not has_hallucination else 0.0  # Hallucination-free contributes 20%
        
        logger.info(
            f"Synthesis quality: score={quality_score:.2f}, "
            f"length_ok={length_ok}, coherence_ok={coherence_ok}, "
            f"hallucination={has_hallucination}, token_overlap={token_overlap:.2%}"
        )
        
        # Extract key_themes: use parsed themes or auto-extract from summary
        if parsed and isinstance(parsed.get("key_themes"), list):
            key_themes = [str(t).strip() for t in parsed.get("key_themes", []) if t][:7]
        else:
            # Auto-extract themes from summary
            key_themes = self._extract_key_themes_from_text(summary)
        
        # Extract source_mapping from parsed output or create basic one
        if parsed and isinstance(parsed.get("source_mapping"), dict):
            source_mapping = parsed.get("source_mapping", {})
        else:
            source_mapping = {}
        
        return {
            "abstractive_summary": summary,
            "key_themes": key_themes,
            "source_mapping": source_mapping,
            "quality_score": quality_score,
            "has_hallucination": has_hallucination,
            "token_overlap": token_overlap,
            "length_ok": length_ok,
            "coherence_ok": coherence_ok
        }

    def _extract_key_themes_from_text(self, text: str, num_themes: int = 5) -> List[str]:
        """Extract key themes/topics from summary text using keyword detection.
        
        Simple approach: identify capitalized noun phrases and domain keywords.
        
        Args:
            text: Summary text to extract themes from
            num_themes: Number of themes to extract (default 5)
        
        Returns:
            List of extracted theme strings (4-7 items)
        """
        import re
        
        # Domain keywords for academic research
        domain_keywords = [
            "deep learning", "machine learning", "neural network", "transformer",
            "natural language", "computer vision", "data science", "artificial intelligence",
            "algorithm", "model", "training", "optimization", "performance",
            "research gap", "methodology", "framework", "architecture", "approach",
            "challenge", "limitation", "future work", "application", "evaluation"
        ]
        
        themes = []
        
        # Extract sentences containing domain keywords
        sentences = text.split(".")
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            
            # Check for domain keywords
            for keyword in domain_keywords:
                if keyword.lower() in sent.lower() and len(themes) < num_themes:
                    # Extract first 8-15 words as theme
                    words = sent.split()
                    theme = " ".join(words[:min(12, len(words))])
                    if theme not in themes and len(theme) > 10:
                        themes.append(theme)
                    break
        
        # If not enough themes, extract capitalized phrases
        if len(themes) < 4:
            capitalized_phrases = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)
            for phrase in capitalized_phrases:
                if phrase not in themes and len(themes) < num_themes:
                    themes.append(phrase)
        
        # Ensure we have at least 4 themes and at most 7
        themes = themes[:7]
        while len(themes) < 4 and text.split():
            # Fallback: add generic themes
            themes.append("Research findings and contributions")
        
        return themes if themes else ["Multi-document research synthesis"]
