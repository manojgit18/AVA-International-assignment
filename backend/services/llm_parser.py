# backend/services/llm_parser.py

import json
import os
import logging
from google import genai
from google.genai import types
from models.invoice import ExtractedInvoice
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=_api_key) if _api_key else None

MAX_RETRIES = 3


def parse_invoice_with_llm(ocr_text: str) -> ExtractedInvoice:
    if client is None:
        logger.warning("No Gemini API key — returning empty invoice")
        return ExtractedInvoice()

    user_prompt = build_prompt(ocr_text)
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Gemini attempt {attempt}/{MAX_RETRIES}")

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                    response_mime_type="application/json"
                )
            )

            raw_text = response.text.strip()

            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.strip()

            data = json.loads(raw_text)
            invoice = ExtractedInvoice(**data)
            return invoice

        except Exception as e:
            error_str = str(e)
            last_error = e

            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                logger.error("Gemini quota exceeded — stopping retries")
                break

            logger.warning(f"Attempt {attempt} failed: {e}")
            user_prompt = build_retry_prompt(ocr_text, error_str)

    logger.error(f"All retries failed: {last_error}")
    return ExtractedInvoice()


def build_prompt(ocr_text: str) -> str:
    return (
        "You are an expert invoice data extraction assistant.\n"
        "Extract invoice fields from the OCR text below.\n\n"
        "Return a JSON object with EXACTLY these fields:\n"
        "- invoice_number: string or null\n"
        "- vendor_name: string or null\n"
        "- invoice_date: string in YYYY-MM-DD format or null\n"
        "- due_date: string in YYYY-MM-DD format or null\n"
        "- total_amount: number (no symbols, just digits) or null\n"
        "- currency: 3-letter ISO code (USD, EUR, GBP, INR) or null\n"
        "- line_items: array of objects with description, quantity, unit_price, total\n"
        "- confidence_scores: object with 0.0-1.0 score per field\n\n"
        "Rules:\n"
        "- Convert all dates to YYYY-MM-DD\n"
        "- Amounts as plain numbers: 1500.00 not $1,500.00\n"
        "- Map symbols: $ -> USD, EUR -> EUR, GBP -> GBP, Rs/INR -> INR\n"
        "- Net 30 / Net 60: due_date = invoice_date + N days\n"
        "- OCR noise: l may mean I, O may mean 0 in numbers\n"
        "- Missing fields: null, never fabricate\n"
        "- Return ONLY the JSON object, no explanation, no markdown\n\n"
        f"OCR TEXT:\n{ocr_text}"
    )


def build_retry_prompt(ocr_text: str, error: str) -> str:
    return (
        f"Your previous response caused this error: {error}\n\n"
        "Return ONLY valid JSON with these fields:\n"
        "invoice_number, vendor_name, invoice_date (YYYY-MM-DD),\n"
        "due_date (YYYY-MM-DD), total_amount (number),\n"
        "currency (3-letter code), line_items (array), confidence_scores (object)\n\n"
        "No explanation. No markdown. JSON only.\n\n"
        f"OCR TEXT:\n{ocr_text}"
    )