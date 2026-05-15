# Multi-Document Abstractive Synthesis Feature

## Overview

The `synthesize_from_extractive_sentences()` method in `SummarizerService` enables **multi-document abstractive synthesis with provenance tracking**. It transforms globally salient extractive sentences from multiple research papers into a single coherent abstractive summary with automatically identified key themes.

## API Reference

### Method Signature

```python
def synthesize_from_extractive_sentences(
    self,
    extractive_sentences: List[Dict[str, Any]],
    target_length: int = 250,
    min_length: int = 150,
    max_length: int = 300
) -> Dict[str, Any]
```

### Input Format

**`extractive_sentences`**: List of dictionaries, each with:
- `text` (str, required): The sentence text (or `sentence` key as alternative)
- `doc_id` (str, optional): Source document identifier (default: `doc_0`, `doc_1`, etc.)
- `sentence_id` (int, optional): Position within source document
- `score` (float, optional): Salience/relevance score (e.g., from TextRank)

**Example Input**:
```python
extractive_sentences = [
    {
        "text": "Deep learning models have revolutionized natural language processing.",
        "doc_id": "paper_arxiv_001",
        "sentence_id": 0,
        "score": 0.89
    },
    {
        "text": "Transformer architectures enable parallel processing through attention.",
        "doc_id": "paper_arxiv_002",
        "sentence_id": 2,
        "score": 0.85
    }
]
```

### Output Format

Returns a dictionary with the following structure:

```python
{
    "abstractive_summary": "A 150-300 word coherent synthesis describing...",
    "key_themes": [
        "Theme 1: Description",
        "Theme 2: Description",
        # ... 4-7 themes total
    ],
    "source_mapping": {
        "theme_key": "Supported by sentences: indices...",
        # ...
    },
    "metadata": {
        "total_input_sentences": 8,
        "documents_represented": ["paper_1", "paper_2", "paper_3"],
        "num_documents": 3,
        "word_count": 245,
        "char_count": 1410,
        "target_length_range": "150-300 words"
    }
}
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `extractive_sentences` | List[Dict] | - | **Required**. List of extractive sentence objects with provenance |
| `target_length` | int | 250 | Target summary length in words (informational for model) |
| `min_length` | int | 150 | Minimum acceptable summary length in words |
| `max_length` | int | 300 | Maximum acceptable summary length in words |

### Returns

**Dict** with keys:
- `abstractive_summary` (str): Synthesized summary (150-300 words, academic tone)
- `key_themes` (List[str]): 4-7 identified main themes/patterns/findings
- `source_mapping` (Dict): Maps themes to supporting sentence indices
- `metadata` (Dict): Statistics about input documents and output quality

### Raises

- **ValueError**: If `extractive_sentences` is empty, not a list, or contains malformed entries

## Usage Examples

### Basic Usage

```python
from services.summarizer_service import SummarizerService

service = SummarizerService()

# Prepare extractive sentences (e.g., from TextRankService)
extractive_sentences = [
    {"text": "...", "doc_id": "paper_1", "sentence_id": 0, "score": 0.89},
    {"text": "...", "doc_id": "paper_2", "sentence_id": 1, "score": 0.85},
    # ... more sentences
]

# Generate synthesis
result = service.synthesize_from_extractive_sentences(
    extractive_sentences=extractive_sentences,
    target_length=250,
    min_length=150,
    max_length=300
)

# Access results
print(result["abstractive_summary"])
print(result["key_themes"])
```

### Integration with TextRankService

```python
from services.text_rank_service_improved import TextRankService
from services.summarizer_service import SummarizerService

# Step 1: Extract key sentences from multiple documents using TextRank
textrank = TextRankService(top_k=100)
documents = {
    "paper_1": "Full text of paper 1...",
    "paper_2": "Full text of paper 2...",
    "paper_3": "Full text of paper 3..."
}

extraction_result = textrank.extract_key_sentences_from_collection(
    documents=documents,
    coverage_target=0.35,
    use_diversity_bonus=True
)

# Step 2: Convert extractive result to synthesis input format
extractive_sentences = [
    {
        "text": sent["sentence"],
        "doc_id": sent["doc_id"],
        "sentence_id": sent["sentence_id"],
        "score": sent["score"]
    }
    for sent in extraction_result["extractive_sentences"]
]

# Step 3: Synthesize into abstractive summary with themes
synthesizer = SummarizerService()
synthesis_result = synthesizer.synthesize_from_extractive_sentences(
    extractive_sentences=extractive_sentences,
    target_length=250
)

print(f"Summary: {synthesis_result['abstractive_summary']}")
print(f"Key themes: {synthesis_result['key_themes']}")
print(f"Coverage: {synthesis_result['metadata']['num_documents']} documents")
```

### API Endpoint Usage (for FastAPI)

```python
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from services.summarizer_service import SummarizerService

router = APIRouter()
synthesizer = SummarizerService()

@router.post("/api/v1/synthesize/multi-document")
async def synthesize_multi_document(
    extractive_sentences: List[Dict[str, Any]],
    target_length: int = 250,
    min_length: int = 150,
    max_length: int = 300
):
    """
    Synthesize extractive sentences from multiple papers into structured output.
    
    Request body:
    {
        "extractive_sentences": [
            {
                "text": "...",
                "doc_id": "paper_1",
                "sentence_id": 0,
                "score": 0.89
            }
        ],
        "target_length": 250
    }
    """
    try:
        result = synthesizer.synthesize_from_extractive_sentences(
            extractive_sentences=extractive_sentences,
            target_length=target_length,
            min_length=min_length,
            max_length=max_length
        )
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")
```

## Implementation Details

### Algorithm

1. **Validation**: Ensures input sentences have required fields and are properly formatted
2. **Text Concatenation**: Joins extractive sentences into a document for the BART model
3. **Abstractive Summarization**: Uses BART-CNN to generate a coherent abstractive summary
4. **Theme Extraction**: Automatically identifies 4-7 key themes using:
   - Domain keyword matching (academic/research terms)
   - Capitalized noun phrase extraction
   - Fallback generic themes if insufficient keywords found
5. **Provenance Tracking**: Maintains source document metadata for each extracted sentence
6. **Output Formatting**: Returns structured JSON with summary, themes, mapping, and statistics

### Component Methods

| Method | Purpose |
|--------|---------|
| `_build_synthesis_prompt()` | Prepares text for BART by concatenating sentences |
| `_parse_synthesis_output()` | Parses model output and attempts JSON extraction; falls back to plain text |
| `_extract_key_themes_from_text()` | Identifies key themes using keyword and phrase matching |

## Quality Characteristics

### Output Quality

- **Abstractive Summary**: 
  - Typically 140-300 words (target 250)
  - Academic tone, scientific precision
  - Grounded in source sentences (minimal hallucination)

- **Key Themes**:
  - 4-7 main themes capturing overarching patterns
  - Domain-aware (identifies ML, NLP, methodology terms)
  - Extractive phrases from summary text

- **Source Mapping**:
  - Maps themes to supporting sentences
  - Empty if model doesn't produce explicit mappings
  - Can be enhanced with custom post-processing

### Limitations

1. **Word Count**: Model may produce summaries slightly below target (typically 70-90% of target)
2. **Theme Extraction**: Automatic theme extraction may miss subtle patterns if not keyword-heavy
3. **Model Capacity**: BART handles ~1000 token inputs; longer collections may be truncated
4. **JSON Parsing**: Model doesn't reliably output JSON; fallback to plain text parsing

## Performance

- **Model**: `sshleifer/distilbart-cnn-12-6` (lightweight, ~358M parameters)
- **Device**: GPU (CUDA) if available, CPU fallback
- **Speed**: Typically <5 seconds per synthesis on GPU, <30s on CPU
- **Memory**: ~1GB GPU / ~2GB CPU

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `ValueError: extractive_sentences cannot be empty` | No input provided | Ensure at least 1 sentence is provided |
| `ValueError: ...must be a list` | Wrong input type | Pass a list, not dict or string |
| `ValueError: ...missing or invalid 'text'/'sentence' key` | Malformed sentence object | Ensure each sentence has `text` or `sentence` field |

### Debugging

Enable debug logging to see synthesis process:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now synthesis calls will print debug info
result = service.synthesize_from_extractive_sentences(extractive_sentences)
```

## Future Enhancements

- [ ] Support for JSON output format from model (requires instruction-tuned models)
- [ ] Configurable theme extraction strategies (TF-IDF, clustering, NER)
- [ ] Per-document theme representation metrics
- [ ] Integration with custom LLMs for better instruction following
- [ ] Re-prompting for summaries below minimum word count
- [ ] Explicit conflict/contradiction detection between papers

## Testing

Run the test suite:

```bash
cd backend
python test_synthesis_feature.py
```

Expected output includes:
- Abstractive summary (140-300 words)
- 5+ identified key themes
- Metadata with document statistics
- Validation checks passing

## Related APIs

- `SummarizerService.generate_summary()` — Single-document abstractive summarization
- `SummarizerService.synthesize_documents()` — Cross-document synthesis from ProcessResults
- `TextRankService.extract_key_sentences_from_collection()` — Multi-document extraction
