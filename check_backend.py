import requests
import json
import time

print('⏳ Checking backend...\n')

for attempt in range(1, 11):
    try:
        r = requests.get('http://localhost:8000/', timeout=2)
        if r.status_code == 200:
            print('✅ BACKEND RUNNING ON PORT 8000\n')
            print('📊 Backend Status:')
            data = r.json()
            print(json.dumps(data, indent=2))
            print('\n🔗 Available Endpoints:')
            print('   - POST   /api/v1/auth/register    (Create account)')
            print('   - POST   /api/v1/auth/login       (Login)')
            print('   - POST   /api/v1/auth/logout      (Logout)')
            print('   - GET    /api/v1/documents        (List documents)')
            print('   - POST   /api/v1/documents/upload (Upload document)')
            print('   - POST   /api/v1/rag/query        (Ask questions)')
            print('   - GET    /docs                    (API documentation)')
            print('\n🌐 OpenAPI Docs: http://localhost:8000/docs')
            print('   (Perfect for testing all endpoints interactively)')
            break
    except Exception as e:
        print('.' * attempt, end='', flush=True)
        time.sleep(1)
else:
    print('\n❌ Backend not responding. Make sure it is running.')
    print('   Run: cd backend && python -m uvicorn main:app --reload')
