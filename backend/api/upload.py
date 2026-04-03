# backend/api/upload.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from services.supabase_client import get_supabase
from services.ocr import extract_text_from_file
from services.llm_parser import parse_invoice_with_llm
from services.validator import validate_and_clean
from services.format_detector import generate_fingerprint, find_similar_format, is_duplicate_invoice
from services.vendor_normalizer import normalize_vendor
from models.invoice import UploadResponse
import uuid, os, logging

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_TYPES = {"pdf", "jpg", "jpeg", "png"}
MAX_FILE_SIZE  = 10 * 1024 * 1024  # 10 MB


# ── Single upload ─────────────────────────────────────────────
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

    # ── Step 6b: Format detection ─────────────────────────────
    fingerprint = generate_fingerprint(raw_text)
    similar     = find_similar_format(fingerprint, user_id)
    if similar:
        logger.info(f"Known format from vendor: {similar.get('vendor_name')}")

    # ── Step 6c: Duplicate detection ──────────────────────────
    duplicate = is_duplicate_invoice(
        extracted.invoice_number,
        extracted.vendor_name,
        user_id
    )

    # ── Step 7: Save to DB ────────────────────────────────────
    invoice_record = supabase.table("invoices").insert({
        "user_id":            user_id,
        "file_id":            file_id,
        "invoice_number":     extracted.invoice_number,
        "vendor_name":        normalize_vendor(extracted.vendor_name),
        "format_fingerprint": fingerprint,
        "is_duplicate":       duplicate,
    }).execute()
    invoice_id = invoice_record.data[0]["id"]

    supabase.table("extracted_data").insert({
        "invoice_id":         invoice_id,
        "invoice_date":       extracted.invoice_date,
        "due_date":           extracted.due_date,
        "total_amount":       extracted.total_amount,
        "currency":           extracted.currency,
        "line_items":         [i.dict() for i in extracted.line_items],
        "confidence_scores":  extracted.confidence_scores,
        "raw_ocr_text":       raw_text,
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


# ── Batch upload ──────────────────────────────────────────────
@router.post("/batch")
async def upload_batch(
    files: List[UploadFile] = File(...),
    user_id: str = "demo-user"
):
    """
    Upload multiple invoices at once.
    Processes each file through the full pipeline.
    Returns results for all files.
    """
    if len(files) > 10:
        raise HTTPException(400, "Maximum 10 files per batch")

    results = []

    for file in files:
        try:
            # ── Validate ──────────────────────────────────────
            ext = file.filename.rsplit(".", 1)[-1].lower()
            if ext not in ALLOWED_TYPES:
                results.append({
                    "file_name": file.filename,
                    "status":    "failed",
                    "error":     f"Unsupported type: {ext}"
                })
                continue

            file_bytes = await file.read()
            if len(file_bytes) > MAX_FILE_SIZE:
                results.append({
                    "file_name": file.filename,
                    "status":    "failed",
                    "error":     "File too large"
                })
                continue

            supabase = get_supabase()

            # ── Store file ────────────────────────────────────
            storage_path = f"{user_id}/{uuid.uuid4()}.{ext}"
            supabase.storage.from_(os.getenv("STORAGE_BUCKET")).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": file.content_type}
            )
            file_url = supabase.storage.from_(
                os.getenv("STORAGE_BUCKET")
            ).get_public_url(storage_path)

            # ── Save file record ──────────────────────────────
            file_record = supabase.table("files_metadata").insert({
                "user_id":         user_id,
                "file_name":       file.filename,
                "file_url":        file_url,
                "file_type":       ext,
                "file_size_bytes": len(file_bytes),
                "status":          "ocr_processing"
            }).execute()
            file_id = file_record.data[0]["id"]

            # ── OCR ───────────────────────────────────────────
            raw_text = extract_text_from_file(file_bytes, ext)

            # ── LLM ───────────────────────────────────────────
            extracted = parse_invoice_with_llm(raw_text)
            extracted = validate_and_clean(extracted)

            # ── Format + duplicate detection ──────────────────
            fingerprint = generate_fingerprint(raw_text)
            duplicate   = is_duplicate_invoice(
                extracted.invoice_number,
                extracted.vendor_name,
                user_id
            )

            # ── Save to DB ────────────────────────────────────
            invoice_record = supabase.table("invoices").insert({
                "user_id":            user_id,
                "file_id":            file_id,
                "invoice_number":     extracted.invoice_number,
                "vendor_name":        normalize_vendor(extracted.vendor_name),
                "format_fingerprint": fingerprint,
                "is_duplicate":       duplicate,
            }).execute()
            invoice_id = invoice_record.data[0]["id"]

            supabase.table("extracted_data").insert({
                "invoice_id":         invoice_id,
                "invoice_date":       extracted.invoice_date,
                "due_date":           extracted.due_date,
                "total_amount":       extracted.total_amount,
                "currency":           extracted.currency,
                "line_items":         [i.dict() for i in extracted.line_items],
                "confidence_scores":  extracted.confidence_scores,
                "raw_ocr_text":       raw_text,
            }).execute()

            supabase.table("files_metadata").update(
                {"status": "completed"}
            ).eq("id", file_id).execute()

            results.append({
                "file_name":  file.filename,
                "file_id":    file_id,
                "invoice_id": invoice_id,
                "status":     "completed",
                "extracted":  extracted
            })

        except Exception as e:
            logger.error(f"Batch item failed {file.filename}: {e}")
            results.append({
                "file_name": file.filename,
                "status":    "failed",
                "error":     str(e)
            })

    successful = sum(1 for r in results if r["status"] == "completed")
    failed     = sum(1 for r in results if r["status"] == "failed")

    return {
        "total":      len(files),
        "successful": successful,
        "failed":     failed,
        "results":    results
    }