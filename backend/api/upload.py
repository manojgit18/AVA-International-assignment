# backend/api/upload.py
from services.format_detector import generate_fingerprint, find_similar_format, is_duplicate_invoice
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.supabase_client import get_supabase
from services.ocr import extract_text_from_file
from services.llm_parser import parse_invoice_with_llm
from services.validator import validate_and_clean
from models.invoice import UploadResponse
import uuid, os, logging

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_TYPES = {"pdf", "jpg", "jpeg", "png"}
MAX_FILE_SIZE  = 10 * 1024 * 1024  # 10 MB

@router.post("/", response_model=UploadResponse)
async def upload_invoice(
    file: UploadFile = File(...),
    user_id: str = "demo-user"
):
    # ── Step 1: Validate file ─────────────────────────────────
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_TYPES:
        raise HTTPException(400, f"Unsupported type: {ext}")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large. Max 10MB.")

    supabase = get_supabase()

    # ── Step 2: Upload to Supabase Storage ───────────────────
    storage_path = f"{user_id}/{uuid.uuid4()}.{ext}"
    try:
        supabase.storage.from_(os.getenv("STORAGE_BUCKET")).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": file.content_type}
        )
        file_url = supabase.storage.from_(
            os.getenv("STORAGE_BUCKET")
        ).get_public_url(storage_path)
    except Exception as e:
        raise HTTPException(500, f"Storage upload failed: {e}")

    # ── Step 3: Save file record ──────────────────────────────
    file_record = supabase.table("files_metadata").insert({
        "user_id":         user_id,
        "file_name":       file.filename,
        "file_url":        file_url,
        "file_type":       ext,
        "file_size_bytes": len(file_bytes),
        "status":          "ocr_processing"
    }).execute()
    file_id = file_record.data[0]["id"]

    # ── Step 4: OCR ───────────────────────────────────────────
    try:
        raw_text = extract_text_from_file(file_bytes, ext)

        # Debug: print OCR output to terminal
        print("=== OCR OUTPUT ===")
        print(raw_text)
        print("==================")

        supabase.table("files_metadata").update(
            {"status": "llm_parsing"}
        ).eq("id", file_id).execute()

    except Exception as e:
        supabase.table("files_metadata").update(
            {"status": "failed"}
        ).eq("id", file_id).execute()
        raise HTTPException(500, f"OCR failed: {e}")

    # ── Step 5: LLM Parsing ───────────────────────────────────
    extracted = parse_invoice_with_llm(raw_text)

    # ── Step 6: Validate ──────────────────────────────────────
    extracted = validate_and_clean(extracted)

    # ── Step 7: Save to DB ────────────────────────────────────
    invoice_record = supabase.table("invoices").insert({
        "user_id":        user_id,
        "file_id":        file_id,
        "invoice_number": extracted.invoice_number,
        "vendor_name":    extracted.vendor_name,
    }).execute()
    invoice_id = invoice_record.data[0]["id"]

    supabase.table("extracted_data").insert({
        "invoice_id":        invoice_id,
        "invoice_date":      extracted.invoice_date,
        "due_date":          extracted.due_date,
        "total_amount":      extracted.total_amount,
        "currency":          extracted.currency,
        "line_items":        [i.dict() for i in extracted.line_items],
        "confidence_scores": extracted.confidence_scores,
        "raw_ocr_text":      raw_text,
    }).execute()

    # ── Step 8: Mark complete ─────────────────────────────────
    supabase.table("files_metadata").update(
        {"status": "completed"}
    ).eq("id", file_id).execute()

    return UploadResponse(
        file_id=file_id,
        invoice_id=invoice_id,
        status="completed",
        extracted=extracted
    )