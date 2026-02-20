"""
Diagnostic script to identify and test the three critical issues:
1. Non-registered emails can login (security issue)
2. PDF text extraction not working
3. Document status shows "upload more" after upload
"""

import requests
import json
from typing import Tuple, Dict

BACKEND_URL = "http://localhost:8000"

def test_auth_security() -> Dict:
    """Test if non-registered email can login (SECURITY BUG)"""
    print("\n" + "="*60)
    print("TEST 1: AUTHENTICATION SECURITY")
    print("="*60)
    
    results = {}
    
    # Test 1a: Try logging in with unregistered email
    print("\n1a. Testing login with UNREGISTERED email...")
    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        json={"username": "nonexistent_test_user@example.com", "password": "password123"},
        timeout=5
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 401:
        results['unregistered_login_blocked'] = True
        print("✅ PASS: Unregistered email cannot login")
    else:
        results['unregistered_login_blocked'] = False
        print("❌ FAIL: Unregistered email can login! SECURITY BUG!")
    
    # Test 1b: Register a user and verify they can login
    print("\n1b. Testing registered user login...")
    
    # Register
    register_response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/register",
        json={
            "username": "testuser_secure",
            "email": "testuser_secure@example.com",
            "password": "SecurePass123",
            "full_name": "Test User Secure"
        },
        timeout=5
    )
    
    print(f"Register Status: {register_response.status_code}")
    
    if register_response.status_code == 201:
        # Try login with registered email
        login_response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"username": "testuser_secure@example.com", "password": "SecurePass123"},
            timeout=5
        )
        
        print(f"Login Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            results['registered_login_works'] = True
            print("✅ PASS: Registered user can login")
            results['token'] = login_response.json().get('access_token')
        else:
            results['registered_login_works'] = False
            print("❌ FAIL: Registered user cannot login")
    else:
        results['registered_login_works'] = False
        print(f"❌ Registration failed: {register_response.json()}")
    
    return results

def test_pdf_extraction(token: str) -> Dict:
    """Test if PDF text extraction is working"""
    print("\n" + "="*60)
    print("TEST 2: PDF EXTRACTION")
    print("="*60)
    
    results = {}
    
    # Create a simple test PDF
    print("\n2a. Creating test PDF...")
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        import os
        
        # Create test PDF
        test_pdf_path = "test_extract.pdf"
        c = canvas.Canvas(test_pdf_path, pagesize=letter)
        c.drawString(100, 750, "This is a test PDF for extraction")
        c.drawString(100, 730, "It contains multiple lines of text")
        c.drawString(100, 710, "The extraction should work properly")
        c.showPage()
        c.save()
        print(f"✅ Test PDF created: {test_pdf_path}")
        
        # Upload the PDF
        print("\n2b. Uploading test PDF...")
        with open(test_pdf_path, 'rb') as f:
            files = {'file': (test_pdf_path, f, 'application/pdf')}
            headers = {'Authorization': f'Bearer {token}'}
            
            upload_response = requests.post(
                f"{BACKEND_URL}/api/v1/documents/upload",
                files=files,
                headers=headers,
                timeout=30
            )
        
        print(f"Upload Status: {upload_response.status_code}")
        upload_data = upload_response.json()
        print(f"Upload Response: {json.dumps(upload_data, indent=2)}")
        
        if upload_response.status_code == 201:
            results['pdf_upload_works'] = True
            
            # Check if text was extracted
            if upload_data.get('text_content_summary'):
                results['pdf_extraction_works'] = True
                print("✅ PASS: PDF text extracted")
                print(f"Summary: {upload_data['text_content_summary'][:100]}")
            else:
                results['pdf_extraction_works'] = False
                print("❌ FAIL: PDF uploaded but text not extracted")
        else:
            results['pdf_upload_works'] = False
            results['pdf_extraction_works'] = False
            print(f"❌ Upload failed: {upload_data.get('detail')}")
        
        # Clean up
        if os.path.exists(test_pdf_path):
            os.remove(test_pdf_path)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        results['pdf_extraction_works'] = False
    
    return results

def test_document_listing(token: str) -> Dict:
    """Test if uploaded documents are listed after upload"""
    print("\n" + "="*60)
    print("TEST 3: DOCUMENT LISTING & STATUS")
    print("="*60)
    
    results = {}
    
    print("\n3a. Fetching user documents...")
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(
        f"{BACKEND_URL}/api/v1/documents/user_documents",
        headers=headers,
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        documents = response.json()
        print(f"Documents found: {len(documents)}")
        
        if len(documents) > 0:
            results['documents_listed'] = True
            print("✅ PASS: Documents are listed")
            for doc in documents:
                print(f"  - {doc.get('filename')} ({doc.get('status')})")
        else:
            results['documents_listed'] = False
            print("❌ FAIL: No documents found after upload")
    else:
        results['documents_listed'] = False
        print(f"❌ Error fetching documents: {response.json()}")
    
    return results

def main():
    print("\n" + "#"*60)
    print("# ADVANCED RAG SYSTEM - DIAGNOSTIC TEST")
    print("#"*60)
    
    # Test authentication
    auth_results = test_auth_security()
    
    # Get token for further tests
    token = auth_results.get('token')
    
    if token:
        # Test PDF extraction
        pdf_results = test_pdf_extraction(token)
        
        # Test document listing
        doc_results = test_document_listing(token)
    else:
        pdf_results = {}
        doc_results = {}
        print("\n⚠️ Cannot test PDF extraction and document listing without valid token")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    all_results = {
        **auth_results,
        **pdf_results,
        **doc_results
    }
    
    issues_found = []
    
    if not auth_results.get('unregistered_login_blocked'):
        issues_found.append("❌ CRITICAL: Non-registered emails can login")
    
    if not pdf_results.get('pdf_extraction_works'):
        issues_found.append("❌ PDF text extraction not working")
    
    if not doc_results.get('documents_listed'):
        issues_found.append("❌ Uploaded documents not showing in list")
    
    if issues_found:
        print("\nISSUES FOUND:")
        for issue in issues_found:
            print(issue)
    else:
        print("\n✅ All tests passed!")
    
    print("\nDetailed Results:")
    for key, value in all_results.items():
        if key != 'token':
            print(f"  {key}: {value}")

if __name__ == "__main__":
    main()
