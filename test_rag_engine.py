#!/usr/bin/env python
"""
Comprehensive RAG engine and vector store diagnostics
"""
import sys
import os
import json

print("\n" + "="*80)
print("RAG ENGINE DIAGNOSTICS")
print("="*80 + "\n")

# Test 1: Vector Store Initialization
print("[TEST 1] Vector Store Initialization")
try:
    from backend.rag_engine.vector_store import VectorStore
    vs = VectorStore()
    stats = vs.get_collection_stats()
    print(f"[PASS] Vector Store initialized")
    print(f"Stats: {stats}\n")
except Exception as e:
    print(f"[FAIL] Error: {e}\n")

# Test 2: Embeddings Generator
print("[TEST 2] Embeddings Generator")
try:
    from backend.rag_engine.embeddings import EmbeddingGenerator
    gen = EmbeddingGenerator()
    
    # Test single embedding
    query_emb = gen.generate("Test query")
    print(f"[PASS] Generated single embedding: shape {query_emb.shape}")
    
    # Test batch embedding
    texts = ["Document 1", "Document 2", "Document 3"]
    batch_embs = gen.generate_batch(texts)
    print(f"[PASS] Generated batch embeddings: shape {batch_embs.shape}\n")
except Exception as e:
    print(f"[FAIL] Error: {e}\n")

# Test 3: Retriever
print("[TEST 3] Retriever")
try:
    from backend.rag_engine.retriever import Retriever
    retriever = Retriever()
    
    # Test retrieval (even if no documents, should not crash)
    results = retriever.retrieve(
        "What is RAG?",
        user_id="test_user",
        n_results=5,
        similarity_threshold=0.3
    )
    print(f"[PASS] Retriever working, returned {len(results)} results\n")
except Exception as e:
    print(f"[FAIL] Error: {e}\n")

# Test 4: Response Generator
print("[TEST 4] Response Generator (OpenAI)")
try:
    from backend.rag_engine.generator import ResponseGenerator
    from backend.config import settings
    
    if not settings.OPENAI_API_KEY:
        print("[WARN] OPENAI_API_KEY not set in environment")
    else:
        gen = ResponseGenerator()
        # Just test initialization, don't actually make API calls
        print(f"[PASS] Response Generator initialized\n")
except Exception as e:
    print(f"[FAIL] Error: {e}\n")

# Test 5: Document Processor (Text Extractor)
print("[TEST 5] Document Processor - Text Extractor")
try:
    from backend.document_processor.text_extractor import TextExtractor
    extractor = TextExtractor()
    
    # Test on a dummy text file
    test_file = "c:\\Users\\Sathwik\\advanced-rag-system\\backend\\main.py"
    if os.path.exists(test_file):
        text = extractor.extract_from_file(test_file)
        print(f"[PASS] Text extraction working, extracted {len(text)} chars\n")
    else:
        print(f"[INFO] Test file not found\n")
except Exception as e:
    print(f"[FAIL] Error: {e}\n")

# Test 6: Text Chunker
print("[TEST 6] Text Chunker")
try:
    from backend.document_processor.chunker import TextChunker
    
    sample_text = "This is a test. This is another sentence. And here is a third one. " * 100
    
    # Test sentence-based chunking
    chunks = TextChunker.chunk_by_sentences(sample_text, sentences_per_chunk=3)
    print(f"[PASS] Sentence chunking: created {len(chunks)} chunks")
    
    # Test word-based chunking
    chunks = TextChunker.chunk_by_words(sample_text, chunk_size=500, overlap=50)
    print(f"[PASS] Word chunking: created {len(chunks)} chunks\n")
except Exception as e:
    print(f"[FAIL] Error: {e}\n")

# Test 7: Database
print("[TEST 7] Database - User Operations")
try:
    from backend.database import SessionLocal, Base
    from sqlalchemy import inspect
    
    db = SessionLocal()
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()
    
    print(f"[PASS] Database connected")
    print(f"Tables found: {tables}\n")
    db.close()
except Exception as e:
    print(f"[FAIL] Error: {e}\n")

# Test 8: Storage directories
print("[TEST 8] Storage Directories")
try:
    from backend.config import settings
    
    dirs_to_check = [
        settings.UPLOAD_DIR,
        settings.CACHE_DIR,
        settings.LOG_DIR,
        settings.VECTOR_DB_PATH,
    ]
    
    for dir_path in dirs_to_check:
        exists = os.path.exists(dir_path)
        status = "[OK]" if exists else "[MISSING]"
        print(f"{status} {dir_path}")
    print()
except Exception as e:
    print(f"[FAIL] Error: {e}\n")

# Test 9: Environment variables
print("[TEST 9] Configuration Load")
try:
    from backend.config import settings
    
    print(f"[INFO] API Version: {settings.API_V1_STR}")
    print(f"[INFO] Host: {settings.HOST}")
    print(f"[INFO] Port: {settings.PORT}")
    print(f"[INFO] Project: {settings.PROJECT_NAME}")
    print(f"[INFO] OpenAI API configured: {bool(settings.OPENAI_API_KEY)}")
    print(f"[INFO] Frontend URL: {settings.FRONTEND_URL}")
    print(f"[INFO] Chunk size: {settings.CHUNK_SIZE}")
    print(f"[INFO] Top K results: {settings.TOP_K_RESULTS}\n")
except Exception as e:
    print(f"[FAIL] Error: {e}\n")

# Test 10: Middleware
print("[TEST 10] Middleware Configuration")
try:
    from backend.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
    print(f"[PASS] RequestLoggingMiddleware: OK")
    print(f"[PASS] SecurityHeadersMiddleware: OK\n")
except Exception as e:
    print(f"[FAIL] Error: {e}\n")

print("="*80)
print("DIAGNOSTICS COMPLETE")
print("="*80)
