"""PDF parsing and text extraction with OCR support."""

import logging
from pathlib import Path
import pymupdf
import pymupdf4llm

from app.config import MAX_PAGES

logger = logging.getLogger(__name__)

# Minimum text length to consider page has meaningful content
MIN_TEXT_PER_PAGE = 50


class PDFTooManyPagesError(Exception):
    """Raised when PDF exceeds maximum page limit."""
    pass


def get_page_count(filepath: str | Path) -> int:
    """Get the number of pages in a PDF file."""
    with pymupdf.open(str(filepath)) as doc:
        return len(doc)


def _extract_with_ocr(filepath: str | Path) -> str:
    """
    Extract text using OCR for scanned documents.

    Uses Tesseract OCR via PyMuPDF for pages with little/no text.
    """
    text_parts = []

    with pymupdf.open(str(filepath)) as doc:
        for page_num, page in enumerate(doc):
            # Try regular text extraction first
            text = page.get_text().strip()

            if len(text) < MIN_TEXT_PER_PAGE:
                # Page has little text — likely a scan, use OCR
                logger.info(f"Page {page_num + 1}: applying OCR (only {len(text)} chars found)")
                try:
                    tp = page.get_textpage_ocr(language="eng+rus", dpi=150)
                    text = page.get_text(textpage=tp).strip()
                    logger.info(f"Page {page_num + 1}: OCR extracted {len(text)} chars")
                except Exception as e:
                    logger.warning(f"Page {page_num + 1}: OCR failed: {e}")

            if text:
                text_parts.append(f"## Page {page_num + 1}\n\n{text}")

    return "\n\n".join(text_parts)


def extract_text_from_pdf(filepath: str | Path) -> str:
    """
    Extract text from PDF with OCR fallback for scanned pages.

    Strategy:
    1. Use pymupdf4llm for structured extraction (tables, formatting)
    2. If result has little text, fall back to OCR

    Raises:
        PDFTooManyPagesError: If PDF exceeds MAX_PAGES limit.
    """
    page_count = get_page_count(filepath)

    if page_count > MAX_PAGES:
        raise PDFTooManyPagesError(
            f"PDF has {page_count} pages, maximum allowed is {MAX_PAGES}"
        )

    # Primary extraction with pymupdf4llm (good for tables and structure)
    md_text = pymupdf4llm.to_markdown(str(filepath))

    # Check if we got meaningful content
    text_length = len(md_text.strip())
    expected_min = page_count * MIN_TEXT_PER_PAGE

    if text_length < expected_min:
        logger.info(
            f"Low text content ({text_length} chars for {page_count} pages), "
            f"trying OCR extraction"
        )
        ocr_text = _extract_with_ocr(filepath)

        # Use OCR result if it's better
        if len(ocr_text) > text_length:
            logger.info(f"Using OCR result ({len(ocr_text)} chars)")
            return ocr_text

    return md_text
