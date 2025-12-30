import os
import json
import google.generativeai as genai
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# Setup API Key (Nanti diatur di Cloud)
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = FastAPI()

# Agar bisa diakses dari Frontend mana saja
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
async def extract_document(file: UploadFile = File(...)):
    # 1. Baca File
    content = await file.read()

    # 2. Panggil Gemini 2.0 Flash
    model = genai.GenerativeModel("models/gemini-2.0-flash")
    prompt = "Extract data from this KTP image to JSON format: {NIK, nama, alamat, tempat lahir, tanggal lahir, agama, pekerjaan, kewarganegaraan}"

    try:
        response = model.generate_content([
            {'mime_type': file.content_type, 'data': content},
            prompt
        ])
        return {"status": "success", "data": response.text}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
