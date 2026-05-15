"""
Simple manual test script for multi-document extraction feature.
Tests the core functionality without requiring pytest.
"""

import sys
sys.path.insert(0, '.')

from src.services.text_rank_service_improved import TextRankService

def test_basic_extraction():
    """Test basic multi-document extraction."""
    print("\n" + "="*70)
    print("TEST 1: Basic Multi-Document Extraction")
    print("="*70)
    
    service = TextRankService(top_k=100, sim_threshold=0.08)
    
    documents = {
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
    
    try:
        result = service.extract_key_sentences_from_collection(
            documents=documents,
            coverage_target=0.35
        )
        
        print(f"✓ Extraction successful")
        print(f"  - Total sentences selected: {result['total_sentences_selected']}")
        print(f"  - Coverage: {result['coverage_statistics']['coverage_percent']:.1f}%")
        print(f"  - Documents represented: {result['coverage_statistics']['docs_represented']}")
        print(f"  - Avg score: {result['coverage_statistics']['avg_score']:.4f}")
        
        print("\n  Top 3 sentences:")
        for i, sent in enumerate(result['extractive_sentences'][:3], 1):
            print(f"  {i}. [{sent['doc_id']}] (score={sent['score']:.4f})")
            print(f"     {sent['sentence'][:80]}...")
        
        return True
    except Exception as e:
        print(f"✗ Extraction failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_coverage_targeting():
    """Test coverage target calculation."""
    print("\n" + "="*70)
    print("TEST 2: Coverage Target Verification")
    print("="*70)
    
    service = TextRankService(top_k=100)
    
    documents = {
        f"doc_{i}": (
            "Reinforcement learning enables agents to learn from interaction. "
            "Temporal difference learning combines Monte Carlo and dynamic programming. "
            "Q-learning is an off-policy algorithm for control. "
            "Policy gradients directly optimize the policy. "
            "Actor-critic methods combine value and policy approaches."
        )
        for i in range(5)
    }
    
    try:
        for target in [0.25, 0.35, 0.50]:
            result = service.extract_key_sentences_from_collection(
                documents=documents,
                coverage_target=target
            )
            actual = result['coverage_statistics']['coverage_percent']
            print(f"✓ Target {target*100:.0f}% → Actual {actual:.1f}%")
        
        return True
    except Exception as e:
        print(f"✗ Coverage targeting failed: {str(e)}")
        return False


def test_provenance_tracking():
    """Test document provenance tracking."""
    print("\n" + "="*70)
    print("TEST 3: Provenance Tracking")
    print("="*70)
    
    service = TextRankService(top_k=100)
    
    documents = {
        "A": "First document has content. It contains multiple sentences. Each sentence is separate.",
        "B": "Second document is different. It has its own sentences. The structure is similar.",
        "C": "Third document completes the set. Additional information is provided. Variety improves results."
    }
    
    try:
        result = service.extract_key_sentences_from_collection(
            documents=documents,
            coverage_target=0.40,
            use_diversity_bonus=True
        )
        
        doc_distribution = result['coverage_statistics']['sentences_per_doc']
        print(f"✓ Provenance tracked successfully")
        print(f"  - Sentences per document: {doc_distribution}")
        
        # Verify all docs are represented
        docs_in_result = set(doc_distribution.keys())
        docs_in_input = set(documents.keys())
        if docs_in_result == docs_in_input:
            print(f"✓ All documents represented: {sorted(docs_in_result)}")
        else:
            print(f"✗ Missing documents: {docs_in_input - docs_in_result}")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Provenance tracking failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_biases_optional():
    """Test that biases are optional."""
    print("\n" + "="*70)
    print("TEST 4: Optional Biases (Pure Global TextRank)")
    print("="*70)
    
    service = TextRankService(top_k=100)
    
    documents = {
        "doc_1": "Machine learning enables computers to learn from data. " * 3,
        "doc_2": "Deep learning uses neural networks with many layers. " * 3
    }
    
    try:
        # Test with both biases
        result_with_bias = service.extract_key_sentences_from_collection(
            documents=documents,
            coverage_target=0.35,
            use_diversity_bonus=True,
            use_position_bonus=True
        )
        print(f"✓ With biases: {result_with_bias['total_sentences_selected']} sentences")
        
        # Test without any biases (pure TextRank)
        result_no_bias = service.extract_key_sentences_from_collection(
            documents=documents,
            coverage_target=0.35,
            use_diversity_bonus=False,
            use_position_bonus=False
        )
        print(f"✓ Without biases: {result_no_bias['total_sentences_selected']} sentences")
        
        return True
    except Exception as e:
        print(f"✗ Bias test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling."""
    print("\n" + "="*70)
    print("TEST 5: Error Handling")
    print("="*70)
    
    service = TextRankService(top_k=100)
    
    tests = [
        ("Empty documents", {}, "documents dict cannot be empty"),
        ("Short documents", {"short": "too"}, "No valid sentences found"),
        ("Invalid coverage", {"doc": "a" * 100}, "coverage_target must be between"),
    ]
    
    passed = 0
    for test_name, docs, expected_error in tests:
        try:
            # Special handling for coverage test
            if "coverage" in test_name:
                service.extract_key_sentences_from_collection(docs, coverage_target=1.5)
            else:
                service.extract_key_sentences_from_collection(docs)
            print(f"✗ {test_name}: Should have raised error")
        except ValueError as e:
            if expected_error.lower() in str(e).lower():
                print(f"✓ {test_name}: Correctly raised ValueError")
                passed += 1
            else:
                print(f"✗ {test_name}: Wrong error message: {str(e)}")
        except Exception as e:
            print(f"✗ {test_name}: Unexpected error: {str(e)}")
    
    return passed == len(tests)


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("MULTI-DOCUMENT GLOBAL TEXTRANK EXTRACTION - TEST SUITE")
    print("="*70)
    
    tests = [
        test_basic_extraction,
        test_coverage_targeting,
        test_provenance_tracking,
        test_biases_optional,
        test_error_handling,
    ]
    
    results = []
    for test_func in tests:
        try:
            results.append(test_func())
        except Exception as e:
            print(f"\n✗ Test {test_func.__name__} crashed: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
