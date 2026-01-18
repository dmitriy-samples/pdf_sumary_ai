import logging
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS
from app.database import engine, get_db, Base
from app.models import Document
from app.services.pdf_parser import extract_text_from_pdf, PDFTooManyPagesError
from app.services.summarizer import summarize_text

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PDF Summary AI", version="1.0.0")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    """Render main page with upload form and history."""
    documents = db.query(Document).order_by(Document.created_at.desc()).limit(5).all()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "documents": documents
    })


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload PDF and generate summary."""
    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")

    # Save file
    unique_filename = f"{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / unique_filename
    filepath.write_bytes(content)

    try:
        # Extract text from PDF
        logger.info(f"Extracting text from: {file.filename}")
        text = extract_text_from_pdf(filepath)

        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")

        logger.info(f"Extracted {len(text)} characters, generating summary...")
        # Generate summary
        summary = await summarize_text(text)
        logger.info("Summary generated successfully")

        # Save to database
        document = Document(
            filename=file.filename,
            filepath=str(filepath),
            summary=summary
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        return {
            "id": document.id,
            "filename": document.filename,
            "summary": document.summary,
            "created_at": document.created_at.isoformat()
        }

    except PDFTooManyPagesError as e:
        filepath.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        filepath.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
async def get_history(db: Session = Depends(get_db)):
    """Get last 5 processed documents."""
    documents = db.query(Document).order_by(Document.created_at.desc()).limit(5).all()
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "summary": doc.summary,
            "created_at": doc.created_at.isoformat()
        }
        for doc in documents
    ]


@app.get("/document/{doc_id}")
async def get_document(doc_id: int, db: Session = Depends(get_db)):
    """Get specific document by ID."""
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": document.id,
        "filename": document.filename,
        "summary": document.summary,
        "created_at": document.created_at.isoformat()
    }
