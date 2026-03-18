# textrank with position bias
import nltk
from nltk.tokenize import sent_tokenize
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict
import numpy as np

nltk.download('punkt', quiet=True)

class TextRankService:
    """Improved TextRank for academic literature (with position bias)."""
    
    def __init__(self, top_k: int = 8, position_bias: float = 0.15):
        self.top_k = top_k
        self.position_bias = position_bias
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),      # captures phrases like "machine learning"
            min_df=1
        )
    
    def extract_key_sentences(self, text: str) -> List[Dict]:
        if not text or len(text.strip()) < 30:
            return [{"sentence": text.strip(), "score": 1.0, "rank": 1}]
        
        sentences = sent_tokenize(text)
        if len(sentences) <= self.top_k:
            return [
                {"sentence": sent, "score": 1.0, "rank": i+1}
                for i, sent in enumerate(sentences)
            ]
        
        # TF-IDF similarity matrix
        tfidf_matrix = self.vectorizer.fit_transform(sentences)
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Build graph
        nx_graph = nx.from_numpy_array(similarity_matrix)
        
        # PageRank
        scores = nx.pagerank(nx_graph, alpha=0.85)
        
        # Add position bias (first sentences get a boost)
        for i in range(len(sentences)):
            scores[i] += self.position_bias * (1 - i / len(sentences))
        
        # Rank
        ranked = sorted(
            [
                {
                    "sentence": sent,
                    "score": round(scores[i], 4),
                    "rank": i + 1
                }
                for i, sent in enumerate(sentences)
            ],
            key=lambda x: x["score"],
            reverse=True
        )[:self.top_k]
        
        return ranked