import pymupdf
from PIL import Image
import io
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

from backend.document_processor.text_extractor import extract_text_from_pdf, extract_text_with_ocr, get_tables_from_pdf, normalize_text

def process_pdf(file_path: str) -> Dict[str, Any]:
    """Processes a PDF file, extracting text, images (for OCR), and tables."""
    logger.info(f"Starting PDF processing for: {file_path}")
    full_text = []
    images_content = [] # Store OCR results from images within PDF
    tables_content = []
    
    document = pymupdf.open(file_path)
    for page_num in range(document.page_count):
        page = document.load_page(page_num)
        
        # 1. Extract text directly
        page_text = page.get_text("text")
        if page_text.strip():
            full_text.append(f"<page_start page=\"{page_num+1}\">\n" + normalize_text(page_text) + f"\n<page_end page=\"{page_num+1}\">")
        else:
            logger.info(f"Page {page_num+1} is empty or primarily image-based, attempting OCR.")
            # If no text, assume it's a scanned page and try OCR
            pix = page.get_pixmap()
            img_bytes = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_bytes))
            
            # Save image temporarily for OCR, or pass bytes if EasyOCR supports
            temp_image_path = f"temp_page_{page_num}.png"
            image.save(temp_image_path)
            ocr_text = extract_text_with_ocr(temp_image_path)
            if ocr_text:
                images_content.append({"page": page_num + 1, "content": normalize_text(ocr_text)})
                full_text.append(f"<page_start page=\"{page_num+1}\" ocr=\"true\">\n" + normalize_text(ocr_text) + f"\n<page_end page=\"{page_num+1}\">")
            os.remove(temp_image_path) # Clean up temp image

        # 2. Extract tables (simplified for now)
        page_tables = get_tables_from_pdf(file_path) # get_tables_from_pdf can be modified to take page object
        for table in page_tables:
            if table['page'] == page_num + 1: # Filter tables for current page
                tables_content.append(table)

    # Combine all extracted content
    combined_content = { 
        "text": "\n".join(full_text),
        "tables": tables_content,
        "images_ocr": images_content
    }
    logger.info(f"Finished PDF processing for: {file_path}. Extracted {len(full_text)} text blocks, {len(tables_content)} tables, {len(images_content)} OCR images.")
    return combined_content
