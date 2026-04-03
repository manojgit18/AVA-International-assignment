# backend/services/llm_parser.py

import json
import os
import logging
import requests
from models.invoice import ExtractedInvoice
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN  = os.getenv("CLOUDFLARE_API_TOKEN")

# Cloudflare Workers AI endpoint
CF_URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/meta/llama-3.1-8b-instruct"

MAX_RETRIES = 3


def parse_invoice_with_llm(ocr_text: str) -> ExtractedInvoice:
    if not ACCOUNT_ID or not API_TOKEN:
        logger.warning("No Cloudflare credentials — returning empty invoice")
        return ExtractedInvoice()

    user_prompt = build_prompt(ocr_text)
    last_error  = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Cloudflare AI attempt {attempt}/{MAX_RETRIES}")

            response = requests.post(
                CF_URL,
                headers={
                    "Authorization": f"Bearer {API_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert invoice data extraction assistant. Return ONLY valid JSON. No explanation. No markdown. No code fences."
                        },
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ],
                    "max_tokens": 1024,
                    "temperature": 0
                },
                timeout=30
            )

            # Check HTTP error
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

            result = response.json()

            # Cloudflare returns: {"result": {"response": "..."}, "success": true}
            if not result.get("success"):
                raise Exception(f"Cloudflare error: {result.get('errors')}")

            raw_text = result["result"]["response"].strip()

            # Strip markdown fences if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.strip()

            # Sometimes the model adds text before the JSON — find the JSON part
            if "{" in raw_text:
                raw_text = raw_text[raw_text.index("{"):]
            if "}" in raw_text:
                raw_text = raw_text[:raw_text.rindex("}") + 1]

            data = json.loads(raw_text)
            invoice = ExtractedInvoice(**data)
            return invoice

        except Exception as e:
            error_str = str(e)
            last_error = e

            # Stop retrying on auth errors
            if "401" in error_str or "403" in error_str:
                logger.error(f"Cloudflare auth error — stopping: {error_str}")
                break

            logger.warning(f"Attempt {attempt} failed: {e}")
            user_prompt = build_retry_prompt(ocr_text, error_str)

    logger.error(f"All retries failed: {last_error}")
    return ExtractedInvoice()


def build_prompt(ocr_text: str) -> str:
    return (
        "Extract invoice data from the OCR text below.\n\n"
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
        "- Map symbols: $ -> USD, € -> EUR, £ -> GBP, Rs/₹ -> INR\n"
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