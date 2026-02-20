import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[Dict[str, Any]]:
    """Splits a given text into smaller, overlapping chunks."""
    logger.info(f"Chunking text with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
    
    chunks = []
    if not text:
        return chunks

    # Split by paragraphs or sentences first to maintain semantic coherence
    # A more advanced approach would use NLP libraries for sentence segmentation
    paragraphs = text.split("\n\n") # Split by double newline for paragraphs
    current_chunk = []
    current_length = 0
    chunk_id_counter = 0

    for para in paragraphs:
        words = para.split()
        for word in words:
            current_chunk.append(word)
            current_length += len(word) + 1 # +1 for space

            if current_length >= chunk_size - chunk_overlap:
                # Create a chunk
                chunk_text_content = " ".join(current_chunk).strip()
                if chunk_text_content:
                    chunks.append({"chunk_id": str(chunk_id_counter), "content": chunk_text_content})
                    chunk_id_counter += 1
                
                # Prepare for next chunk with overlap
                overlap_words = current_chunk[max(0, len(current_chunk) - (chunk_overlap // 5)):] # Rough overlap based on word count
                current_chunk = list(overlap_words) # Start new chunk with overlap
                current_length = sum(len(w) + 1 for w in current_chunk)
    
    # Add any remaining text as a chunk
    if current_chunk:
        chunk_text_content = " ".join(current_chunk).strip()
        if chunk_text_content:
            chunks.append({"chunk_id": str(chunk_id_counter), "content": chunk_text_content})

    logger.info(f"Finished chunking. Generated {len(chunks)} chunks.")
    return chunks

def chunk_document_content(processed_content: Dict[str, Any], chunk_size: int = 500, chunk_overlap: int = 50) -> List[Dict[str, Any]]:
    """Takes processed multi-modal content and chunks it intelligently."""
    import re
    all_chunks = []
    document_text = processed_content.get("text", "")
    tables = processed_content.get("tables", [])
    images_ocr = processed_content.get("images_ocr", [])

    logger.info(f"Starting chunking. Document text length: {len(document_text)}")
    logger.info(f"Document text preview: {document_text[:200]}")

    # First, extract page info from the text and split by pages
    # This ensures we don't lose page information when chunking
    pages = []
    page_pattern = r"<page_start page=\"(\d+)\">(.*?)<page_end page=\"\d+\">"
    
    matches = list(re.finditer(page_pattern, document_text, re.DOTALL))
    logger.info(f"Found {len(matches)} pages using regex")
    
    for match in matches:
        page_num = int(match.group(1))
        page_content = match.group(2).strip()
        pages.append({"page_number": page_num, "content": page_content})
        logger.info(f"Extracted page {page_num} with {len(page_content)} characters")
    
    # If no page tags found, treat entire document as one page
    if not pages:
        logger.warning("No page tags found in document text. Treating entire content as page 1.")
        pages = [{"page_number": None, "content": document_text}]
    
    logger.info(f"Document contains {len(pages)} pages")
    
    # Chunk main text content by page, then within each page
    for page_info in pages:
        page_num = page_info.get("page_number")
        page_text = page_info.get("content", "")
        
        logger.info(f"Chunking page {page_num} with {len(page_text)} characters")
        
        # Chunk this page's text
        page_chunks = chunk_text(page_text, chunk_size, chunk_overlap)
        logger.info(f"Page {page_num} produced {len(page_chunks)} chunks")
        
        for chunk in page_chunks:
            chunk["type"] = "text"
            chunk["page_number"] = page_num  # Assign page number to chunk
            all_chunks.append(chunk)

    # Process tables as chunks (each table can be a chunk or further chunked if very large)
    for i, table in enumerate(tables):
        table_chunk_content = f"Table content from page {table.get('page', 'Unknown')}: {table.get('content', '')}"
        table_chunks = chunk_text(table_chunk_content, chunk_size, chunk_overlap) # Chunk table text if needed
        for j, t_chunk in enumerate(table_chunks):
            t_chunk["chunk_id"] = f"table_{i}_{j}"
            t_chunk["type"] = "table"
            t_chunk["page_number"] = table.get("page") # Can be None
            all_chunks.append(t_chunk)

    # Process OCR content as chunks
    for i, img_ocr in enumerate(images_ocr):
        ocr_chunk_content = f"OCR content from page {img_ocr.get('page', 'Unknown')}: {img_ocr.get('content', '')}"
        ocr_chunks = chunk_text(ocr_chunk_content, chunk_size, chunk_overlap) # Chunk OCR text if needed
        for j, o_chunk in enumerate(ocr_chunks):
            o_chunk["chunk_id"] = f"ocr_{i}_{j}"
            o_chunk["type"] = "image_ocr"
            o_chunk["page_number"] = img_ocr.get("page") # Can be None
            all_chunks.append(o_chunk)
    
    logger.info(f"Finished multi-modal document chunking. Total {len(all_chunks)} chunks generated.")
    return all_chunks
