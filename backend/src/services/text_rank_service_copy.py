import re
from typing import List, Dict, Any, Tuple

import nltk
from nltk.tokenize import sent_tokenize
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

nltk.download('punkt', quiet=True)


class TextRankService:
    """Enhanced TextRank tailored for academic abstracts/papers (refactored)."""

    def __init__(self, top_k: int = 5, sim_threshold: float = 0.08):
        self.top_k = top_k
        self.sim_threshold = sim_threshold
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 3),
            min_df=1,
            max_df=0.8,
            smooth_idf=True
        )

    # ---------- Preprocessing ----------
    def _preprocess_and_tokenize(self, text: str) -> List[str]:
        clean_text = re.sub(r'\s+', ' ', text).strip()
        return sent_tokenize(clean_text)

    # ---------- Vectorization / Similarity ----------
    def _compute_tfidf_matrix(self, sentences: List[str]):
        return self.vectorizer.fit_transform(sentences)

    def _build_similarity_matrix(self, tfidf_matrix) -> np.ndarray:
        sim = cosine_similarity(tfidf_matrix)
        if self.sim_threshold is not None:
            sim[sim < self.sim_threshold] = 0.0
        # ensure diagonal is zero so PageRank relies on cross-sentence links
        np.fill_diagonal(sim, 0.0)
        return sim

    # ---------- Graph and ranking ----------
    def _build_graph_and_pagerank(self, similarity_matrix: np.ndarray) -> dict:
        graph = nx.from_numpy_array(similarity_matrix)
        return nx.pagerank(graph, alpha=0.85, max_iter=300, tol=1e-6)

    # ---------- Score adjustments ----------
    def _apply_position_bias(self, scores: dict, n: int, bias_strength: float = 0.2) -> dict:
        for i in range(n):
            scores[i] = scores.get(i, 0.0) + bias_strength * (1 - i / max(1, n))
        return scores

    def _apply_length_bonus(self, scores: dict, sentences: List[str], bonus_strength: float = 0.05) -> dict:
        lengths = [len(s.split()) for s in sentences]
        max_len = max(lengths) if lengths else 1
        for i, l in enumerate(lengths):
            scores[i] = scores.get(i, 0.0) + bonus_strength * (l / max_len)
        return scores

    # ---------- Redundancy filtering ----------
    def _redundancy_filter(
        self,
        scored_sentences: List[Dict[str, Any]],
        tfidf_matrix,
        max_selected: int
    ) -> List[Dict[str, Any]]:
        selected = []
        selected_indices = []
        for cand in scored_sentences:
            if len(selected) >= max_selected:
                break
            if not selected:
                selected.append(cand)
                selected_indices.append(cand["index"])
                continue
            too_similar = False
            for s_idx in selected_indices:
                sim = cosine_similarity(tfidf_matrix[cand["index"]], tfidf_matrix[s_idx])[0][0]
                if sim >= 0.75:
                    too_similar = True
                    break
            if not too_similar:
                selected.append(cand)
                selected_indices.append(cand["index"])
        return selected

    # ---------- Formatting ----------
    def _format_results(self, selected: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        final = []
        for rank, item in enumerate(selected[:self.top_k], start=1):
            final.append({
                "sentence": item["sentence"],
                "score": round(item["score"], 6),
                "rank": rank,
                "original_position": item["original_position"]
            })
        return final

    # ---------- Public API ----------
    def extract_key_sentences(self, text: str) -> List[Dict[str, Any]]:
        if not text or len(text.strip()) < 50:
            return [{"sentence": text.strip(), "score": 0.0, "rank": 1, "original_position": 0}]

        sentences = self._preprocess_and_tokenize(text)
        if not sentences:
            return [{"sentence": "Could not extract sentences from text.", "score": 0.0, "rank": 1, "original_position": 0}]

        # compute TF-IDF and similarity
        tfidf_matrix = self._compute_tfidf_matrix(sentences)
        similarity_matrix = self._build_similarity_matrix(tfidf_matrix)

        # PageRank
        scores = self._build_graph_and_pagerank(similarity_matrix)

        # adjustments
        scores = self._apply_position_bias(scores, len(sentences))
        scores = self._apply_length_bonus(scores, sentences)

        # assemble scored list
        scored_sentences = [
            {
                "sentence": sentences[i],
                "score": float(scores.get(i, 0.0)),
                "original_position": i,
                "index": i
            }
            for i in range(len(sentences))
        ]

        # sort by score
        scored_sentences.sort(key=lambda x: x["score"], reverse=True)

        # redundancy filter (optional)
        selected = self._redundancy_filter(scored_sentences, tfidf_matrix, self.top_k)
        final_selection = selected if selected else scored_sentences[:self.top_k]

        return self._format_results(final_selection)
