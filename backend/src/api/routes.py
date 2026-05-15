from fastapi import APIRouter, UploadFile, HTTPException, File, Depends
import shutil
import importlib
from typing import List
from pydantic import BaseModel
import logging
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import get_db
from src.models.user import User
from src.schemas.reviews import SaveReviewRequest, SavedReviewResponse
from src.schemas.analysis import AnalysisRequest
from src.api.dependencies import get_current_user_optional
from src.api.review_routes import save_review_to_db
from src.services.analysis_service import generate_analysis_results
from src.services.text_rank_service_improved import TextRankService
from src.services.summarizer_service import SummarizerService
from src.services.tfidf_service import get_theme_service

# Configure logging
logger = logging.getLogger(__name__)


# Review file-backed endpoints removed (use DB-backed endpoints in review_routes.py)

class ProcessRequest(BaseModel):
    filenames: List[str] = []

class ExtractThemesRequest(BaseModel):
    text: str

class ExtractThemesResponse(BaseModel):
    status: str
    themes: List[str]


class CollectionExtractionRequest(BaseModel):
    """Multi-document collection extraction request."""
    documents: dict  # {doc_id: text}
    coverage_target: float = 0.35
    redundancy_threshold: float = 0.75
    use_diversity_bonus: bool = True
    use_position_bonus: bool = True


class ExtractedSentence(BaseModel):
    """Single extracted sentence with metadata."""
    sentence: str
    score: float
    doc_id: str
    sentence_id: int
    rank: int
    position_in_doc: int


class CoverageStats(BaseModel):
    """Collection coverage statistics."""
    total_sentences_in_collection: int
    coverage_percent: float
    total_documents: int
    docs_represented: List[str]
    sentences_per_doc: dict
    avg_score: float
    min_score: float
    max_score: float


class CollectionExtractionResponse(BaseModel):
    """Multi-document collection extraction response."""
    extractive_sentences: List[ExtractedSentence]
    total_sentences_selected: int
    coverage_statistics: CoverageStats


class SynthesizeRequest(BaseModel):
    """Request body for multi-document synthesis endpoint."""
    extractive_sentences: List[dict] | None = None
    documents: dict | None = None
    action: str | None = "synthesize"  # synthesize | regenerate | export | save
    regen_k: int | None = None
    export_format: str | None = "md"  # md or docx
    title: str | None = None


class SynthesizeResponse(BaseModel):
    status: str
    data: dict
    message: str | None = None


text_rank = TextRankService()
summarizer = SummarizerService()  # loads once when module imports
theme_service = get_theme_service()  # TF-IDF theme extraction service


router = APIRouter(tags=["Upload & Process"])

@router.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(..., description="Drag and drop or select PDF or TXT files")
):
    """Drag-and-drop upload with better encoding handling."""
    uploaded_files = []

    for file in files:
        filename_lower = file.filename.lower()
        if not filename_lower.endswith(('.pdf', '.txt')):
            raise HTTPException(status_code=400, detail=f"Only .pdf and .txt allowed: {file.filename}")

        file_path = settings.UPLOAD_DIR / file.filename

        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract a short preview with tolerant text decoding.
        content_preview = ""
        try:
            if filename_lower.endswith(".pdf"):
                pdfplumber = importlib.import_module("pdfplumber")
                with pdfplumber.open(file_path) as pdf:
                    pages_text = [page.extract_text() or "" for page in pdf.pages]
                    content_preview = "\n".join(pages_text)
            else:  # .txt
                content_preview = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            content_preview = f"[Extraction failed: {str(e)}]"

        uploaded_files.append({
            "filename": file.filename,
            "size_kb": round(file_path.stat().st_size / 1024, 2),
            "preview": content_preview[:500] + "..." if len(content_preview) > 500 else content_preview
        })

    return {
        "status": "success",
        "files_uploaded": len(uploaded_files),
        "details": uploaded_files,
        "message": "Upload successful! Ready for processing."
    }


@router.post("/process")
async def process_documents(request: ProcessRequest):
    """Run full hybrid pipeline: TextRank extractive + BART abstractive.
    
    Delegates to analysis_service for all processing logic.
    Returns ProcessResponse format for backward compatibility with frontend.
    """
    try:
        # Convert to AnalysisRequest and delegate to service
        analysis_request = AnalysisRequest(
            mode="overall",
            filenames=request.filenames,
            compute_rouge=True,
            top_k=5,
            coverage_target=0.35
        )
        
        analysis_response = generate_analysis_results(analysis_request)
        
        # Map AnalysisResponse to ProcessResponse format (backward compatibility)
        return {
            "status": analysis_response.status,
            "processed_files": analysis_response.processed_files,
            "results": [
                {
                    "filename": result.filename,
                    "original_text": "",  # Not included in AnalysisResponse, set empty
                    "extractive": result.extractive,
                    "abstractive_summary": result.abstractive_summary,
                    "key_themes": result.key_themes,
                    "metrics": result.metrics,
                    "error": result.error
                }
                for result in analysis_response.results
            ],
            "overall_synthesis": analysis_response.overall_synthesis,
            "synthesis": analysis_response.synthesis,
            "synthesis_message": analysis_response.synthesis_message
        }
    except Exception as e:
        logger.error(f"Process endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/extract-themes", response_model=ExtractThemesResponse)
async def extract_themes(request: ExtractThemesRequest):
    """
    Extract key themes from text using TF-IDF scoring.
    
    Returns up to 2 most important themes from the input text.
    Filters out common stopwords and returns capitalized terms.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text field cannot be empty")
    
    try:
        themes = theme_service.extract_themes(request.text, num_themes=2)
        return {
            "status": "success",
            "themes": themes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Theme extraction failed: {str(e)}")







@router.post("/extract-collection", response_model=CollectionExtractionResponse)
async def extract_collection_summary(request: CollectionExtractionRequest):
    """
    Extract key sentences from multiple documents using global TextRank.
    
    This endpoint implements multi-document extractive summarization:
    - Builds a global similarity graph across all documents
    - Computes PageRank scores across the entire collection
    - Dynamically selects sentences targeting specified coverage (default 30-40%)
    - Returns ranked sentences with document provenance and statistics
    
    Parameters:
    - documents: Dict mapping doc_id to full text
    - coverage_target: Target coverage ratio (0.30-0.40 recommended)
    - redundancy_threshold: Minimum similarity to exclude duplicates (0-1)
    - use_diversity_bonus: Boost sentences from underrepresented documents
    - use_position_bonus: Boost sentences from start/end of documents
    
    Returns:
    - Ranked extractive sentences with scores and metadata
    - Coverage statistics showing per-document breakdown
    - Quality metrics (avg/min/max scores)
    
    Example:
    ```json
    {
        "documents": {
            "paper_1": "Abstract text...",
            "paper_2": "Another abstract..."
        },
        "coverage_target": 0.35,
        "redundancy_threshold": 0.75
    }
    ```
    """
    # Input validation
    if not request.documents:
        raise HTTPException(status_code=400, detail="documents dict cannot be empty")
    
    if len(request.documents) < 1:
        raise HTTPException(status_code=400, detail="At least 1 document required")
    
    # Validate coverage target
    if not (0.1 <= request.coverage_target <= 0.9):
        raise HTTPException(status_code=400, detail="coverage_target must be between 0.1 and 0.9")
    
    # Validate redundancy threshold
    if not (0.0 <= request.redundancy_threshold <= 1.0):
        raise HTTPException(status_code=400, detail="redundancy_threshold must be between 0.0 and 1.0")
    
    try:
        logger.info(
            f"Multi-document extraction: {len(request.documents)} documents, "
            f"coverage_target={request.coverage_target}"
        )
        
        result = text_rank.extract_key_sentences_from_collection(
            documents=request.documents,
            coverage_target=request.coverage_target,
            redundancy_threshold=request.redundancy_threshold,
            use_diversity_bonus=request.use_diversity_bonus,
            use_position_bonus=request.use_position_bonus
        )
        
        logger.info(
            f"Multi-document extraction complete: "
            f"{result['total_sentences_selected']} sentences selected, "
            f"{result['coverage_statistics']['coverage_percent']:.1f}% coverage"
        )
        
        return result
        
    except ValueError as e:
        logger.error(f"Collection extraction validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Collection extraction failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Collection extraction failed: {str(e)}")


@router.post("/synthesize/multi-document", response_model=SynthesizeResponse)
async def synthesize_multi_document(
    request: SynthesizeRequest,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Synthesize extractive sentences or documents into an abstractive summary.

    Supports actions:
    - synthesize: standard synthesis
    - regenerate: re-run synthesis with truncated top-`regen_k` sentences
    - export: save export (Markdown or Word) to project data folder
    - save: save JSON result to project library
    """
    try:
        action = (request.action or "synthesize").lower()

        # Determine extractive sentences
        extractive = []
        if request.extractive_sentences:
            extractive = request.extractive_sentences
        elif request.documents:
            # Run multi-document extraction to produce extractive sentences
            extraction = text_rank.extract_key_sentences_from_collection(
                documents=request.documents,
                coverage_target=0.35
            )
            # extraction returns dict with 'extractive_sentences' list (dicts matching ExtractedSentence)
            extractive = [
                {
                    "text": s["sentence"] if isinstance(s, dict) else s,
                    "doc_id": s.get("doc_id"),
                    "sentence_id": s.get("sentence_id", 0),
                    "score": s.get("score", 0.0)
                }
                for s in extraction.get("extractive_sentences", [])
            ]

        if not extractive:
            raise HTTPException(status_code=400, detail="No extractive_sentences or documents provided")

        # Handle regenerate: truncate to top-k by score if specified
        if action == "regenerate" and request.regen_k:
            try:
                extractive_sorted = sorted(extractive, key=lambda x: x.get("score", 0.0), reverse=True)
                extractive = extractive_sorted[: max(1, int(request.regen_k))]
            except Exception:
                pass

        # Call synthesizer
        synthesis_result = summarizer.synthesize_from_extractive_sentences(
            extractive_sentences=extractive,
            target_length=250
        )

        # Handle export action: write markdown or docx to DATA_DIR/syntheses
        if action == "export":
            out_dir = settings.DATA_DIR / "syntheses"
            out_dir.mkdir(parents=True, exist_ok=True)
            from datetime import datetime
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            base_name = f"synthesis_{ts}"

            # Build markdown content
            md_lines = ["# Abstractive Synthesis\n"]
            md_lines.append("## Summary\n")
            md_lines.append(synthesis_result.get("abstractive_summary", ""))
            md_lines.append("\n## Key Themes\n")
            for t in synthesis_result.get("key_themes", []):
                md_lines.append(f"- {t}")
            md_lines.append("\n## Representative Quotes\n")
            for theme, quote in synthesis_result.get("representative_quotes", {}).items():
                if quote:
                    md_lines.append(f"- **{theme}**: \"{quote.get('text')}\" ({quote.get('doc_id')})")

            md_content = "\n".join(md_lines)

            if (request.export_format or "md").lower() == "md":
                out_path = out_dir / f"{base_name}.md"
                out_path.write_text(md_content, encoding="utf-8")
                return {"status": "success", "data": synthesis_result, "message": f"Exported to {out_path}"}
            else:
                # Attempt to create a simple Word doc if python-docx available
                try:
                    docx_module = importlib.import_module("docx")
                    Document = getattr(docx_module, "Document")
                    doc = Document()
                    doc.add_heading('Abstractive Synthesis', level=1)
                    doc.add_paragraph(synthesis_result.get('abstractive_summary', ''))
                    doc.add_heading('Key Themes', level=2)
                    for t in synthesis_result.get('key_themes', []):
                        doc.add_paragraph(t, style='List Bullet')
                    out_path = out_dir / f"{base_name}.docx"
                    doc.save(str(out_path))
                    return {"status": "success", "data": synthesis_result, "message": f"Exported to {out_path}"}
                except Exception:
                    raise HTTPException(status_code=501, detail="DOCX export requires `python-docx` package. Install it to enable Word export.")

        # Handle save action: persist JSON to DATA_DIR/syntheses
        if action == "save":
            if current_user is None:
                raise HTTPException(status_code=401, detail="Login required to save synthesis to the project library.")

            extractive_text = "\n\n".join(item.get("text", "") for item in synthesis_result.get("provenance", []))
            save_request = SaveReviewRequest(
                title=request.title,
                input_abstracts_count=max(1, len(synthesis_result.get("metadata", {}).get("documents_represented", []))),
                extractive_summary=extractive_text,
                abstractive_summary=synthesis_result.get("abstractive_summary", ""),
                key_themes=synthesis_result.get("key_themes", []),
                visualizations_metadata={
                    "provenance": synthesis_result.get("provenance", []),
                    "theme_support_counts": synthesis_result.get("theme_support_counts", {}),
                    "representative_quotes": synthesis_result.get("representative_quotes", {}),
                },
                rouge_scores={
                    "faithfulness_score": float(synthesis_result.get("metadata", {}).get("faithfulness_score", 0.0)),
                    "avg_input_score": float(synthesis_result.get("metadata", {}).get("avg_input_score", 0.0)),
                },
            )
            saved_review = save_review_to_db(db, current_user, save_request)
            saved_payload = SavedReviewResponse.model_validate(saved_review).model_dump()
            return {"status": "success", "data": {**synthesis_result, "saved_review": saved_payload}, "message": "Saved to project library."}

        # Default: return synthesis result
        return {"status": "success", "data": synthesis_result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Synthesis endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


# legacy review endpoints removed prefer DB-backed, authenticated routes in review_routes.py

