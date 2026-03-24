from fastapi import APIRouter, UploadFile, HTTPException, File
import shutil               # now properly imported — we use it below
import pdfplumber
from typing import List
from pydantic import BaseModel

from src.core.config import settings
from src.services.text_rank_service_copy import TextRankService
from src.services.summarizer_service import SummarizerService

text_rank = TextRankService(top_k=8)
summarizer = SummarizerService()  # loads once when module imports

class ProcessRequest(BaseModel):
    filenames: List[str] = []


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

        # Extract preview — FIXED encoding
        content_preview = ""
        try:
            if filename_lower.endswith(".pdf"):
                with pdfplumber.open(file_path) as pdf:
                    pages_text = [page.extract_text() or "" for page in pdf.pages]
                    content_preview = "\n".join(pages_text)
            else:  # .txt
                content_preview = file_path.read_text(encoding="utf-8", errors="ignore")  # ← this fixes the error
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
    """Run full hybrid pipeline: TextRank extractive → BART abstractive."""

    upload_dir = settings.UPLOAD_DIR
    results = []

    # Determine files to process
    if request.filenames:
        file_paths = [upload_dir / fname for fname in request.filenames]
    else:
        file_paths = list(upload_dir.glob("*.*"))

    for file_path in file_paths:
        if not file_path.exists():
            results.append({"filename": file_path.name, "error": "File not found"})
            continue

        if file_path.name in ("requirements.txt",):  # skip junk
            continue
        
        if file_path.suffix.lower() not in ('.pdf', '.txt'):
            if request.filenames:
                results.append({"filename": file_path.name, "error": "Unsupported file type"})
            continue
        
        try:
            # Extract full text
            if file_path.suffix.lower() == '.pdf':
                with pdfplumber.open(file_path) as pdf:
                    text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            else:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            
            # Extractive step
            key_sentences = text_rank.extract_key_sentences(text)
            
            # Abstractive step
            abstractive_summary = summarizer.generate_summary(key_sentences)
            
            results.append({
                "filename": file_path.name,
                "extractive": {
                    "key_sentences": key_sentences,
                    "total_extracted": len(key_sentences)
                },
                "abstractive_summary": abstractive_summary
            })
        except Exception as e:
            results.append({"filename": file_path.name, "error": str(e)})

    return {
        "status": "success",
        "processed_files": len(results),
        "results": results
    }