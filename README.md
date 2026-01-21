# BAD CORE API
**Business Automated Docs - Character Optical Recognition Engine**

This is a FastAPI-based backend for document extraction using the Google Gemini API. The application is built with SOLID principles and clean architecture for maintainability and extensibility.

## Features
- **Clean Architecture**: Separated concerns across layers (API, Service, Repository, Database)
- **SOLID Principles**: Following best practices for maintainable code
- **FastAPI**: High-performance async API endpoints
- **Gemini 2.0 Flash**: AI-powered OCR and data extraction
- **Smart Caching**: Dual-layer caching (image hash + unique identifier)
- **Extensible Design**: Easy to add new document types (SIM, Passport, etc.)
- **Type Safety**: Full type hints throughout the codebase
- **Comprehensive Logging**: Structured logging for debugging and monitoring

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

## Architecture

This application follows Clean Architecture and SOLID principles:

```
app/
├── config/          # Configuration management (Pydantic Settings)
├── core/            # Core utilities (logging, security, exceptions)
├── api/             # API layer (endpoints, dependencies)
├── services/        # Business logic layer
│   ├── interfaces/  # Abstract interfaces (OCR provider)
│   ├── ocr/         # OCR implementations (Gemini)
│   └── extractors/  # Document extractors (KTP, SIM, etc.)
├── repositories/    # Data access layer
├── models/          # Database models
├── schemas/         # Pydantic response/request schemas
└── db/              # Database configuration
```

### SOLID Principles Applied

- **Single Responsibility**: Each class has one reason to change
- **Open/Closed**: New document types can be added without modifying existing code
- **Liskov Substitution**: All extractors are interchangeable via base class
- **Interface Segregation**: Focused interfaces (OCRProvider, DocumentExtractor)
- **Dependency Inversion**: High-level modules depend on abstractions

### Adding New Document Types

To add a new document type (e.g., SIM):

1. Create extractor class in `app/services/extractors/sim_extractor.py`
2. Implement `DocumentExtractor` interface
3. Register in `app/api/deps.py`

No modifications to existing code required!

## Running the API
```bash
uvicorn main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

## Running Tests
```bash
pip install -r requirements-dev.txt
pytest
```

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
