# PDF Summary AI

Web application for uploading PDF documents and generating AI-powered summaries using OpenAI API.

## Features

- **PDF Upload**: Support for files up to 50MB, 100 pages
- **Text Extraction**: Extracts text with table structure preservation using PyMuPDF
- **OCR Support**: Automatic OCR for scanned documents via Tesseract
- **AI Summarization**: Generates concise summaries via OpenAI / Gemini / io.net
- **History**: Displays last 5 processed documents

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **PDF Processing**: PyMuPDF (pymupdf4llm) + Tesseract OCR
- **AI**: OpenAI API / Google Gemini / io.net (configurable)
- **Frontend**: Jinja2 templates, vanilla JS

## Project Structure

```
PDF_Summary_AI/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── database.py          # Database setup
│   ├── models.py            # SQLAlchemy models
│   ├── services/
│   │   ├── pdf_parser.py    # PDF text extraction
│   │   ├── chunker.py       # Text chunking for large documents
│   │   └── summarizer.py    # LLM integration (async Map-Reduce)
│   └── templates/
│       └── index.html       # Web UI
├── uploads/                 # Uploaded PDF files
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Setup

### Prerequisites

- Python 3.11+
- API key (Google Gemini, OpenAI, or io.net)

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd PDF_Summary_AI
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

6. Open http://localhost:8000 in your browser

> **Note**: For OCR support (scanned PDFs), install [Tesseract](https://github.com/tesseract-ocr/tesseract). In Docker, it's included automatically.

### Docker

1. Create `.env` file:
```bash
cp .env.example .env
# Edit .env and add your API key
```

2. Build and run:
```bash
docker-compose up --build
```

3. Open http://localhost:8000

#### Docker Commands

```bash
# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild after code changes
docker-compose up --build
```

#### Data Persistence

Data is stored in mounted volumes:
- `./uploads/` — uploaded PDF files
- `./data/` — SQLite database

## API Documentation

### Endpoints

#### `GET /`
Renders the main page with upload form and document history.

#### `POST /upload`
Upload a PDF file and generate summary.

**Request**: `multipart/form-data` with `file` field

**Response**:
```json
{
  "id": 1,
  "filename": "document.pdf",
  "summary": "Summary text...",
  "created_at": "2024-01-15T10:30:00"
}
```

#### `GET /history`
Get last 5 processed documents.

**Response**:
```json
[
  {
    "id": 1,
    "filename": "document.pdf",
    "summary": "Summary text...",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

#### `GET /document/{doc_id}`
Get specific document by ID.

**Response**:
```json
{
  "id": 1,
  "filename": "document.pdf",
  "summary": "Summary text...",
  "created_at": "2024-01-15T10:30:00"
}
```

**Error** (404):
```json
{
  "detail": "Document not found"
}
```

### Error Responses

All endpoints may return these errors:

| Status | Description |
|--------|-------------|
| `400` | Bad request (invalid file type, file too large, too many pages) |
| `404` | Document not found |
| `500` | Internal server error (LLM API error, etc.) |

### Interactive API Docs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider: `gemini`, `openai`, or `ionet` | `gemini` |
| `GOOGLE_API_KEY` | Google Gemini API key | - |
| `GEMINI_MODEL` | Gemini model name | `gemini-2.0-flash` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENAI_MODEL` | OpenAI model name | `gpt-4o-mini` |
| `IONET_API_KEY` | io.net API key | - |
| `IONET_BASE_URL` | io.net API base URL | `https://api.intelligence.io.solutions/api/v1` |
| `IONET_MODEL` | io.net model name | `deepseek-ai/DeepSeek-V3` |
| `LLM_TEMPERATURE` | LLM temperature (creativity) | `0.3` |
| `LLM_MAX_TOKENS` | Max tokens in LLM response | `1500` |
| `RATE_LIMIT_RPM` | Rate limit (requests/minute) | `5` |
| `MAX_FILE_SIZE_MB` | Max PDF file size in MB | `50` |
| `MAX_PAGES` | Max PDF pages allowed | `100` |
| `DATABASE_URL` | Database connection string | SQLite |
