# add_cors.py
import re

# Read the file
with open('backend/api/server.py', 'r') as f:
    content = f.read()

# Step 1: Add import if not present
if 'from fastapi.middleware.cors import CORSMiddleware' not in content:
    # Find the line with "from fastapi import FastAPI"
    content = content.replace(
        'from fastapi import FastAPI, HTTPException',
        'from fastapi import FastAPI, HTTPException\nfrom fastapi.middleware.cors import CORSMiddleware'
    )
    print("✅ Added CORS import")

# Step 2: Add middleware if not present
if 'app.add_middleware' not in content:
    # Find the app = FastAPI(...) block and add middleware after it
    cors_middleware = '''
# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
'''
    # Insert after app = FastAPI(...)
    content = content.replace(
        'version="1.0.0",\n)',
        'version="1.0.0",\n)' + cors_middleware
    )
    print("✅ Added CORS middleware")

# Write back
with open('backend/api/server.py', 'w') as f:
    f.write(content)

print("✅ CORS added successfully!")
