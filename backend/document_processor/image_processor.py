from PIL import Image
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

from backend.document_processor.text_extractor import extract_text_with_ocr, normalize_text

def process_image(file_path: str) -> Dict[str, Any]:
    """Processes an image file, performing OCR to extract text."""
    logger.info(f"Starting image processing for: {file_path}")
    
    ocr_text = extract_text_with_ocr(file_path)
    
    processed_content = {
        "text": normalize_text(ocr_text) if ocr_text else "",
        "images_ocr": [{"content": normalize_text(ocr_text), "file_path": file_path}] if ocr_text else []
    }
    
    logger.info(f"Finished image processing for: {file_path}. Extracted {len(ocr_text)} characters via OCR.")
    return processed_content
