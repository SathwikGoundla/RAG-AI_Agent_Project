import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from typing import List
import os

logger = logging.getLogger(__name__)

from backend.auth.security import get_current_active_user
from backend.models import UserOut, DocumentMetadata
from backend.document_processor.services import DocumentProcessorService, get_document_processor_service
from backend.rag_engine.vector_store import ChromaDBManager, get_chroma_manager

router = APIRouter()

@router.post("/upload", response_model=DocumentMetadata, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload (PDF, DOCX, TXT, JPG, PNG)"),
    current_user: UserOut = Depends(get_current_active_user),
    doc_service: DocumentProcessorService = Depends(get_document_processor_service)
):
    """Uploads and processes a document for the current user."""
    logger.info(f"User {current_user.username} is uploading document: {file.filename}")
    allowed_extensions = ["pdf", "docx", "txt", "jpg", "jpeg", "png"]
    file_extension = file.filename.split(".")[-1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.filename}. Allowed types are {', '.join(allowed_extensions)}."
        )
    
    try:
        document_metadata = await doc_service.ingest_document(file, current_user.id)
        logger.info(f"Document {file.filename} (ID: {document_metadata.id}) uploaded and processed successfully for user {current_user.username}.")
        return document_metadata
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error uploading document {file.filename} for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process document: {e}")

@router.get("/user_documents", response_model=List[DocumentMetadata])
async def get_user_documents(
    current_user: UserOut = Depends(get_current_active_user),
    chroma_manager: ChromaDBManager = Depends(get_chroma_manager)
):
    """Retrieves a list of all documents uploaded by the current user."""
    logger.info(f"Fetching documents for user: {current_user.username}")
    user_collection_name = f"user_{current_user.id}_documents"
    try:
        collection = chroma_manager.get_collection(user_collection_name)
        # In ChromaDB, metadata is stored per chunk. We need to aggregate document metadata.
        # This approach assumes document_id is consistent across all chunks of a document.
        # Use where filter AND limit, but NOT empty ids list
        results = collection.get(
            where={"user_id": str(current_user.id)},
            limit=1000
        )

        documents_info = {}
        for metadata in results.get("metadatas", []):
            doc_id = metadata.get("document_id")
            if doc_id and doc_id not in documents_info:
                documents_info[doc_id] = DocumentMetadata(
                    id=doc_id,
                    user_id=current_user.id,
                    filename=metadata.get("filename", "unknown"),
                    file_path="", # Path might not be stored directly in chunk metadata, or reconstruct it
                    file_type=metadata.get("filename", "").split(".")[-1].lower() if metadata.get("filename") else "unknown",
                    # text_content_summary will need to be retrieved or handled differently
                )
        # A more robust solution would involve a separate metadata store (e.g., SQL DB) for documents
        # For now, we are reconstructing limited metadata from chunk metadata.
        # To get actual file_path and text_content_summary, we might need another DB lookup or infer from filename.
        
        logger.info(f"Retrieved {len(documents_info)} documents for user {current_user.username}.")
        return list(documents_info.values())
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND: # Collection not found means no documents yet
            return []
        raise e
    except Exception as e:
        logger.error(f"Error retrieving documents for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve documents: {e}")

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: UserOut = Depends(get_current_active_user),
    chroma_manager: ChromaDBManager = Depends(get_chroma_manager)
):
    """Deletes a document and its associated chunks from the system."""
    logger.info(f"User {current_user.username} attempting to delete document: {document_id}")
    user_collection_name = f"user_{current_user.id}_documents"
    try:
        collection = chroma_manager.get_collection(user_collection_name)
        
        # Find all chunks belonging to this document and user
        results = collection.get(where={
            "document_id": document_id,
            "user_id": str(current_user.id)
        })
        chunk_ids_to_delete = results.get("ids", [])
        
        if not chunk_ids_to_delete:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found or unauthorized to delete.")

        # Delete chunks from ChromaDB
        collection.delete(ids=chunk_ids_to_delete)
        logger.info(f"Deleted {len(chunk_ids_to_delete)} chunks for document {document_id} from ChromaDB.")

        # Also delete the physical file from storage
        # This requires retrieving the original file path. Currently, DocumentMetadata is not persisted.
        # A separate document metadata database (e.g., SQL) would be ideal here.
        # For now, we'll skip physical file deletion or assume it's handled externally/manually.
        # In a real app, you'd fetch DocumentMetadata from a persistent store, get its file_path, and delete.
        # Example (if metadata was stored): 
        # doc_meta = get_document_metadata_from_db(document_id, current_user.id)
        # if doc_meta and os.path.exists(doc_meta.file_path): os.remove(doc_meta.file_path)
        logger.warning(f"Physical file deletion for document {document_id} skipped. Needs persistent metadata storage.")

        return {"message": "Document and its chunks deleted successfully."}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error deleting document {document_id} for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete document: {e}")
