# AVA International Assignment
# Invoice Extraction AI

An AI-powered invoice data extraction system that accepts JPG, PNG, and PDF invoices,
extracts structured data using OCR + LLM, stores results in Supabase, and provides analytics.

## Live Demo
- Frontend: https://your-app.vercel.app
- Backend API: https://your-api.onrender.com
- API Docs: https://your-api.onrender.com/docs

## Architecture
User → React Frontend → FastAPI Backend → OCR (Tesseract) → LLM (Cloudflare AI)
↓
Supabase Storage (files)
Supabase DB (structured data)
↓
Analytics API → React Dashboard

## Tech Stack
- **Frontend**: React + Vite
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL)
- **Storage**: Supabase Storage
- **OCR**: Tesseract
- **LLM**: Cloudflare Workers AI (Llama 3.1)
- **Deployment**: Render (backend), Vercel (frontend)

## Key Design Decisions

### Why OCR + LLM instead of Vision API?
OCR is free and fast. We only call the LLM for structured parsing,
keeping costs low while maintaining accuracy.

### Why Cloudflare Workers AI?
Free tier with no credit card required. 10,000 requests/day.
Uses Llama 3.1 8B which is strong enough for structured extraction.

### Why separate invoices and extracted_data tables?
Extraction can fail and be retried without corrupting the invoice record.
Allows re-extraction without re-uploading files.

### Why jsonb for line_items?
Line items vary per invoice. JSONB avoids complex joins and
PostgreSQL can query it efficiently.

## Features
- Single and batch invoice upload
- OCR text extraction from JPG, PNG, PDF
- LLM parsing with retry logic (3 attempts)
- Confidence scores per field
- Duplicate invoice detection
- Format fingerprinting for repeat vendors
- Vendor name normalization
- Analytics dashboard (spend by vendor, monthly trends)

## Database Schema
- `users` — user accounts
- `files_metadata` — uploaded file info + status tracking
- `invoices` — invoice records with format fingerprint
- `extracted_data` — AI-extracted fields + confidence scores

## Assumptions & Limitations
- OCR quality depends on image resolution (300 DPI recommended)
- LLM parsing works best with English invoices
- Free tier LLM has rate limits
- No real authentication (uses demo-user for now)

## Potential Improvements
- Add Supabase Auth for real user accounts
- Use vector embeddings for better format detection
- Add human review queue for low confidence scores
- Support more languages
- Add email notifications on completion
- Implement webhook for async processing

## Setup Instructions

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
# Add .env file with credentials
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables