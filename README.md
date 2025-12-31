# BAD CORE API
**Business Automated Docs - Character Optical Recognition Engine**

This is a FastAPI-based backend for document extraction (currently focused on KTP) using the Google Gemini 2.0 Flash model.

## Features
- FastAPI for high-performance API endpoints.
- Gemini 2.0 Flash integration for OCR and data extraction.
- CORS enabled for frontend integration.
- KTP extraction caching with SQLAlchemy to store and deduplicate KTP records.

## Prerequisites
- Python 3.9+
- Google Gemini API Key

## Setup

1. **Clone the repository** (or navigate to this folder).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure environment variables**:
   Create a `.env` file based on `.env.example`:
   ```env
   GOOGLE_API_KEY=your_actual_api_key
   ```

## Running the API
```bash
uvicorn main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

## API Endpoints
- `GET /`: Health check.
- `POST /extract`: Upload an image (KTP) to extract data in JSON format.
