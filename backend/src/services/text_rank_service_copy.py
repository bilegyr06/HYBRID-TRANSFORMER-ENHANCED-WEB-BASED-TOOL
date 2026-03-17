# backend/src/services/text_rank_service.py
import nltk
from nltk.tokenize import sent_tokenize
import networkx as nx
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any
import re


def _ensure_nltk_punkt():
    """
    Downloads the NLTK 'punkt' tokenizer models if not already present.
    This is a safer way to handle NLTK data dependencies.
    """
    try:
        nltk.data.find('tokenizers/punkt')
    except nltk.downloader.DownloadError:
        nltk.download('punkt', quiet=True)

_ensure_nltk_punkt()


class TextRankService:
    """
    A service for performing extractive summarization using the TextRank algorithm.
    This implementation uses Semantic Embeddings for sentence vectorization and PageRank for scoring.
    """

    def __init__(self, top_k: int = 10, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initializes the TextRankService.

        Args:
            top_k (int): The number of top-ranked sentences to return.
            model_name (str): The name of the SentenceTransformer model to use.
        """
        self.top_k = top_k
        self.model = SentenceTransformer(model_name)

    def _preprocess_and_tokenize(self, text: str) -> List[str]:
        """Cleans text and tokenizes it into sentences."""
        # Replace multiple whitespace chars (including newlines) with a single space
        clean_text = re.sub(r'\s+', ' ', text).strip()
        return sent_tokenize(clean_text)

    def _build_similarity_matrix(self, sentences: List[str]):
        """Builds a cosine similarity matrix from a list of sentences."""
        embeddings = self.model.encode(sentences)
        return cosine_similarity(embeddings)

    def _calculate_sentence_ranks(self, similarity_matrix) -> Dict[int, float]:
        """Calculates sentence ranks using PageRank on the similarity graph."""
        nx_graph = nx.from_numpy_array(similarity_matrix)
        # Add max_iter to ensure convergence and prevent long runtimes on complex graphs
        return nx.pagerank(nx_graph, alpha=0.85, max_iter=200)

    def extract_key_sentences(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts the most important sentences from a text using TextRank.

        Args:
            text (str): The input text to summarize.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing a
                                  'sentence', its 'score', and its 'rank'.
        """
        if not text or len(text.strip()) < 50:
            return [{"sentence": "Text too short for summarization.", "score": 0.0, "rank": 1}]

        sentences = self._preprocess_and_tokenize(text)

        if not sentences:
            return [{"sentence": "Could not extract sentences from text.", "score": 0.0, "rank": 1}]

        if len(sentences) <= self.top_k:
            return [
                {"sentence": sent, "score": 1.0, "rank": i + 1}
                for i, sent in enumerate(sentences)
            ]

        similarity_matrix = self._build_similarity_matrix(sentences)

        scores = self._calculate_sentence_ranks(similarity_matrix)

        ranked_sentences = sorted(
            [
                {
                    "sentence": sent,
                    "score": round(scores.get(i, 0), 4)
                }
                for i, sent in enumerate(sentences)
            ],
            key=lambda x: x["score"], reverse=True
        )

        # Add rank number to the output and return the top-k
        final_ranked = []
        for i, item in enumerate(ranked_sentences[:self.top_k]):
            item["rank"] = i + 1
            final_ranked.append(item)

        return final_ranked