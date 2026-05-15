"""
Test suite for multi-document collection extraction feature.

Tests the TextRankService.extract_key_sentences_from_collection() method and
the /api/extract-collection endpoint.
"""

import pytest
from src.services.text_rank_service_improved import TextRankService


# ========== Test Fixtures ==========

@pytest.fixture
def text_rank_service():
    """Create a TextRankService instance for testing."""
    return TextRankService(top_k=100, sim_threshold=0.08)


@pytest.fixture
def sample_documents_2():
    """Two sample academic abstracts."""
    return {
        "paper_1": (
            "Deep learning has revolutionized natural language processing. "
            "Neural networks can learn hierarchical representations of text. "
            "Transformers have become the state-of-the-art architecture. "
            "Attention mechanisms enable parallel processing of sequences. "
            "Pre-trained language models transfer knowledge to downstream tasks."
        ),
        "paper_2": (
            "Graph neural networks extend deep learning to graph-structured data. "
            "Message passing aggregates information from neighboring nodes. "
            "Graph convolutional networks are widely used for node classification. "
            "Knowledge graphs represent structured information efficiently. "
            "Link prediction is an important task in graph learning."
        )
    }


@pytest.fixture
def sample_documents_5():
    """Five sample academic abstracts for larger collection testing."""
    docs = {
        "doc_1": (
            "Reinforcement learning enables agents to learn from interaction. "
            "Temporal difference learning combines Monte Carlo and dynamic programming. "
            "Q-learning is an off-policy algorithm for control. "
            "Policy gradients directly optimize the policy. "
            "Actor-critic methods combine value and policy approaches."
        ),
        "doc_2": (
            "Generative adversarial networks learn to generate realistic samples. "
            "The discriminator distinguishes real from fake data. "
            "The generator learns to fool the discriminator. "
            "Training GANs is notoriously unstable. "
            "Conditional GANs enable controlled generation."
        ),
        "doc_3": (
            "Computer vision has advanced with deep convolutional networks. "
            "ImageNet pre-training provides useful features. "
            "Object detection localizes multiple objects in images. "
            "Semantic segmentation assigns labels to pixels. "
            "Instance segmentation combines detection and segmentation."
        ),
        "doc_4": (
            "Attention mechanisms improve machine translation. "
            "Self-attention allows tokens to attend to all positions. "
            "Multi-head attention captures different representations. "
            "Positional encodings provide sequence order information. "
            "Transformer models scale efficiently to large datasets."
        ),
        "doc_5": (
            "Meta-learning enables rapid adaptation to new tasks. "
            "Few-shot learning achieves good performance with minimal data. "
            "Model-agnostic meta-learning optimizes for fast adaptation. "
            "Prototypical networks learn from few examples. "
            "Siamese networks compare similarity between samples."
        )
    }
    return docs


@pytest.fixture
def single_document():
    """A single document for edge case testing."""
    return {
        "doc_only": (
            "This is a test document with multiple sentences. "
            "Each sentence should be processed independently. "
            "The algorithm must handle single documents gracefully. "
            "Coverage calculations should work for single documents."
        )
    }


@pytest.fixture
def very_short_documents():
    """Documents that are too short to process."""
    return {
        "short_1": "Too short.",
        "short_2": "Also too short."
    }


# ========== Core Functionality Tests ==========

class TestCollectionTokenization:
    """Test _tokenize_collection method."""
    
    def test_tokenize_basic(self, text_rank_service, sample_documents_2):
        """Test basic tokenization with multiple documents."""
        sentences = text_rank_service._tokenize_collection(sample_documents_2)
        
        assert len(sentences) > 0, "Should extract sentences from documents"
        assert all("id" in s for s in sentences), "Each sentence should have an id"
        assert all("text" in s for s in sentences), "Each sentence should have text"
        assert all("doc_id" in s for s in sentences), "Each sentence should have doc_id"
        assert all("sentence_pos" in s for s in sentences), "Each sentence should have position"
        assert all("doc_length" in s for s in sentences), "Each sentence should have doc_length"
    
    def test_tokenize_provenance(self, text_rank_service, sample_documents_2):
        """Test that provenance tracking is correct."""
        sentences = text_rank_service._tokenize_collection(sample_documents_2)
        
        # Check unique document IDs
        doc_ids = set(s["doc_id"] for s in sentences)
        assert doc_ids == {"paper_1", "paper_2"}, "Should have correct doc_ids"
        
        # Check sentence IDs are unique and sequential
        sentence_ids = [s["id"] for s in sentences]
        assert len(sentence_ids) == len(set(sentence_ids)), "Sentence IDs should be unique"
        assert sentence_ids == list(range(len(sentence_ids))), "Sentence IDs should be sequential"
    
    def test_tokenize_empty_dict(self, text_rank_service):
        """Test handling of empty documents dict."""
        sentences = text_rank_service._tokenize_collection({})
        assert sentences == [], "Empty dict should return empty list"
    
    def test_tokenize_short_documents_skipped(self, text_rank_service):
        """Test that very short documents are skipped."""
        docs = {
            "short": "Too short",
            "long": "This is a proper document with multiple sentences. " * 3
        }
        sentences = text_rank_service._tokenize_collection(docs)
        
        # Should only have sentences from "long" document
        doc_ids = set(s["doc_id"] for s in sentences)
        assert "long" in doc_ids, "Should include proper documents"
        assert "short" not in doc_ids, "Should skip very short documents"


class TestDynamicKCalculation:
    """Test _calculate_dynamic_k method."""
    
    def test_k_calculation_35_percent(self, text_rank_service):
        """Test k calculation for 35% coverage."""
        k = text_rank_service._calculate_dynamic_k(total_sentences=100, coverage_target=0.35)
        assert k == 35, "35% of 100 should be 35"
    
    def test_k_calculation_40_percent(self, text_rank_service):
        """Test k calculation for 40% coverage."""
        k = text_rank_service._calculate_dynamic_k(total_sentences=100, coverage_target=0.40)
        assert k == 40, "40% of 100 should be 40"
    
    def test_k_min_boundary(self, text_rank_service):
        """Test that k is at least 1."""
        k = text_rank_service._calculate_dynamic_k(total_sentences=5, coverage_target=0.01)
        assert k >= 1, "k should be at least 1"
    
    def test_k_max_boundary(self, text_rank_service):
        """Test that k does not exceed total_sentences."""
        k = text_rank_service._calculate_dynamic_k(total_sentences=10, coverage_target=0.99)
        assert k <= 10, "k should not exceed total_sentences"
    
    def test_k_zero_sentences(self, text_rank_service):
        """Test handling of zero sentences."""
        k = text_rank_service._calculate_dynamic_k(total_sentences=0, coverage_target=0.35)
        assert k == 1, "Should return 1 for zero sentences"
    
    def test_k_coverage_clamping(self, text_rank_service):
        """Test that coverage_target is clamped to [0.1, 0.9]."""
        k_high = text_rank_service._calculate_dynamic_k(total_sentences=100, coverage_target=1.5)
        k_low = text_rank_service._calculate_dynamic_k(total_sentences=100, coverage_target=0.01)
        
        assert k_high <= 90, "Should clamp excessive coverage target"
        assert k_low >= 10, "Should clamp insufficient coverage target"


class TestCollectionExtractionOutput:
    """Test extract_key_sentences_from_collection output format."""
    
    def test_extraction_output_structure(self, text_rank_service, sample_documents_2):
        """Test that output has correct structure."""
        result = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_2,
            coverage_target=0.35
        )
        
        assert "extractive_sentences" in result, "Should have extractive_sentences key"
        assert "total_sentences_selected" in result, "Should have total_sentences_selected key"
        assert "coverage_statistics" in result, "Should have coverage_statistics key"
    
    def test_extractive_sentences_format(self, text_rank_service, sample_documents_2):
        """Test that each extracted sentence has required fields."""
        result = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_2,
            coverage_target=0.35
        )
        
        for sentence in result["extractive_sentences"]:
            assert "sentence" in sentence, "Should have sentence text"
            assert "score" in sentence, "Should have score"
            assert "doc_id" in sentence, "Should have doc_id"
            assert "sentence_id" in sentence, "Should have sentence_id"
            assert "rank" in sentence, "Should have rank"
            assert "position_in_doc" in sentence, "Should have position_in_doc"
            assert 0 <= sentence["score"] <= 1, "Score should be in [0, 1]"
    
    def test_coverage_statistics(self, text_rank_service, sample_documents_2):
        """Test that coverage_statistics has all required fields."""
        result = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_2,
            coverage_target=0.35
        )
        
        stats = result["coverage_statistics"]
        assert "total_sentences_in_collection" in stats
        assert "coverage_percent" in stats
        assert "total_documents" in stats
        assert "docs_represented" in stats
        assert "sentences_per_doc" in stats
        assert "avg_score" in stats
        assert "min_score" in stats
        assert "max_score" in stats


class TestCoverageTargeting:
    """Test that coverage targets are respected."""
    
    def test_coverage_target_low(self, text_rank_service, sample_documents_5):
        """Test coverage targeting at 30%."""
        result = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_5,
            coverage_target=0.30
        )
        
        total = result["coverage_statistics"]["total_sentences_in_collection"]
        selected = result["total_sentences_selected"]
        coverage = result["coverage_statistics"]["coverage_percent"]
        
        expected_coverage = 30.0
        assert abs(coverage - expected_coverage) < 5, "Coverage should be near target"
    
    def test_coverage_target_high(self, text_rank_service, sample_documents_5):
        """Test coverage targeting at 40%."""
        result = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_5,
            coverage_target=0.40
        )
        
        coverage = result["coverage_statistics"]["coverage_percent"]
        expected_coverage = 40.0
        assert abs(coverage - expected_coverage) < 5, "Coverage should be near target"
    
    def test_coverage_calculation_correctness(self, text_rank_service, sample_documents_2):
        """Test that coverage % is calculated correctly."""
        result = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_2,
            coverage_target=0.35
        )
        
        stats = result["coverage_statistics"]
        total = stats["total_sentences_in_collection"]
        selected = result["total_sentences_selected"]
        coverage = stats["coverage_percent"]
        
        expected_coverage = 100.0 * selected / total
        assert abs(coverage - expected_coverage) < 0.1, "Coverage % should be correctly calculated"


class TestRedundancyFiltering:
    """Test redundancy filtering in collection extraction."""
    
    def test_no_duplicate_sentences(self, text_rank_service, sample_documents_2):
        """Test that no identical sentences are selected."""
        result = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_2,
            coverage_target=0.40,
            redundancy_threshold=0.75
        )
        
        sentences = [s["sentence"] for s in result["extractive_sentences"]]
        assert len(sentences) == len(set(sentences)), "Should not have duplicate sentences"
    
    def test_high_redundancy_threshold(self, text_rank_service, sample_documents_2):
        """Test with high redundancy threshold (less filtering)."""
        result_strict = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_2,
            coverage_target=0.40,
            redundancy_threshold=0.95
        )
        
        result_lenient = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_2,
            coverage_target=0.40,
            redundancy_threshold=0.50
        )
        
        # Higher threshold should allow more similar sentences
        assert (result_strict["total_sentences_selected"] <= 
                result_lenient["total_sentences_selected"]), \
            "Higher threshold should select fewer sentences"


class TestMultiDocumentRepresentation:
    """Test that results represent multiple documents."""
    
    def test_all_documents_represented(self, text_rank_service, sample_documents_5):
        """Test that all documents are represented in results."""
        result = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_5,
            coverage_target=0.35,
            use_diversity_bonus=True
        )
        
        stats = result["coverage_statistics"]
        docs_represented = set(stats["docs_represented"])
        original_docs = set(sample_documents_5.keys())
        
        assert docs_represented == original_docs, "All documents should be represented"
    
    def test_sentences_per_document_balance(self, text_rank_service, sample_documents_5):
        """Test that sentences are somewhat balanced across documents."""
        result = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_5,
            coverage_target=0.35,
            use_diversity_bonus=True
        )
        
        sentences_per_doc = result["coverage_statistics"]["sentences_per_doc"]
        counts = list(sentences_per_doc.values())
        
        # With diversity bonus, no single document should dominate
        # (no document should have > 50% of sentences)
        total_selected = sum(counts)
        for count in counts:
            assert count <= total_selected * 0.6, \
                "No document should have more than 60% of selected sentences"


class TestProvenanceTracking:
    """Test that document provenance is correctly tracked."""
    
    def test_sentence_ids_unique(self, text_rank_service, sample_documents_2):
        """Test that sentence_ids are unique across collection."""
        result = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_2,
            coverage_target=0.35
        )
        
        sentence_ids = [s["sentence_id"] for s in result["extractive_sentences"]]
        assert len(sentence_ids) == len(set(sentence_ids)), \
            "Sentence IDs should be unique across collection"
    
    def test_doc_id_correctness(self, text_rank_service, sample_documents_2):
        """Test that doc_ids match original document keys."""
        result = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_2,
            coverage_target=0.35
        )
        
        doc_ids_in_result = set(s["doc_id"] for s in result["extractive_sentences"])
        original_doc_ids = set(sample_documents_2.keys())
        
        assert doc_ids_in_result.issubset(original_doc_ids), \
            "Result doc_ids should be subset of original doc_ids"


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_empty_documents(self, text_rank_service):
        """Test handling of empty documents dict."""
        with pytest.raises(ValueError, match="documents dict cannot be empty"):
            text_rank_service.extract_key_sentences_from_collection({})
    
    def test_all_short_documents(self, text_rank_service, very_short_documents):
        """Test handling when all documents are too short."""
        with pytest.raises(ValueError, match="No valid sentences found"):
            text_rank_service.extract_key_sentences_from_collection(very_short_documents)
    
    def test_invalid_coverage_target_low(self, text_rank_service, sample_documents_2):
        """Test that invalid coverage target < 0.1 raises error."""
        with pytest.raises(ValueError):
            text_rank_service.extract_key_sentences_from_collection(
                documents=sample_documents_2,
                coverage_target=0.05
            )
    
    def test_invalid_coverage_target_high(self, text_rank_service, sample_documents_2):
        """Test that invalid coverage target > 0.9 raises error."""
        with pytest.raises(ValueError):
            text_rank_service.extract_key_sentences_from_collection(
                documents=sample_documents_2,
                coverage_target=1.5
            )
    
    def test_invalid_redundancy_threshold_low(self, text_rank_service, sample_documents_2):
        """Test that invalid redundancy threshold < 0 raises error."""
        with pytest.raises(ValueError):
            text_rank_service.extract_key_sentences_from_collection(
                documents=sample_documents_2,
                redundancy_threshold=-0.1
            )
    
    def test_invalid_redundancy_threshold_high(self, text_rank_service, sample_documents_2):
        """Test that invalid redundancy threshold > 1 raises error."""
        with pytest.raises(ValueError):
            text_rank_service.extract_key_sentences_from_collection(
                documents=sample_documents_2,
                redundancy_threshold=1.1
            )


class TestBiasesOptional:
    """Test that bias mechanisms are optional."""
    
    def test_disable_diversity_bonus(self, text_rank_service, sample_documents_2):
        """Test extraction without diversity bonus."""
        result = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_2,
            coverage_target=0.35,
            use_diversity_bonus=False
        )
        
        assert result["total_sentences_selected"] > 0, "Should work without diversity bonus"
    
    def test_disable_position_bonus(self, text_rank_service, sample_documents_2):
        """Test extraction without position bonus."""
        result = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_2,
            coverage_target=0.35,
            use_position_bonus=False
        )
        
        assert result["total_sentences_selected"] > 0, "Should work without position bonus"
    
    def test_disable_all_biases(self, text_rank_service, sample_documents_2):
        """Test extraction with pure global TextRank (no biases)."""
        result = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_2,
            coverage_target=0.35,
            use_diversity_bonus=False,
            use_position_bonus=False
        )
        
        assert result["total_sentences_selected"] > 0, "Should work as pure TextRank"


class TestRanking:
    """Test that results are properly ranked."""
    
    def test_rank_field_sequential(self, text_rank_service, sample_documents_2):
        """Test that rank field is sequential starting from 1."""
        result = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_2,
            coverage_target=0.35
        )
        
        ranks = [s["rank"] for s in result["extractive_sentences"]]
        assert ranks == list(range(1, len(ranks) + 1)), "Ranks should be sequential"
    
    def test_scores_sorted(self, text_rank_service, sample_documents_2):
        """Test that sentences with higher scores come first."""
        result = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_2,
            coverage_target=0.35
        )
        
        scores = [s["score"] for s in result["extractive_sentences"]]
        # Scores should be in descending order (highest first)
        assert scores == sorted(scores, reverse=True), "Scores should be in descending order"


# ========== Integration Tests ==========

class TestIntegration:
    """Integration tests for multi-document extraction."""
    
    def test_end_to_end_extraction(self, text_rank_service, sample_documents_5):
        """Test complete extraction pipeline with realistic data."""
        result = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_5,
            coverage_target=0.35,
            redundancy_threshold=0.75,
            use_diversity_bonus=True,
            use_position_bonus=True
        )
        
        # Verify result integrity
        assert result["total_sentences_selected"] > 0
        assert len(result["extractive_sentences"]) == result["total_sentences_selected"]
        assert result["coverage_statistics"]["coverage_percent"] > 0
        assert len(result["coverage_statistics"]["docs_represented"]) > 0
    
    def test_reproducibility(self, text_rank_service, sample_documents_2):
        """Test that results are reproducible (deterministic)."""
        result1 = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_2,
            coverage_target=0.35
        )
        
        result2 = text_rank_service.extract_key_sentences_from_collection(
            documents=sample_documents_2,
            coverage_target=0.35
        )
        
        # Results should be identical
        sentences1 = sorted([s["sentence"] for s in result1["extractive_sentences"]])
        sentences2 = sorted([s["sentence"] for s in result2["extractive_sentences"]])
        assert sentences1 == sentences2, "Results should be reproducible"


# ========== Run Tests ==========
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
