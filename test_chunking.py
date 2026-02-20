import sys
import os
sys.path.insert(0, 'c:\\Users\\Sathwik\\advanced-rag-system')

from backend.document_processor.chunker import chunk_document_content, chunk_text
import json

# Test with the same format as PDF processor
test_content = {
    "text": "<page_start page=\"1\">\nTEST PDF DOCUMENT This is a test PDF file for extraction testing. It contains multiple lines of text. PDF text extraction should work on this document. The system will extract and index this content.\n<page_end page=\"1\">",
    "tables": [],
    "images_ocr": []
}

print("Test content:")
print(test_content["text"][:100])
print("\nChunking...")

chunks = chunk_document_content(test_content)

print(f"\nChunks generated: {len(chunks)}")
print("\nFull chunk objects:")
print(json.dumps([{k:v for k,v in c.items() if k != 'content'} for c in chunks], indent=2))

for i, chunk in enumerate(chunks):
    print(f"\n[CHUNK {i}]")
    print(f"  Keys: {list(chunk.keys())}")
    print(f"  Page: {chunk.get('page_number')}")
    print(f"  Type: {chunk.get('type')}")
    print(f"  Chunk ID: {chunk.get('chunk_id')}")
    content = chunk.get('content', '')
    print(f"  Content Length: {len(content)}")
    print(f"  Content Empty: {not content or not content.strip()}")
    print(f"  Content Preview: {content[:60]}")
