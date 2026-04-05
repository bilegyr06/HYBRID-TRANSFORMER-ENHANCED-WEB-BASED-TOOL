"""
Enhanced TextRank with Research-Aware Biases for Academic Abstracts

This implementation combines TextRank (graph-based ranking) with controlled priors that
represent domain knowledge without replacing the core PageRank mechanism.

Mathematical Formulation:
    Final Score = (1 - β) * PageRank_score + β * Bias_vector
    
    where:
    - β (bias_weight) ∈ [0, 1] controls the influence of priors
    - PageRank_score is the pure graph-based ranking
    - Bias_vector is a normalized combination of academic structural cues

    Bias_vector = (w_pos * position_bias + w_struct * structural_bias + w_keyword * keyword_bias) / norm

Reference: Mihalcea & Tarau (2004) "TextRank: Bringing Order into Texts"
           Brin & Page (1998) "The Anatomy of a Large-Scale Hypertext Search Engine"
"""

import re
from typing import List, Dict, Any, Optional, Tuple
import warnings

import nltk
from nltk.tokenize import sent_tokenize
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

nltk.download('punkt', quiet=True)


class TextRankService:
    """
    Enhanced TextRank with controlled, modular bias mechanisms for academic abstracts.
    
    All bias components are optional and tunable. The system can be reverted to pure
    TextRank by setting bias_weight=0 or by disabling individual bias components.
    """

    def __init__(
        self,
        top_k: int = 5,
        sim_threshold: float = 0.08,
        # Bias control parameters
        bias_weight: float = 0.15,  # Weight of priors vs. PageRank (0 = pure TextRank, 1 = full bias)
        use_position_bias: bool = True,
        use_structural_bias: bool = True,
        use_keyword_bias: bool = True,
        use_length_penalty: bool = True,  # Prevent extreme short/long sentences
        # Bias weighting
        position_weight: float = 0.4,
        structural_weight: float = 0.4,
        keyword_weight: float = 0.2,
        # Fine-tuning
        position_decay: float = 0.3,  # How quickly position importance decays
        keyword_sim_threshold: float = 0.6,  # Minimum similarity for keyword match
        min_sentence_length: int = 5,  # Minimum words to avoid extremely short sentences
    ):
        """
        Initialize TextRank with optional research-aware biases.

        Args:
            top_k: Number of sentences to extract
            sim_threshold: Minimum edge weight in similarity graph (0.08 is conservative)
            bias_weight: Overall influence of biases (0 = pure TextRank, 1 = maximum bias)
            use_position_bias: Apply position-in-text bias
            use_structural_bias: Apply structural cue detection (IMRD + keywords)
            use_keyword_bias: Apply domain-specific keyword overlap
            use_length_penalty: Apply length normalization
            position_weight: Relative importance of position bias
            structural_weight: Relative importance of structural bias
            keyword_weight: Relative importance of keyword bias
            position_decay: Decay rate for position importance (higher = faster decay)
            keyword_sim_threshold: Minimum TF-IDF similarity for keyword matching
            min_sentence_length: Minimum sentence length in words
        """
        self.top_k = top_k
        self.sim_threshold = sim_threshold
        
        # Bias parameters
        self.bias_weight = np.clip(bias_weight, 0.0, 1.0)
        self.use_position_bias = use_position_bias
        self.use_structural_bias = use_structural_bias
        self.use_keyword_bias = use_keyword_bias
        self.use_length_penalty = use_length_penalty
        
        # Bias weighting (normalized internally)
        self.position_weight = max(0.0, position_weight)
        self.structural_weight = max(0.0, structural_weight)
        self.keyword_weight = max(0.0, keyword_weight)
        
        # Fine-tuning
        self.position_decay = np.clip(position_decay, 0.0, 1.0)
        self.keyword_sim_threshold = np.clip(keyword_sim_threshold, 0.0, 1.0)
        self.min_sentence_length = min_sentence_length
        
        # TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 3),
            min_df=1,
            max_df=0.8,
            smooth_idf=True
        )
        
        # Academic keywords for structural cue detection
        # Organized by IMRD (Introduction, Methods, Results, Discussion) structure
        self.structural_keywords = {
            'objective': [
                'objective', 'purpose', 'aim', 'goal', 'investigate', 'propose',
                'present', 'introduce', 'novel', 'new', 'method'
            ],
            'method': [
                'method', 'approach', 'algorithm', 'technique', 'model', 'framework',
                'implementation', 'study', 'experiment', 'conduct', 'develop'
            ],
            'result': [
                'result', 'finding', 'show', 'demonstrate', 'achieve', 'obtain',
                'observe', 'conclude', 'indicate', 'suggest', 'improvement'
            ],
            'conclusion': [
                'conclusion', 'summary', 'conclude', 'significant', 'future',
                'limitation', 'implication', 'advantage', 'important'
            ]
        }

    # ========== Preprocessing ==========
    def _preprocess_and_tokenize(self, text: str) -> List[str]:
        """Clean and tokenize text into sentences."""
        clean_text = re.sub(r'\s+', ' ', text).strip()
        return sent_tokenize(clean_text)

    # ========== Vectorization & Similarity ==========
    def _compute_tfidf_matrix(self, sentences: List[str]):
        """Compute TF-IDF matrix for sentences."""
        return self.vectorizer.fit_transform(sentences)

    def _build_similarity_matrix(self, tfidf_matrix) -> np.ndarray:
        """
        Build similarity matrix with thresholding.
        
        Diagonal is set to 0 to prevent self-loops, ensuring PageRank relies on
        cross-sentence connections (pure graph structure).
        """
        sim = cosine_similarity(tfidf_matrix)
        if self.sim_threshold is not None and self.sim_threshold > 0:
            sim[sim < self.sim_threshold] = 0.0
        np.fill_diagonal(sim, 0.0)  # Remove self-loops
        return sim

    # ========== Pure TextRank Ranking ==========
    def _build_graph_and_pagerank(self, similarity_matrix: np.ndarray) -> dict:
        """
        Compute PageRank scores on similarity graph.
        
        This is the core TextRank mechanism. The personalization vector is not used
        here; instead, we apply biases as a post-processing step to preserve the
        integrity of the ranking algorithm.
        
        Args:
            similarity_matrix: Adjacency matrix of sentence similarities
            
        Returns:
            Dictionary mapping sentence indices to PageRank scores
        """
        graph = nx.from_numpy_array(similarity_matrix)
        return nx.pagerank(graph, alpha=0.85, max_iter=300, tol=1e-6)

    # ========== Bias Mechanisms ==========
    def _compute_position_bias(self, n_sentences: int) -> np.ndarray:
        """
        Compute position-based bias for sentences.
        
        Academic writing convention: Important information (objective, hypothesis)
        typically appears early; conclusions appear later.
        
        Formula: bias[i] = exp(-position_decay * i / n) if i < n/2 else exp(-position_decay * (n-i) / n)
        
        This creates a U-shaped bias favoring opening and closing sentences, with
        exponential decay controlled by position_decay parameter.
        
        Args:
            n_sentences: Total number of sentences
            
        Returns:
            Array of position biases (normalized to [0, 1])
        """
        if n_sentences <= 1:
            return np.array([1.0])
        
        bias = np.zeros(n_sentences)
        decay = self.position_decay
        
        for i in range(n_sentences):
            # Exponential decay from both ends
            dist_from_start = i
            dist_from_end = n_sentences - 1 - i
            
            # Apply decay (sentences near start/end get higher bias)
            bias_start = np.exp(-decay * dist_from_start / max(1, n_sentences / 2))
            bias_end = np.exp(-decay * dist_from_end / max(1, n_sentences / 2))
            
            # Take maximum to create U-shape
            bias[i] = max(bias_start, bias_end)
        
        # Normalize to [0, 1]
        bias_min, bias_max = bias.min(), bias.max()
        if bias_max > bias_min:
            bias = (bias - bias_min) / (bias_max - bias_min)
        
        return bias

    def _compute_structural_bias(self, sentences: List[str]) -> np.ndarray:
        """
        Compute bias based on presence of academic structural cues.
        
        Detects keywords from the IMRD framework (Introduction, Methods,
        Results, Discussion). Each sentence gets a score based on keyword overlap.
        
        Formula: structural_bias[i] = count_of_matching_keywords[i] / total_keywords_in_sentence[i]
        
        Args:
            sentences: List of sentences
            
        Returns:
            Array of structural biases (normalized to [0, 1])
        """
        bias = np.zeros(len(sentences))
        
        # Flatten all keywords
        all_keywords = set()
        for keywords in self.structural_keywords.values():
            all_keywords.update(keywords)
        
        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            # Count keyword matches (case-insensitive)
            matches = sum(1 for kw in all_keywords if re.search(r'\b' + kw + r'\b', sentence_lower))
            # Normalize by sentence length to avoid bias toward longer sentences
            words = len(sentence.split())
            if words > 0:
                bias[i] = min(1.0, matches / max(1, words / 5))  # Cap at 1.0
        
        # Normalize to [0, 1]
        if bias.max() > 0:
            bias = bias / bias.max()
        
        return bias

    def _compute_keyword_bias(self, sentences: List[str], tfidf_matrix) -> np.ndarray:
        """
        Compute bias based on domain-specific keyword prominence.
        
        Sentences with higher term frequency across the document (as measured by
        TF-IDF) are considered more representative of the document's main topics.
        
        Formula: keyword_bias[i] = mean_tfidf_score[i]
        
        Args:
            sentences: List of sentences
            tfidf_matrix: TF-IDF matrix (sparse matrix)
            
        Returns:
            Array of keyword biases (normalized to [0, 1])
        """
        # Compute mean TF-IDF score per sentence (ignoring zeros)
        bias = np.asarray(tfidf_matrix.mean(axis=1)).flatten()
        
        # Normalize to [0, 1]
        if bias.max() > 0:
            bias = (bias - bias.min()) / (bias.max() - bias.min())
        
        return bias

    def _compute_length_penalty(self, sentences: List[str]) -> np.ndarray:
        """
        Compute length normalization to prevent extreme short/long sentence bias.
        
        Very short sentences (< min_length) get penalized.
        Very long sentences (> 3x median length) get slightly penalized.
        Normal-length sentences get neutral (1.0) score.
        
        Formula: penalty[i] = exp(-0.5 * ((length[i] - median) / std)^2) if length > min
                            = exp(-length_deviation) otherwise
        
        Args:
            sentences: List of sentences
            
        Returns:
            Array of length penalties (normalized to [0, 1], where 1 = no penalty)
        """
        lengths = np.array([len(s.split()) for s in sentences])
        
        # Very short sentences get penalized heavily
        penalty = np.ones(len(sentences))
        short_mask = lengths < self.min_sentence_length
        if short_mask.any():
            penalty[short_mask] = 0.1  # 90% penalty for very short sentences
        
        # Very long sentences get mild penalty (Gaussian over deviations from median)
        if len(lengths) > 1:
            median_length = np.median(lengths[~short_mask])
            std_length = np.std(lengths[~short_mask]) + 1e-6  # Avoid division by zero
            # Gaussian penalty over standardized length
            normalized_lengths = (lengths - median_length) / std_length
            long_penalty = np.exp(-0.1 * normalized_lengths ** 2)
            penalty = penalty * long_penalty
        
        # Normalize to [0, 1]
        if penalty.max() > 0:
            penalty = penalty / penalty.max()
        
        return penalty

    def _compute_combined_bias(
        self,
        sentences: List[str],
        tfidf_matrix,
        n_sentences: int
    ) -> np.ndarray:
        """
        Combine individual bias components into a single prior vector.
        
        Each bias component is weighted and normalized. This creates a prior
        that will be combined with PageRank via:
            Final_score = (1 - bias_weight) * pagerank + bias_weight * combined_bias
        
        Args:
            sentences: List of sentences
            tfidf_matrix: TF-IDF matrix
            n_sentences: Total sentences
            
        Returns:
            Combined bias vector (normalized to [0, 1])
        """
        combined = np.zeros(n_sentences)
        total_weight = 0.0
        
        # Position bias
        if self.use_position_bias and self.position_weight > 0:
            pos_bias = self._compute_position_bias(n_sentences)
            combined += self.position_weight * pos_bias
            total_weight += self.position_weight
        
        # Structural bias
        if self.use_structural_bias and self.structural_weight > 0:
            struct_bias = self._compute_structural_bias(sentences)
            combined += self.structural_weight * struct_bias
            total_weight += self.structural_weight
        
        # Keyword bias
        if self.use_keyword_bias and self.keyword_weight > 0:
            kw_bias = self._compute_keyword_bias(sentences, tfidf_matrix)
            combined += self.keyword_weight * kw_bias
            total_weight += self.keyword_weight
        
        # Length penalty
        if self.use_length_penalty:
            length_penalty = self._compute_length_penalty(sentences)
            combined = combined * length_penalty
        
        # Normalize
        if total_weight > 0:
            combined = combined / total_weight
        
        # Ensure values in [0, 1]
        combined = np.clip(combined, 0.0, 1.0)
        
        return combined

    def _blend_scores(self, pagerank_scores: dict, bias_vector: np.ndarray) -> dict:
        """
        Blend PageRank scores with bias vector.
        
        Mathematical formulation:
            score[i] = (1 - β) * pagerank[i] + β * bias[i]
        
        where β = bias_weight. This ensures:
        - β = 0: Pure TextRank (no bias)
        - β = 1: Bias-only ranking (rarely useful)
        - 0 < β < 0.3: TextRank with subtle guidance (recommended)
        
        Args:
            pagerank_scores: Dict of PageRank scores per sentence
            bias_vector: Array of bias values
            
        Returns:
            Dictionary of blended scores
        """
        blended = {}
        for i in range(len(bias_vector)):
            pr_score = pagerank_scores.get(i, 0.0)
            bias_score = bias_vector[i]
            blended[i] = (1 - self.bias_weight) * pr_score + self.bias_weight * bias_score
        
        return blended

    # ========== Redundancy Filtering ==========
    def _redundancy_filter(
        self,
        scored_sentences: List[Dict[str, Any]],
        tfidf_matrix,
        max_selected: int,
        redundancy_threshold: float = 0.75
    ) -> List[Dict[str, Any]]:
        """
        Filter redundant sentences from the top-k candidates.
        
        Greedy approach: select highest-scoring sentences that are not too similar
        to previously selected sentences. This maximizes information diversity.
        
        Args:
            scored_sentences: Pre-sorted list of sentences with scores
            tfidf_matrix: TF-IDF matrix for similarity computation
            max_selected: Maximum sentences to select
            redundancy_threshold: Minimum similarity to exclude as redundant
            
        Returns:
            Non-redundant selection of sentences
        """
        selected = []
        selected_indices = []
        
        for cand in scored_sentences:
            if len(selected) >= max_selected:
                break
            
            if not selected:
                # First sentence always selected
                selected.append(cand)
                selected_indices.append(cand["index"])
                continue
            
            # Check similarity to all previously selected sentences
            too_similar = False
            for s_idx in selected_indices:
                sim = cosine_similarity(tfidf_matrix[cand["index"]], tfidf_matrix[s_idx])[0][0]
                if sim >= redundancy_threshold:
                    too_similar = True
                    break
            
            if not too_similar:
                selected.append(cand)
                selected_indices.append(cand["index"])
        
        return selected

    # ========== Formatting & Output ==========
    def _format_results(self, selected: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format final results with ranking, scores, and metadata.
        
        Returns sentences in original document order (not score order) for readability.
        """
        # Sort by original position to maintain document flow
        selected_by_pos = sorted(selected, key=lambda x: x["original_position"])
        
        final = []
        for rank, item in enumerate(selected_by_pos[:self.top_k], start=1):
            final.append({
                "sentence": item["sentence"],
                "score": round(item["score"], 6),
                "rank": rank,
                "original_position": item["original_position"],
                "components": item.get("components", {})  # Individual bias components
            })
        
        return final

    # ========== Main Public API ==========
    def extract_key_sentences(self, text: str, return_components: bool = False) -> List[Dict[str, Any]]:
        """
        Extract key sentences using enhanced TextRank with optional biases.
        
        Pipeline:
        1. Preprocess and tokenize into sentences
        2. Compute TF-IDF and similarity matrix
        3. Compute PageRank scores (pure TextRank)
        4. Compute bias vector (optional)
        5. Blend scores: final = (1-β)*PageRank + β*Bias
        6. Apply redundancy filtering
        7. Return results in original order
        
        Args:
            text: Input text (typically an abstract or document)
            return_components: If True, include individual bias components in output
            
        Returns:
            List of extracted sentences with scores and metadata
        """
        # Handle edge cases
        if not text or len(text.strip()) < 50:
            return [{
                "sentence": text.strip(),
                "score": 1.0,
                "rank": 1,
                "original_position": 0,
                "components": {"note": "Text too short for extraction"}
            }]
        
        # Tokenize into sentences
        sentences = self._preprocess_and_tokenize(text)
        if not sentences:
            return [{
                "sentence": "Could not extract sentences from text.",
                "score": 0.0,
                "rank": 1,
                "original_position": 0,
                "components": {"note": "Tokenization failed"}
            }]
        
        # Compute TF-IDF and similarity
        tfidf_matrix = self._compute_tfidf_matrix(sentences)
        similarity_matrix = self._build_similarity_matrix(tfidf_matrix)
        
        # Compute pure TextRank (PageRank on similarity graph)
        pagerank_scores = self._build_graph_and_pagerank(similarity_matrix)
        
        # Compute and blend bias vector
        bias_vector = self._compute_combined_bias(sentences, tfidf_matrix, len(sentences))
        blended_scores = self._blend_scores(pagerank_scores, bias_vector)
        
        # Assemble scored sentences
        scored_sentences = []
        for i in range(len(sentences)):
            components = {}
            if return_components:
                components = {
                    "pagerank": round(pagerank_scores.get(i, 0.0), 6),
                    "bias": round(bias_vector[i], 6),
                    "blended": round(blended_scores.get(i, 0.0), 6)
                }
            
            scored_sentences.append({
                "sentence": sentences[i],
                "score": float(blended_scores.get(i, 0.0)),
                "original_position": i,
                "index": i,
                "components": components
            })
        
        # Sort by score (descending)
        scored_sentences.sort(key=lambda x: x["score"], reverse=True)
        
        # Apply redundancy filtering
        selected = self._redundancy_filter(scored_sentences, tfidf_matrix, self.top_k)
        final_selection = selected if selected else scored_sentences[:self.top_k]
        
        return self._format_results(final_selection)

    # ========== Diagnostic & Evaluation Methods ==========
    def get_bias_diagnostics(self, text: str) -> Dict[str, Any]:
        """
        Return detailed diagnostics on how each bias component affects scoring.
        
        Useful for understanding bias contributions and tuning parameters.
        
        Returns:
            Dictionary with bias weight analysis
        """
        if not text or len(text.strip()) < 50:
            return {"error": "Text too short for analysis"}
        
        sentences = self._preprocess_and_tokenize(text)
        if not sentences:
            return {"error": "Could not tokenize text"}
        
        tfidf_matrix = self._compute_tfidf_matrix(sentences)
        similarity_matrix = self._build_similarity_matrix(tfidf_matrix)
        pagerank_scores = self._build_graph_and_pagerank(similarity_matrix)
        
        # Compute individual biases
        pos_bias = self._compute_position_bias(len(sentences))
        struct_bias = self._compute_structural_bias(sentences)
        kw_bias = self._compute_keyword_bias(sentences, tfidf_matrix)
        length_penalty = self._compute_length_penalty(sentences)
        
        diagnostics = {
            "num_sentences": len(sentences),
            "bias_weight": self.bias_weight,
            "position_bias": {
                "enabled": self.use_position_bias,
                "weight": self.position_weight,
                "values": pos_bias.tolist()
            },
            "structural_bias": {
                "enabled": self.use_structural_bias,
                "weight": self.structural_weight,
                "values": struct_bias.tolist()
            },
            "keyword_bias": {
                "enabled": self.use_keyword_bias,
                "weight": self.keyword_weight,
                "values": kw_bias.tolist()
            },
            "length_penalty": {
                "enabled": self.use_length_penalty,
                "values": length_penalty.tolist()
            },
            "pagerank_scores": {i: round(v, 6) for i, v in pagerank_scores.items()},
        }
        
        return diagnostics

    def revert_to_pure_textrank(self):
        """Disable all biases to revert to pure TextRank algorithm."""
        self.bias_weight = 0.0
        self.use_position_bias = False
        self.use_structural_bias = False
        self.use_keyword_bias = False
        warnings.warn("All biases disabled. Running pure TextRank.", UserWarning)
