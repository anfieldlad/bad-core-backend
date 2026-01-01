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
   DATABASE_URL=postgresql://postgres:[password]@[host]:5432/postgres
   API_KEY=your_secret_api_key
   ALLOWED_ORIGINS=http://localhost:3000,https://core.badai.tech
   ```

## Running the API
```bash
uvicorn main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

## API Endpoints

### `GET /` - Health Check
Returns API status. **No authentication required.**

### `POST /extract` - Extract KTP Data
Upload an image (KTP) to extract data in JSON format.

**Authentication:** Requires `X-API-Key` header.

**Example:**
```bash
curl -X POST "http://localhost:8000/extract" \
  -H "X-API-Key: your_secret_api_key" \
  -F "file=@ktp_image.jpg"
```
