#!/usr/bin/env python
"""
Detailed circular import investigation
"""
import sys
import traceback

print("\n" + "="*80)
print("CIRCULAR IMPORT INVESTIGATION")
print("="*80 + "\n")

# Test individual module imports
print("[TEST 1] Import vector_store directly")
try:
    import backend.rag_engine.vector_store
    print("[PASS] vector_store imported successfully")
except Exception as e:
    print(f"[FAIL] Error: {e}")
    traceback.print_exc()

print("\n[TEST 2] Import embeddings module")
try:
    import backend.rag_engine.embeddings
    print("[PASS] embeddings imported successfully")
except Exception as e:
    print(f"[FAIL] Error: {e}")
    traceback.print_exc()

print("\n[TEST 3] Try to import EmbeddingService from embeddings")
try:
    from backend.rag_engine.embeddings import EmbeddingService
    print("[PASS] EmbeddingService imported successfully")
except Exception as e:
    print(f"[FAIL] Error: {e}")
    print(f"Available attributes in embeddings: {dir(backend.rag_engine.embeddings)}")

print("\n[TEST 4] Import retriever module")
try:
    import backend.rag_engine.retriever
    print("[PASS] retriever imported successfully")
except Exception as e:
    print(f"[FAIL] Error: {e}")
    traceback.print_exc()

print("\n[TEST 5] Try to import RetrieverService from retriever")
try:
    from backend.rag_engine.retriever import RetrieverService
    print("[PASS] RetrieverService imported successfully")
except Exception as e:
    print(f"[FAIL] Error: {e}")
    print(f"Available attributes in retriever: {dir(backend.rag_engine.retriever)}")

print("\n[TEST 6] Import router module")
try:
    import backend.rag_engine.router
    print("[PASS] router imported successfully")
except Exception as e:
    print(f"[FAIL] Error: {e}")
    traceback.print_exc()

print("\n" + "="*80)
