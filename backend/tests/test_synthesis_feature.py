"""Test script for the new synthesize_from_extractive_sentences feature."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.summarizer_service import SummarizerService


def test_synthesis_feature():
    """Test the new multi-document synthesis feature with provenance."""
    
    print("=" * 80)
    print("Testing Multi-Document Abstractive Synthesis with Provenance")
    print("=" * 80)
    
    # Sample extractive sentences from hypothetical papers
    extractive_sentences = [
        {
            "text": "Deep learning models have revolutionized natural language processing in recent years.",
            "doc_id": "paper_1",
            "sentence_id": 0,
            "score": 0.89
        },
        {
            "text": "Transformer architectures enable parallel processing of sequential data through attention mechanisms.",
            "doc_id": "paper_1",
            "sentence_id": 5,
            "score": 0.85
        },
        {
            "text": "The introduction of BERT demonstrated the effectiveness of bidirectional pre-training.",
            "doc_id": "paper_2",
            "sentence_id": 2,
            "score": 0.82
        },
        {
            "text": "Transfer learning from large pre-trained models significantly improves downstream task performance.",
            "doc_id": "paper_2",
            "sentence_id": 8,
            "score": 0.88
        },
        {
            "text": "However, these large models require substantial computational resources and training data.",
            "doc_id": "paper_3",
            "sentence_id": 1,
            "score": 0.76
        },
        {
            "text": "Model distillation techniques have emerged as a practical solution for deployment in resource-constrained environments.",
            "doc_id": "paper_3",
            "sentence_id": 9,
            "score": 0.79
        },
        {
            "text": "Attention mechanisms provide interpretability by visualizing which input tokens contribute to predictions.",
            "doc_id": "paper_4",
            "sentence_id": 3,
            "score": 0.81
        },
        {
            "text": "Recent advances in prompt engineering have enabled few-shot learning capabilities in large language models.",
            "doc_id": "paper_5",
            "sentence_id": 4,
            "score": 0.84
        }
    ]
    
    print(f"\nInput: {len(extractive_sentences)} extractive sentences from {len(set(s['doc_id'] for s in extractive_sentences))} papers")
    print("\nExtractive sentences:")
    for i, sent in enumerate(extractive_sentences, 1):
        print(f"  {i}. [{sent['doc_id']}] {sent['text'][:70]}...")
    
    # Initialize summarizer
    print("\n[*] Initializing SummarizerService...")
    try:
        service = SummarizerService()
        print("    [OK] Summarizer initialized successfully")
    except Exception as e:
        print(f"    [FAIL] Failed to initialize: {e}")
        return False
    
    # Call the new synthesis method
    print("\n[*] Calling synthesize_from_extractive_sentences()...")
    try:
        result = service.synthesize_from_extractive_sentences(
            extractive_sentences=extractive_sentences,
            target_length=250,
            min_length=150,
            max_length=300
        )
        print("    [OK] Synthesis completed successfully")
    except Exception as e:
        print(f"    [FAIL] Synthesis failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Display results
    print("\n" + "=" * 80)
    print("SYNTHESIS RESULTS")
    print("=" * 80)
    
    print("\n[SUMMARY] ABSTRACTIVE SUMMARY:")
    print("-" * 80)
    print(result["abstractive_summary"])
    print("-" * 80)
    
    print(f"\n[METADATA]:")
    metadata = result.get("metadata", {})
    print(f"  - Word count: {metadata.get('word_count', 'N/A')} words")
    print(f"  - Character count: {metadata.get('char_count', 'N/A')} chars")
    print(f"  - Documents represented: {metadata.get('num_documents', 'N/A')} ({', '.join(metadata.get('documents_represented', []))})")
    print(f"  - Input sentences processed: {metadata.get('total_input_sentences', 'N/A')}")
    print(f"  - Target range: {metadata.get('target_length_range', 'N/A')}")
    
    print(f"\n[THEMES] KEY THEMES ({len(result['key_themes'])} identified):")
    for i, theme in enumerate(result["key_themes"], 1):
        print(f"  {i}. {theme}")
    
    print(f"\n[MAPPING] SOURCE MAPPING:")
    if result["source_mapping"]:
        for theme_key, sources in result["source_mapping"].items():
            print(f"  - {theme_key}: {sources}")
    else:
        print("  (No explicit source mapping in model output)")
    
    # Validation checks
    print("\n" + "=" * 80)
    print("VALIDATION CHECKS")
    print("=" * 80)
    
    checks = []
    
    # Check 1: Word count in range
    word_count = metadata.get('word_count', 0)
    if 150 <= word_count <= 300:
        checks.append(("[OK]", f"Word count in range: {word_count} words (150-300)"))
    else:
        checks.append(("[WARN]", f"Word count out of range: {word_count} words (expected 150-300)"))
    
    # Check 2: Key themes present
    if len(result["key_themes"]) >= 4:
        checks.append(("[OK]", f"Adequate themes: {len(result['key_themes'])} themes (target 4-7)"))
    else:
        checks.append(("[WARN]", f"Few themes: {len(result['key_themes'])} themes (expected 4-7)"))
    
    # Check 3: Source mapping present
    if result["source_mapping"]:
        checks.append(("[OK]", f"Source mapping present: {len(result['source_mapping'])} mappings"))
    else:
        checks.append(("[INFO]", "Source mapping empty (depends on model output)"))
    
    # Check 4: Summary is non-empty
    if result["abstractive_summary"].strip():
        checks.append(("[OK]", "Abstractive summary generated"))
    else:
        checks.append(("[FAIL]", "Abstractive summary is empty"))
    
    for status, msg in checks:
        print(f"  {status} {msg}")
    
    print("\n" + "=" * 80)
    print("Full JSON output:")
    print("=" * 80)
    print(json.dumps(result, indent=2))
    
    return True


if __name__ == "__main__":
    success = test_synthesis_feature()
    sys.exit(0 if success else 1)
