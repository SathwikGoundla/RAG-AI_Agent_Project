import docx
import pymupdf
from PIL import Image
import easyocr
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Initialize EasyOCR reader lazily (only when first needed)
_reader = None

def get_ocr_reader():
    """Get or initialize the EasyOCR reader (lazy initialization)."""
    global _reader
    if _reader is None:
        try:
            _reader = easyocr.Reader(['en', 'te'], gpu=True)  # English and Telugu
            logger.info("EasyOCR reader initialized with English and Telugu languages (GPU enabled if available).")
        except Exception as e:
            logger.warning(f"Failed to initialize EasyOCR with GPU, trying CPU: {e}")
            try:
                _reader = easyocr.Reader(['en', 'te'], gpu=False)  # Fallback to CPU
                logger.info("EasyOCR reader initialized with English and Telugu languages (CPU enabled).")
            except Exception as e2:
                logger.error(f"Failed to initialize EasyOCR reader: {e2}")
                _reader = None
    return _reader

def extract_text_from_txt(file_path: str) -> str:
    """Extracts text from a .txt file."""
    logger.info(f"Extracting text from TXT: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def extract_text_from_docx(file_path: str) -> str:
    """Extracts text from a .docx file."""
    logger.info(f"Extracting text from DOCX: {file_path}")
    document = docx.Document(file_path)
    full_text = []
    for para in document.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts text from a PDF file using PyMuPDF."""
    logger.info(f"Extracting text from PDF: {file_path}")
    document = pymupdf.open(file_path)
    text = ""
    for page_num in range(document.page_count):
        page = document.load_page(page_num)
        text += page.get_text()
    return text

def extract_text_with_ocr(image_path: str) -> str:
    """Extracts text from an image file using OCR."""
    logger.info(f"Performing OCR on image: {image_path}")
    try:
        reader = get_ocr_reader()
        if reader is None:
            logger.warning(f"OCR reader not available for {image_path}")
            return ""
        # EasyOCR returns a list of detected text bounding boxes and their text
        results = reader.readtext(image_path)
        ocr_text = " ".join([res[1] for res in results])
        logger.info(f"OCR successful for {image_path}, extracted {len(ocr_text)} characters.")
        return ocr_text
    except Exception as e:
        logger.error(f"OCR failed for {image_path}: {e}")
        return ""

def get_tables_from_pdf(file_path: str) -> List[Dict[str, Any]]:
    """Extracts tables from a PDF file using PyMuPDF (simplified - usually more complex parsing is needed)."""
    logger.info(f"Attempting to extract tables from PDF: {file_path} (simplified approach).")
    document = pymupdf.open(file_path)
    tables_data = []
    for page_num in range(document.page_count):
        page = document.load_page(page_num)
        # PyMuPDF has limited direct table extraction. This is a placeholder.
        # Advanced table extraction usually requires libraries like Camelot or Tabula-py.
        # For simplicity, we'll just try to get blocks that look like tables.
        blocks = page.get_text("blocks") # get all text blocks
        for block in blocks:
            # Heuristic: if a block has many tabs or spaces, it might be a table
            if "\t" in block[4] or "  " * 4 in block[4]: # block[4] is the text content
                # For a real implementation, you'd use more sophisticated table parsing
                tables_data.append({"page": page_num + 1, "content": block[4], "bbox": block[:4]})
    logger.info(f"Extracted {len(tables_data)} potential table blocks from PDF {file_path}.")
    return tables_data

def normalize_text(text: str) -> str:
    """Normalizes and cleans extracted text."""
    # Remove excessive whitespace, replace newlines with spaces or single newlines based on context
    text = os.linesep.join([s for s in text.splitlines() if s]) # Remove empty lines
    text = " ".join(text.split()) # Replace multiple spaces with single space
    logger.debug("Text normalized.")
    return text
