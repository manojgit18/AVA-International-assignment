# backend/services/llm_parser.py

import json
import os
import logging
import requests
import time
import re
from models.invoice import ExtractedInvoice
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN  = os.getenv("CLOUDFLARE_API_TOKEN")

CF_URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/meta/llama-3.1-8b-instruct"

MAX_RETRIES = 3


# 🔥 FALLBACK (VERY IMPORTANT)
def fallback_extract(ocr_text: str):
    invoice_match = re.search(r'(INV[-/ ]?\d+)', ocr_text, re.I)

    return {
        "invoice_number": invoice_match.group(1) if invoice_match else None,
        "vendor_name": ocr_text.split("\n")[0].strip() if ocr_text else None,
        "invoice_date": None,
        "due_date": None,
        "total_amount": None,
        "currency": None,
        "line_items": [],
        "confidence_scores": {}
    }


def parse_invoice_with_llm(ocr_text: str) -> ExtractedInvoice:
    if not ACCOUNT_ID or not API_TOKEN:
        logger.warning("No Cloudflare credentials — using fallback")
        return ExtractedInvoice(**fallback_extract(ocr_text))

    user_prompt = build_prompt(ocr_text)

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
                            "content": "You are a strict JSON generator. Return ONLY valid JSON."
                        },
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ],
                    "max_tokens": 1024,
                    "temperature": 0
                },
                timeout=60  # 🔥 increased timeout
            )

            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

            result = response.json()

            if not result.get("success"):
                raise Exception(f"Cloudflare error: {result.get('errors')}")

            raw_text = result["result"]["response"].strip()

            # 🔥 Clean response
            if "{" in raw_text:
                raw_text = raw_text[raw_text.index("{"):]
            if "}" in raw_text:
                raw_text = raw_text[:raw_text.rindex("}") + 1]

            data = json.loads(raw_text)

            return ExtractedInvoice(**data)

        except Exception as e:
            logger.warning(f"Attempt {attempt} failed: {e}")
            time.sleep(2)  # 🔥 retry delay

    # 🔥 FINAL FALLBACK (THIS FIXES YOUR ISSUE)
    logger.error("All retries failed — using fallback extraction")
    fallback_data = fallback_extract(ocr_text)
    return ExtractedInvoice(**fallback_data)


def build_prompt(ocr_text: str) -> str:
    return f"""
You are an expert invoice extraction AI.

Extract structured data from noisy OCR text.

STRICT RULES:
- Return ONLY valid JSON
- No explanation
- No markdown
- If unsure → return null

FIELDS:
invoice_number
vendor_name
invoice_date (YYYY-MM-DD)
due_date (YYYY-MM-DD)
total_amount (number)
currency (USD, EUR, GBP, INR)
line_items (array)
confidence_scores (object)

IMPORTANT:
- Invoice number looks like INV-12345
- Vendor name is usually at top
- Fix OCR errors (O→0, I→1)

OCR TEXT:
{ocr_text}
"""