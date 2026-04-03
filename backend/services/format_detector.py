# backend/services/format_detector.py

import hashlib
import re
import logging
from services.supabase_client import get_supabase

logger = logging.getLogger(__name__)

# Words that appear on almost every invoice — ignore these
# We only want words unique to this vendor's format
STOP_WORDS = {
    "invoice", "date", "due", "total", "amount", "tax", "subtotal",
    "bill", "to", "from", "payment", "terms", "description", "qty",
    "quantity", "price", "unit", "thank", "you", "please", "pay",
    "the", "and", "for", "net", "days", "page", "number", "no",
    "account", "bank", "email", "phone", "fax", "www", "http"
}


def generate_fingerprint(ocr_text: str) -> str:
    """
    Creates a short fingerprint from the structural keywords in OCR text.
    Same vendor = same fingerprint (even with different amounts/dates).
    """
    # Step 1: lowercase and extract only words (no numbers, no symbols)
    words = re.findall(r'[a-zA-Z]{3,}', ocr_text.lower())

    # Step 2: remove stop words — keep only vendor-specific structural words
    keywords = [w for w in words if w not in STOP_WORDS]

    # Step 3: remove duplicates and sort (order doesn't matter)
    unique_keywords = sorted(set(keywords))

    # Step 4: take top 20 most meaningful words
    top_keywords = unique_keywords[:20]

    # Step 5: join and hash into a short fingerprint
    keyword_string = " ".join(top_keywords)
    fingerprint = hashlib.md5(keyword_string.encode()).hexdigest()[:16]

    logger.info(f"Generated fingerprint: {fingerprint} from keywords: {top_keywords}")
    return fingerprint


def find_similar_format(fingerprint: str, user_id: str) -> dict | None:
    """
    Checks if we have seen this invoice format before.
    Returns the most recent matching invoice if found, None otherwise.
    """
    try:
        supabase = get_supabase()

        # Look for invoices with the same fingerprint from this user
        result = supabase.table("invoices").select(
            "id, vendor_name, format_fingerprint, created_at"
        ).eq("user_id", user_id).eq(
            "format_fingerprint", fingerprint
        ).order("created_at", desc=True).limit(1).execute()

        if result.data:
            logger.info(f"Found matching format: {fingerprint}")
            return result.data[0]

        return None

    except Exception as e:
        logger.error(f"Format detection error: {e}")
        return None


def is_duplicate_invoice(
    invoice_number: str,
    vendor_name: str,
    user_id: str
) -> bool:
    """
    Checks if an invoice with the same number and vendor already exists.
    Prevents processing the same invoice twice.
    """
    if not invoice_number or not vendor_name:
        return False

    try:
        supabase = get_supabase()

        result = supabase.table("invoices").select("id").eq(
            "user_id", user_id
        ).eq(
            "invoice_number", invoice_number
        ).eq(
            "vendor_name", vendor_name
        ).execute()

        is_dup = len(result.data) > 0
        if is_dup:
            logger.warning(f"Duplicate invoice detected: {invoice_number} from {vendor_name}")
        return is_dup

    except Exception as e:
        logger.error(f"Duplicate check error: {e}")
        return False