"""
extract_text.py
Extracts text from PDF files.
Handles both digital PDFs and scanned images.
"""
import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from PIL import Image
from loguru import logger
import io


def is_scanned_pdf(pdf_path: str, sample_pages: int = 3,
                   threshold: int = 30) -> bool:
    """
    Check if a PDF is scanned (image-based) or digital (text-based).
    Returns True if scanned, False if digital.
    """
    try:
        doc = fitz.open(pdf_path)
        pages_to_check = min(sample_pages, len(doc))
        total_chars = 0
        for i in range(pages_to_check):
            text = doc[i].get_text()
            total_chars += len(text.strip())
        doc.close()
        is_scanned = total_chars < threshold
        logger.info(f"PDF type: {'SCANNED' if is_scanned else 'DIGITAL'} "
                    f"(chars in first {pages_to_check} pages: {total_chars})")
        return is_scanned
    except Exception as e:
        logger.error(f"Error detecting PDF type: {e}")
        return False  # default: try digital extraction


def extract_digital_pdf(pdf_path: str) -> list:
    """
    Extract text from a digital (text-based) PDF.
    Returns list of page texts.
    """
    pages = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                pages.append(text)
                logger.debug(f"Page {i+1}: extracted {len(text)} chars")
    except Exception as e:
        logger.error(f"pdfplumber failed: {e}. Trying PyMuPDF...")
        # Fallback to PyMuPDF
        doc = fitz.open(pdf_path)
        for page in doc:
            pages.append(page.get_text())
        doc.close()
    
    logger.info(f"Extracted {len(pages)} pages from digital PDF")
    return pages


def extract_scanned_pdf(pdf_path: str, dpi: int = 300) -> list:
    """
    Extract text from a scanned PDF using OCR (Tesseract).
    Returns list of page texts.
    """
    pages = []
    try:
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc):
            logger.info(f"OCR processing page {i+1}/{len(doc)}...")
            
            # Render page to image
            mat = fitz.Matrix(dpi/72, dpi/72)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            
            # Run OCR
            text = pytesseract.image_to_string(img, lang="eng")
            pages.append(text)
            logger.debug(f"Page {i+1}: OCR extracted {len(text)} chars")
        
        doc.close()
    except Exception as e:
        logger.error(f"OCR failed: {e}")
    
    logger.info(f"OCR complete: {len(pages)} pages processed")
    return pages


def extract_pdf(pdf_path: str, force_ocr: bool = False) -> list:
    """
    Smart PDF extraction:
    - Auto-detects if PDF is scanned or digital
    - Uses appropriate method
    - Returns list of page text strings
    
    Usage:
        pages = extract_pdf("question_paper.pdf")
    """
    logger.info(f"Processing PDF: {pdf_path}")
    
    if force_ocr:
        logger.info("Force OCR mode enabled")
        return extract_scanned_pdf(pdf_path)
    
    if is_scanned_pdf(pdf_path):
        return extract_scanned_pdf(pdf_path)
    else:
        return extract_digital_pdf(pdf_path)
