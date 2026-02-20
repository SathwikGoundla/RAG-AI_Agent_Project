"""
Test PDF extraction using an existing sample PDF
"""

import requests
import json
import os
import sys

# Disable Unicode emoji printing on Windows
def print_success(msg):
    print("[OK] " + msg)

def print_error(msg):
    print("[ERROR] " + msg)

def print_warning(msg):
    print("[WARNING] " + msg)

def test_pdf_extraction_simple():
    """Test PDF extraction with existing sample file"""
    print("\n" + "="*70)
    print("PDF EXTRACTION TEST (Simple)")
    print("="*70)
    
    BACKEND_URL = "http://localhost:8000"
    pdf_file = "sample_test.pdf"
    
    # Check if PDF exists
    if not os.path.exists(pdf_file):
        print(f"❌ Sample PDF not found: {pdf_file}")
        return False
    
    # Register test user
    print("\nSTEP 1: Registering test user...")
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    test_username = f"pdftest_{unique_id}"
    test_email = f"pdf_{unique_id}@test.com"
    test_password = "PDFTest123!"
    
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
    print("STEP 2: Logging in...")
    login_response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        json={"username": test_email, "password": test_password},
        timeout=10
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.json()}")
        return False
    
    token = login_response.json()['access_token']
    print(f"✅ Authenticated")
    
    # Upload PDF
    print("\nSTEP 3: Uploading PDF...")
    headers = {'Authorization': f'Bearer {token}'}
    
    with open(pdf_file, 'rb') as f:
        files = {'file': (pdf_file, f, 'application/pdf')}
        upload_response = requests.post(
            f"{BACKEND_URL}/api/v1/documents/upload",
            files=files,
            headers=headers,
            timeout=30
        )
    
    print(f"Upload Status: {upload_response.status_code}")
    
    if upload_response.status_code !=201:
        print(f"❌ Upload failed: {upload_response.json()}")
        return False
    
    upload_data = upload_response.json()
    print(f"✅ Upload successful")
    print(json.dumps(upload_data, indent=2))
    
    # Test 1: Check text extraction
    text_summary = upload_data.get('text_content_summary', '')
    print(f"\nTEST 1 - Text Extraction:")
    if text_summary and text_summary.strip():
        print(f"✅ Text extracted: {text_summary[:100]}...")
    else:
        print(f"❌ NO TEXT EXTRACTED FROM PDF")
    
    # Test 2: Fetch documents
    print(f"\nTEST 2 - Document Listing:")
    doc_response = requests.get(
        f"{BACKEND_URL}/api/v1/documents/user_documents",
        headers=headers,
        timeout=10
    )
    
    if doc_response.status_code == 200:
        documents = doc_response.json()
        if len(documents) > 0:
            print(f"✅ Document listed: {len(documents)} document(s)")
            for doc in documents:
                print(f"   - {doc.get('filename')}")
        else:
            print(f"❌ NO DOCUMENTS FOUND (should have 1)")
    else:
        print(f"❌ Failed to list documents: {doc_response.json()}")
    
    # Test 3: Query the document
    print(f"\nTEST 3 - Document Query:")
    query_response = requests.post(
        f"{BACKEND_URL}/api/v1/rag/query",
        json={"question": "What is in this PDF?"},
        headers=headers,
        timeout=30
    )
    
    if query_response.status_code == 200:
        query_data = query_response.json()
        response_text = query_data.get('response', '')
        sources = query_data.get('sources', [])
        
        if response_text.strip():
            print(f"✅ Query response received")
            print(f"   Response: {response_text[:150]}...")
            print(f"   Sources found: {len(sources)}")
        else:
            print(f"⚠️ Empty response from query")
    else:
        print(f"Query error: {query_response.json()}")
    
    return True

if __name__ == "__main__":
    test_pdf_extraction_simple()
