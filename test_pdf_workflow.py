"""
Test PDF upload, extraction, and document retrieval
"""

import requests
import json
import os
import sys

# Create a test PDF
def create_test_pdf():
    """Create a simple test PDF"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        test_pdf_path = "test_pdf_upload.pdf"
        c = canvas.Canvas(test_pdf_path, pagesize=letter)
        c.drawString(100, 750, "=" * 50)
        c.drawString(100, 730, "TEST DOCUMENT FOR PDF EXTRACTION")
        c.drawString(100, 710, "=" * 50)
        c.drawString(100, 690, " ")
        c.drawString(100, 670, "This is a test PDF document.")
        c.drawString(100, 650, "It contains multiple lines of text.")
        c.drawString(100, 630, "The system should extract and index this content.")
        c.drawString(100, 610, " ")
        c.drawString(100, 590, "Key features to test:")
        c.drawString(100, 570, "1. Text extraction from PDF")
        c.drawString(100, 550, "2. Text chunking into smaller pieces")
        c.drawString(100, 530, "3. Embedding generation")
        c.drawString(100, 510, "4. Storage in vector database")
        c.drawString(100, 490, "5. Retrieval when querying")
        c.showPage()
        c.save()
        
        return test_pdf_path
    except ImportError:
        print("❌ reportlab not installed. Install it with: pip install reportlab")
        return None

def test_pdf_workflow():
    """Test complete PDF upload and retrieval workflow"""
    print("\n" + "="*70)
    print("PDF UPLOAD & EXTRACTION TEST")
    print("="*70)
    
    BACKEND_URL = "http://localhost:8000"
    
    # Step 1: Register and login to get token
    print("\nSTEP 1: Registering and authenticating...")
    
    # Unique user for this test
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    test_username = f"pdftest_{unique_id}"
    test_email = f"pdf_{unique_id}@test.com"
    test_password = "PDFTest123!"
    
    # Register first
    register_response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/register",
        json={
            "username": test_username,
            "email": test_email,
            "password": test_password,
            "full_name": "PDF Test User"
        },
        timeout=10
    )
    
    if register_response.status_code != 201:
        print(f"❌ Registration failed: {register_response.json()}")
        return False
    
    # Login
    login_response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        json={"username": test_email, "password": test_password},
        timeout=10
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.json()}")
        return False
    
    token = login_response.json()['access_token']
    print(f"✅ Registered and authenticated as {test_username}")
    
    # Step 2: Create test PDF
    print("\nSTEP 2: Creating test PDF...")
    pdf_path = create_test_pdf()
    
    if not pdf_path:
        return False
    
    print(f"✅ Test PDF created: {pdf_path}")
    
    # Step 3: Upload PDF
    print("\nSTEP 3: Uploading PDF...")
    headers = {'Authorization': f'Bearer {token}'}
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (pdf_path, f, 'application/pdf')}
        upload_response = requests.post(
            f"{BACKEND_URL}/api/v1/documents/upload",
            files=files,
            headers=headers,
            timeout=30
        )
    
    print(f"Upload Status: {upload_response.status_code}")
    
    if upload_response.status_code != 201:
        print(f"❌ Upload failed: {upload_response.json()}")
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        return False
    
    upload_data = upload_response.json()
    print(f"✅ Upload successful")
    print(f"   Document ID: {upload_data.get('id')}")
    print(f"   Filename: {upload_data.get('filename')}")
    print(f"   File Type: {upload_data.get('file_type')}")
    
    # Check if text was extracted
    text_summary = upload_data.get('text_content_summary', '')
    print(f"\n   Text Summary: {text_summary}")
    
    if not text_summary or text_summary.strip() == '':
        print("❌ WARNING: No text extracted from PDF!")
    else:
        print("✅ Text was extracted from PDF")
    
    # Step 4: Fetch user documents
    print("\nSTEP 4: Fetching uploaded documents...")
    doc_response = requests.get(
        f"{BACKEND_URL}/api/v1/documents/user_documents",
        headers=headers,
        timeout=10
    )
    
    print(f"Response Status: {doc_response.status_code}")
    
    if doc_response.status_code == 200:
        documents = doc_response.json()
        print(f"✅ Documents retrieved: {len(documents)}")
        
        for doc in documents:
            print(f"\n   Document: {doc.get('filename')}")
            print(f"   - File Type: {doc.get('file_type')}")
            print(f"   - Text Summary: {doc.get('text_content_summary', '')[:100]}")
    else:
        print(f"❌ Failed to retrieve documents: {doc_response.json()}")
    
    # Step 5: Test RAG Query
    print("\nSTEP 5: Testing RAG Query on uploaded document...")
    query_response = requests.post(
        f"{BACKEND_URL}/api/v1/rag/query",
        json={"question": "What is in this document?"},
        headers=headers,
        timeout=30
    )
    
    print(f"Query Status: {query_response.status_code}")
    
    if query_response.status_code == 200:
        query_data = query_response.json()
        print(f"✅ Query successful")
        print(f"   Response: {query_data.get('response', '')[:200]}...")
        print(f"   Sources: {len(query_data.get('sources', []))} documents")
    else:
        print(f"Query response: {query_response.json()}")
    
    # Cleanup
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    
    return True

if __name__ == "__main__":
    test_pdf_workflow()
