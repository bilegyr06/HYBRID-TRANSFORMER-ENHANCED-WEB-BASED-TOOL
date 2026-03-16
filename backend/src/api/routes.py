from fastapi import APIRouter, UploadFile, HTTPException
import shutil               # now properly imported — we use it below
import pdfplumber

from src.core.config import settings

router = APIRouter(tags=["Upload"])


@router.post("/upload")
async def upload_documents(files: list[UploadFile]):
    """
    Accepts one or multiple files via drag-and-drop.
    Supported formats: .pdf, .txt
    Returns basic metadata + short preview of extracted text.
    """
    uploaded_files = []

    for file in files:
        filename_lower = file.filename.lower()
        if not filename_lower.endswith(('.pdf', '.txt')):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.filename}. Only .pdf and .txt allowed."
            )

        # Build safe destination path
        file_path = settings.UPLOAD_DIR / file.filename

        # Save the uploaded file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)           # ← here is where shutil is used

        # Extract preview — improved encoding handling
        content_preview = ""
        try:
            if filename_lower.endswith(".pdf"):
                with pdfplumber.open(file_path) as pdf:
                    pages_text = [page.extract_text() or "" for page in pdf.pages]
                    content_preview = "\n".join(pages_text)
            else:  # .txt
                content_preview = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            content_preview = f"[Extraction failed: {str(e)}]"

        # Prepare response item
        uploaded_files.append({
            "filename": file.filename,
            "size_kb": round(file_path.stat().st_size / 1024, 2),
            "preview": (
                content_preview[:500] + "..." 
                if len(content_preview) > 500 
                else content_preview
            )
        })

    return {
        "status": "success",
        "files_uploaded": len(uploaded_files),
        "details": uploaded_files,
        "message": "Files uploaded successfully. Next step: call /api/process to analyze."
    }