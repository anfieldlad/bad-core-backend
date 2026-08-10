import os
import json
import hashlib
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import SessionLocal, engine, get_db
from providers import get_vision_provider
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

# Schema creation is deliberately NOT done at import time. Doing so opens a
# database connection while the module loads, so an unreachable database made
# the import raise, uvicorn exit, and systemd restart the service in a loop.
_schema_ready = False


def _ensure_schema() -> bool:
    """Create tables if needed. Returns True once the schema exists.

    Safe to call repeatedly: it retries until it succeeds, then short-circuits.
    """
    global _schema_ready
    if not _schema_ready:
        try:
            models.Base.metadata.create_all(bind=engine)
            _schema_ready = True
        except Exception as exc:
            print(f"WARN: schema init deferred, database unreachable: {exc}")
    return _schema_ready


def _db_reachable() -> bool:
    """Check live database connectivity with a trivial query."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    # A failure here is logged, not raised: the process must stay up so the
    # service degrades instead of crash-looping.
    _ensure_schema()
    yield


# Setup the configured LLM provider (Gemini or any OpenAI-compatible endpoint)
llm = get_vision_provider()
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()

app = FastAPI(lifespan=lifespan)

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

@app.get("/health")
def health():
    """Report database reachability. 503 when degraded, so probes can see it."""
    reachable = _db_reachable()
    if reachable:
        # Pick up schema creation that was deferred by an earlier outage.
        _ensure_schema()
    return JSONResponse(
        content={
            "status": "ok" if reachable else "degraded",
            "database": "up" if reachable else "down",
        },
        status_code=200 if reachable else 503,
    )

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
        # Call the configured LLM provider if no hash match
        extracted_text = llm.extract(
            image_bytes=content,
            mime_type=file.content_type,
            prompt=prompt,
        )

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
            
        return {"status": "success", "source": LLM_PROVIDER, "data": data}
        
    except Exception as e:
        return {"status": "error", "detail": str(e)}
