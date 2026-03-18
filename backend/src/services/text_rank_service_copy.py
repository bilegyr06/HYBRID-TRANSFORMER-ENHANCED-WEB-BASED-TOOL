import nltk
from nltk.tokenize import sent_tokenize
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict

nltk.download('punkt', quiet=True)

class TextRankService:
    """Enhanced TextRank tailored for academic abstracts/papers."""
    
    def __init__(self, top_k: int = 4):
        self.top_k = top_k
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 3),           # catch phrases like "deep learning model"
            min_df=1,
            max_df=0.8,                   # ignore super-common terms
            smooth_idf=True
        )
    
    def extract_key_sentences(self, text: str) -> List[Dict]:
        if not text or len(text.strip()) < 50:
            return [{"sentence": text.strip(), "score": 1.0, "rank": 1}]
        
        sentences = sent_tokenize(text.strip())
        original_sentences = sentences[:]  # keep original order reference
        
        if len(sentences) <= self.top_k:
            return [
                {"sentence": s, "score": 1.0, "rank": i+1, "original_position": i}
                for i, s in enumerate(sentences)
            ]
        
        # Compute similarity matrix
        tfidf_matrix = self.vectorizer.fit_transform(sentences)
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Graph + PageRank
        graph = nx.from_numpy_array(similarity_matrix)
        scores = nx.pagerank(graph, alpha=0.85, max_iter=300, tol=1e-6)
        
        # Position bias: boost early sentences (common in abstracts: intro/problem → contribution)
        pos_bias = [0.20 * (1 - i / len(sentences)) for i in range(len(sentences))]
        for i in range(len(sentences)):
            scores[i] += pos_bias[i]
        
        # Length normalization (longer informative sentences get slight boost)
        lengths = [len(s.split()) for s in sentences]
        max_len = max(lengths) if lengths else 1
        len_bonus = [0.05 * (l / max_len) for l in lengths]
        for i in range(len(sentences)):
            scores[i] += len_bonus[i]
        
        # Build ranked list
        ranked_list = sorted(
            [
                {
                    "sentence": original_sentences[i],
                    "score": round(float(scores[i]), 4),
                    "rank": idx + 1,
                    "original_position": i
                }
                for idx, i in enumerate(range(len(sentences)))
            ],
            key=lambda x: x["score"],
            reverse=True
        )[:self.top_k]
        
        return ranked_list