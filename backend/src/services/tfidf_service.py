"""
TF-IDF based theme extraction service.
Extracts key themes from text using scikit-learn's TfidfVectorizer.
"""

import logging
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


class ThemeExtractionService:
    """Service for extracting key themes from text using TF-IDF scoring."""

    def __init__(self):
        """Initialize the TF-IDF vectorizer with English stopwords."""
        self.vectorizer = TfidfVectorizer(
            max_features=100,  # Limit to top 100 terms for efficiency
            stop_words='english',
            lowercase=True,
            token_pattern=r'\b\w+\b',
            min_df=1,  # Single document analysis
            max_df=1.0,
            ngram_range=(1, 1),  # Unigrams only (single terms)
        )

    def extract_themes(self, text: str, num_themes: int = 5) -> List[str]:
        """
        Extract key themes from text using TF-IDF scoring.

        Args:
            text: Input text to extract themes from
            num_themes: Number of themes to extract (default: 5)

        Returns:
            List of capitalized theme strings, up to num_themes items
        """
        # Handle edge cases
        if not text or not isinstance(text, str):
            logger.debug("Empty or invalid text provided for theme extraction")
            return []

        # Reject very short text (likely not enough content for meaningful themes)
        if len(text.strip()) < 20:
            logger.debug(f"Text too short ({len(text)} chars) for theme extraction")
            return []

        try:
            # Fit and transform the text
            # TfidfVectorizer.fit_transform returns a sparse matrix
            tfidf_matrix = self.vectorizer.fit_transform([text])

            # Get feature names (terms/words)
            feature_names = self.vectorizer.get_feature_names_out()

            # Get TF-IDF scores for the document (convert sparse matrix to dense, take first row)
            tfidf_scores = tfidf_matrix.toarray()[0]

            # Create list of (term, score) tuples
            term_scores = [
                (term, score)
                for term, score in zip(feature_names, tfidf_scores)
                if score > 0  # Only include terms with non-zero scores
            ]

            # Sort by score descending, then by term length descending (prefer longer terms on tie)
            term_scores.sort(key=lambda x: (-x[1], -len(x[0])))

            # Extract top N themes and capitalize
            themes = [
                term.capitalize() for term, _ in term_scores[:num_themes]
            ]

            logger.debug(
                f"Extracted {len(themes)} themes from text: {themes}"
            )
            return themes

        except Exception as e:
            logger.error(f"Error extracting themes: {str(e)}", exc_info=True)
            return []


# Singleton instance
_theme_service = None


def get_theme_service() -> ThemeExtractionService:
    """Get or create the singleton ThemeExtractionService instance."""
    global _theme_service
    if _theme_service is None:
        logger.info("Initializing ThemeExtractionService")
        _theme_service = ThemeExtractionService()
    return _theme_service
