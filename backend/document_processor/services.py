import os
import uuid
import logging
from typing import Dict, Any, List
from fastapi import UploadFile, HTTPException, status, Depends

logger = logging.getLogger(__name__)

from backend.config import settings
from backend.models import DocumentMetadata, ChunkMetadata
from backend.document_processor.text_extractor import extract_text_from_docx, extract_text_from_txt, normalize_text
from backend.document_processor.pdf_processor import process_pdf
from backend.document_processor.image_processor import process_image
from backend.document_processor.chunker import chunk_document_content
from backend.rag_engine.vector_store import ChromaDBManager, get_chroma_manager

class DocumentProcessorService:
    def __init__(self, chroma_manager: ChromaDBManager = get_chroma_manager()):
        self.chroma_manager = chroma_manager
        self.document_storage_path = settings.STORAGE_DOCUMENTS_PATH
        os.makedirs(self.document_storage_path, exist_ok=True)
        logger.info(f"DocumentProcessorService initialized. Storage path: {self.document_storage_path}")

    async def save_document_file(self, file: UploadFile, user_id: str) -> str:
        """Saves the uploaded file to disk and returns its path."""
        file_extension = file.filename.split(".")[-1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        user_dir = os.path.join(self.document_storage_path, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        file_location = os.path.join(user_dir, unique_filename)
        
        with open(file_location, "wb") as f:
            f.write(await file.read())
        logger.info(f"File saved: {file_location} for user {user_id}")
        return file_location

    def process_document_content(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Processes the document based on its type to extract content."""
        logger.info(f"Processing document content: {file_path} (Type: {file_type})")
        processed_content = {"text": "", "tables": [], "images_ocr": []}

        if file_type == "pdf":
            processed_content = process_pdf(file_path)
        elif file_type == "docx":
            text = extract_text_from_docx(file_path)
            processed_content["text"] = normalize_text(text)
        elif file_type == "txt":
            text = extract_text_from_txt(file_path)
            processed_content["text"] = normalize_text(text)
        elif file_type in ["jpg", "jpeg", "png"]:
            processed_content = process_image(file_path)
        else:
            logger.error(f"Unsupported file type: {file_type} for file {file_path}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported file type: {file_type}")
        
        logger.info(f"Document content processed for {file_path}.")
        return processed_content

    async def ingest_document(self, file: UploadFile, user_id: str) -> DocumentMetadata:
        """Handles the full ingestion pipeline: save, process, chunk, and store embeddings."""
        document_id = str(uuid.uuid4())
        user_id = str(user_id)  # Ensure user_id is string
        file_extension = file.filename.split(".")[-1].lower()
        
        # 1. Save document file
        file_location = await self.save_document_file(file, user_id)
        
        # 2. Process document content
        processed_content = self.process_document_content(file_location, file_extension)
        logger.info(f"Processed content text length: {len(processed_content.get('text', ''))}")

        # 3. Chunk the content
        chunks_data = chunk_document_content(processed_content)
        logger.info(f"Generated {len(chunks_data)} chunks from document")

        # Prepare for ChromaDB
        documents_to_store = []
        metadatas_to_store = []
        ids_to_store = []

        for chunk in chunks_data:
            try:
                # Ensure all chunk_id components are strings
                chunk_id_str = str(chunk.get('chunk_id', 'unknown'))
                chunk_id = f"{document_id}_{chunk_id_str}"
                
                chunk_content = chunk.get("content", "").strip()
                if not chunk_content:
                    logger.warning(f"Skipping empty chunk: {chunk_id}")
                    continue
                
                documents_to_store.append(chunk_content)
                
                # Build metadata with NO None values (ChromaDB strict validation)
                metadata = {
                    "document_id": str(document_id),
                    "user_id": str(user_id),
                    "filename": str(file.filename),
                    "chunk_id": chunk_id_str,
                    "chunk_type": str(chunk.get("type", "text")),
                }
                
                # Only add page_number if it's a valid integer
                page_num = chunk.get("page_number")
                if page_num is not None:
                    try:
                        metadata["page_number"] = int(page_num)
                    except (ValueError, TypeError):
                        pass  # Skip invalid page numbers
                
                metadatas_to_store.append(metadata)
                ids_to_store.append(chunk_id)
            except Exception as chunk_err:
                logger.error(f"Error processing chunk: {chunk_err}")
                continue

        # 4. Store embeddings in ChromaDB (using a per-user collection for isolation)
        if len(ids_to_store) > 0:
            user_collection_name = f"user_{user_id}_documents"
            user_collection = self.chroma_manager.get_or_create_collection(user_collection_name)
            user_collection.add(documents=documents_to_store, metadatas=metadatas_to_store, ids=ids_to_store)
            logger.info(f"Ingested {len(ids_to_store)} chunks into ChromaDB for document {document_id} (user: {user_id}).")
        else:
            logger.error(f"No valid chunks to store for document {document_id}. Generated {len(chunks_data)} chunks total.")

        # Create and return DocumentMetadata
        doc_metadata = DocumentMetadata(
            id=document_id,
            user_id=user_id,
            filename=file.filename,
            file_path=file_location,
            file_type=file_extension,
            text_content_summary=processed_content["text"][:200] + "..." if processed_content["text"] else ""
        )
        return doc_metadata

def get_document_processor_service(chroma_manager: ChromaDBManager = Depends(get_chroma_manager)):
    return DocumentProcessorService(chroma_manager)
