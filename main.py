import os
import json
import hashlib
from datetime import datetime, timedelta
import google.genai as genai
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from database import SessionLocal, engine, get_db
import models

# Initialize database tables
models.Base.metadata.create_all(bind=engine)

load_dotenv()

# Setup Gemini Client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

app = FastAPI()

# Enable CORS to allow access from any frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "BAD CORE API is Running!"}

@app.post("/extract")
async def extract_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
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
