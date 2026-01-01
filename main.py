import os
import json
import hashlib
from datetime import datetime, timedelta
import google.genai as genai
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from database import SessionLocal, engine, get_db
import models

# Load environment variables first
load_dotenv()

# API Key Configuration
API_KEY = os.getenv("API_KEY")

# CORS Configuration - comma-separated list of allowed origins
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")


def verify_api_key(x_api_key: str = Header(..., description="API Key for authentication")):
    """Dependency to verify the API key from request headers."""
    if not API_KEY:
        raise HTTPException(
            status_code=500,
            detail="API_KEY not configured on server"
        )
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key"
        )
    return x_api_key

# Initialize database tables
models.Base.metadata.create_all(bind=engine)

# Setup Gemini Client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

app = FastAPI()

# Enable CORS with configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type"],
)

@app.get("/")
def home():
    return {"message": "BAD CORE API is Running!"}

@app.post("/extract")
async def extract_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    # 1. Read File
    content = await file.read()
    
    # Calculate hash to potentially skip Gemini for identical files
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Check if this exact image was extracted before (anytime)
    existing_record = db.query(models.KTPRecord).filter(
        models.KTPRecord.image_hash == file_hash
    ).first()
    
    if existing_record:
        return {"status": "success", "source": "cache (hash matching)", "data": existing_record.data}

    # Define prompt
    prompt = "Extract data from this KTP image to JSON format: {NIK, nama, tempat lahir, tanggal lahir, jenis kelamin, alamat, agama, status perkawinan, pekerjaan, kewarganegaraan}"

    try:
        # Call Gemini if no hash match
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                genai.types.Part.from_bytes(data=content, mime_type=file.content_type),
                prompt
            ]
        )
        
        extracted_text = response.text
        clean_json = extracted_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        
        nik = data.get("NIK")
        if nik:
            # Secondary check: If the NIK exists and is fresh (even if image hash is different)
            # This handles the case of a different photo of the same KTP
            one_month_ago = datetime.utcnow() - timedelta(days=30)
            existing_by_nik = db.query(models.KTPRecord).filter(
                models.KTPRecord.nik == nik,
                models.KTPRecord.created_at >= one_month_ago
            ).first()
            
            if existing_by_nik:
                # Still technically called Gemini, but we can return the "standard" record or confirm
                # However, since we already called Gemini, we might as well use the new data 
                # OR update the old one with new hash.
                existing_by_nik.image_hash = file_hash # Update hash for future skip
                db.commit()
                return {"status": "success", "source": "cache (NIK matching)", "data": existing_by_nik.data}
            
            # Save new record
            new_record = models.KTPRecord(nik=nik, image_hash=file_hash, data=data)
            db.add(new_record)
            db.commit()
            
        return {"status": "success", "source": "gemini", "data": data}
        
    except Exception as e:
        return {"status": "error", "detail": str(e)}
