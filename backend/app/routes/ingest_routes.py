import os
import shutil

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.auth import get_current_user
from app.ingestion import KB_PATH, index_pdf


router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post("/upload")
def upload_pdf(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Save an uploaded PDF in the knowledge base and index it immediately."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    save_path = os.path.join(KB_PATH, file.filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    index_pdf(save_path)

    return {"message": f"{file.filename} uploaded and indexed successfully"}
