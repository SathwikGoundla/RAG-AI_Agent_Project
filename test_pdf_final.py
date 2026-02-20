"""
Test PDF extraction using an existing sample PDF
"""

import requests
import json
import os
import sys
import uuid

BACKEND_URL = "http://localhost:8000"
pdf_file = "sample_test.pdf"

# Check if PDF exists
if not os.path.exists(pdf_file):
    print("[ERROR] Sample PDF not found: " + pdf_file)
    sys.exit(1)

# Register test user
print("\nSTEP 1: Registering test user...")
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
    print("[ERROR] Registration failed: " + str(register_response.json()))
    sys.exit(1)

# Login
print("STEP 2: Logging in...")
login_response = requests.post(
    f"{BACKEND_URL}/api/v1/auth/login",
    json={"username": test_email, "password": test_password},
    timeout=10
)

if login_response.status_code != 200:
    print("[ERROR] Login failed: " + str(login_response.json()))
    sys.exit(1)

token = login_response.json()['access_token']
print("[OK] Authenticated")

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

print("Upload Status: " + str(upload_response.status_code))

if upload_response.status_code != 201:
    print("[ERROR] Upload failed: " + str(upload_response.json()))
    sys.exit(1)

upload_data = upload_response.json()
print("[OK] Upload successful")
print("Upload Data:")
print(json.dumps(upload_data, indent=2))

# Test 1: Check text extraction
text_summary = upload_data.get('text_content_summary', '')
print("\nTEST 1 - Text Extraction:")
if text_summary and text_summary.strip():
    print("[OK] Text extracted: " + text_summary[:100])
else:
    print("[ERROR] NO TEXT EXTRACTED FROM PDF")

# Test 2: Fetch documents
print("\nTEST 2 - Document Listing:")
doc_response = requests.get(
    f"{BACKEND_URL}/api/v1/documents/user_documents",
    headers=headers,
    timeout=10
)

if doc_response.status_code == 200:
    documents = doc_response.json()
    if len(documents) > 0:
        print("[OK] Document listed: " + str(len(documents)) + " document(s)")
        for doc in documents:
            print("   - " + doc.get('filename'))
    else:
        print("[ERROR] NO DOCUMENTS FOUND (should have 1)")
else:
    print("[ERROR] Failed to list documents: " + str(doc_response.json()))

# Test 3: Query the document
print("\nTEST 3 - Document Query:")
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
        print("[OK] Query response received")
        print("   Response: " + response_text[:150])
        print("   Sources found: " + str(len(sources)))
    else:
        print("[WARNING] Empty response from query")
else:
    print("Query error: " + str(query_response.json()))
