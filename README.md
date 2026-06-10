# BAD CORE API
**Business Automated Docs - Character Optical Recognition Engine**

A FastAPI backend for document extraction (currently focused on Indonesian KTP).
It supports multiple LLM vision backends — Google Gemini or any OpenAI-compatible
endpoint — selectable at runtime via a single environment variable.

## Features
- **FastAPI** for high-performance API endpoints.
- **Pluggable LLM provider** for OCR and data extraction: **Gemini** or any
  **OpenAI-compatible** vision endpoint (OpenAI, vLLM, Ollama, LM Studio,
  Together, Groq, etc.). Switch with one env var — no code changes.
- **Extraction caching** with SQLAlchemy: identical images (by SHA-256 hash) and
  recently-seen NIKs are served from the database instead of re-calling the LLM.
- **API key authentication** via the `X-API-Key` header.
- **Configurable CORS** for frontend integration.

## Project structure
| File | Purpose |
|------|---------|
| `main.py` | FastAPI app, routes (`/`, `/extract`), auth, caching logic. |
| `providers.py` | LLM provider abstraction — `VisionProvider` interface plus Gemini / OpenAI-compatible implementations and the `get_vision_provider()` factory. |
| `database.py` | SQLAlchemy engine/session setup (Postgres, or SQLite fallback). |
| `models.py` | `KTPRecord` table definition. |

## Prerequisites
- Python 3.9+
- An API key for your chosen provider (Google Gemini, or an OpenAI-compatible endpoint)
- A PostgreSQL database (optional — falls back to a local SQLite file)

## Setup

1. **Clone the repository** (or navigate to this folder).
2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/Scripts/activate  # On Windows (Git Bash)
   # .venv\Scripts\activate       # On Windows (PowerShell/CMD)
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure environment variables**:
   Create a `.env` file based on `.env.example`.

   **Using Gemini (default):**
   ```env
   LLM_PROVIDER=gemini
   GOOGLE_API_KEY=your_actual_api_key
   # LLM_MODEL=gemini-2.5-flash-lite   # optional, this is the default

   DATABASE_URL=postgresql://postgres:[password]@[host]:5432/postgres
   API_KEY=your_secret_api_key
   ALLOWED_ORIGINS=http://localhost:3000,https://core.badai.tech
   ```

   **Using an OpenAI-compatible endpoint:**
   ```env
   LLM_PROVIDER=openai
   OPENAI_API_KEY=your_actual_api_key
   OPENAI_BASE_URL=https://api.openai.com/v1   # or your vLLM/Ollama/etc. URL
   LLM_MODEL=gpt-4o-mini                        # any vision-capable model

   DATABASE_URL=postgresql://postgres:[password]@[host]:5432/postgres
   API_KEY=your_secret_api_key
   ALLOWED_ORIGINS=http://localhost:3000,https://core.badai.tech
   ```

## Configuration reference

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM backend: `gemini` or `openai` | `gemini` |
| `LLM_MODEL` | Model name (must be vision-capable). Empty = per-provider default. | `gemini-2.5-flash-lite` (gemini) / `gpt-4o-mini` (openai) |
| `GOOGLE_API_KEY` | Gemini API key — required when `LLM_PROVIDER=gemini` | — |
| `OPENAI_API_KEY` | API key — required when `LLM_PROVIDER=openai` | — |
| `OPENAI_BASE_URL` | OpenAI-compatible endpoint base URL | `https://api.openai.com/v1` |
| `DATABASE_URL` | PostgreSQL connection string. `postgres://` is auto-normalized to `postgresql://`. | `sqlite:///./ktp.db` |
| `API_KEY` | Secret required in the `X-API-Key` request header | — |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins | `http://localhost:3000` |

> **Note:** the selected model must be **vision-capable**, since extraction sends the document image to the model.

## Running the API
```bash
uvicorn main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

## API Endpoints

### `GET /` — Health Check
Returns API status. **No authentication required.**

```json
{ "message": "BAD CORE API is Running!" }
```

### `POST /extract` — Extract KTP Data
Upload an image (KTP) to extract its fields as JSON.

**Authentication:** requires the `X-API-Key` header.

**Request:** `multipart/form-data` with a single `file` field (the image).

**Example:**
```bash
curl -X POST "http://localhost:8000/extract" \
  -H "X-API-Key: your_secret_api_key" \
  -F "file=@ktp_image.jpg"
```

**Response:**
```json
{
  "status": "success",
  "source": "openai",
  "data": {
    "NIK": "3171234567890001",
    "nama": "BUDI SANTOSO",
    "tempat_lahir": "JAKARTA",
    "tanggal_lahir": "01-01-1990",
    "jenis_kelamin": "LAKI-LAKI",
    "alamat": "JL MERDEKA NO 1",
    "agama": "ISLAM",
    "status_perkawinan": "KAWIN",
    "pekerjaan": "KARYAWAN SWASTA",
    "kewarganegaraan": "WNI"
  }
}
```

The `source` field tells you where the result came from:

| `source` | Meaning |
|----------|---------|
| `gemini` / `openai` | Freshly extracted by the configured LLM provider. |
| `cache (hash matching)` | Exact same image was extracted before (matched by SHA-256). No LLM call. |
| `cache (NIK matching)` | A different photo of a KTP with the same NIK was seen within the last 30 days. |

On failure the response is `{ "status": "error", "detail": "<message>" }`.

## Caching behavior
Each uploaded image is hashed (SHA-256). If that hash already exists in the
database, the stored result is returned immediately without calling the LLM.
Otherwise the image is sent to the provider; if the extracted **NIK** was already
recorded within the last 30 days, that record is reused (and its hash updated).
New NIKs are stored as fresh records.

## Frontend
A companion Next.js UI is available at
[bad-core-ui](https://github.com/anfieldlad/bad-core-ui), which talks to this
API's `GET /` and `POST /extract` endpoints.
