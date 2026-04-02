# backend/services/validator.py

from datetime import datetime
from models.invoice import ExtractedInvoice
import logging

logger = logging.getLogger(__name__)

DATE_FORMATS = [
    "%Y-%m-%d",     # 2024-03-15   (our target format)
    "%d/%m/%Y",     # 15/03/2024   (common in Europe)
    "%m/%d/%Y",     # 03/15/2024   (common in US)
    "%d-%m-%Y",     # 15-03-2024
    "%B %d, %Y",    # March 15, 2024
    "%b %d, %Y",    # Mar 15, 2024
    "%d %B %Y",     # 15 March 2024
]

def validate_and_clean(invoice: ExtractedInvoice) -> ExtractedInvoice:
    """
    Runs all validators and returns a cleaned invoice object.
    Never raises — logs issues and continues with best-effort values.
    """
    invoice.invoice_date = _parse_date(invoice.invoice_date, "invoice_date")
    invoice.due_date     = _parse_date(invoice.due_date, "due_date")
    invoice.total_amount = _parse_amount(invoice.total_amount)
    invoice.currency     = _validate_currency(invoice.currency)
    invoice.vendor_name  = _clean_text(invoice.vendor_name)
    return invoice


def _parse_date(value: str | None, field_name: str) -> str | None:
    """
    Tries multiple date formats and normalizes to YYYY-MM-DD.
    Returns None if no format matches.
    """
    if not value:
        return None

    # Remove extra whitespace
    value = value.strip()

    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.strftime("%Y-%m-%d")  # normalize to ISO format
        except ValueError:
            continue

    logger.warning(f"Could not parse {field_name}: '{value}'")
    return None


def _parse_amount(value) -> float | None:
    """
    Converts various amount formats to a float.
    Handles: "$1,500.00", "1.500,00" (European), "1500", 1500.0
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return round(float(value), 2)

    if isinstance(value, str):
        # Remove currency symbols and spaces
        cleaned = value.replace("$", "").replace("€", "").replace("£", "")
        cleaned = cleaned.replace(" ", "").strip()

        # Handle European format: 1.500,00 → 1500.00
        if "," in cleaned and "." in cleaned:
            if cleaned.index(",") > cleaned.index("."):
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", ".")

        try:
            return round(float(cleaned), 2)
        except ValueError:
            logger.warning(f"Could not parse amount: '{value}'")
            return None

    return None


def _validate_currency(value: str | None) -> str:
    """Validates against common ISO 4217 codes. Defaults to USD."""
    known = {"USD","EUR","GBP","INR","JPY","CAD","AUD","CHF","CNY","SGD"}
    if value and value.upper() in known:
        return value.upper()
    return "USD"


def _clean_text(value: str | None) -> str | None:
    """Strips extra whitespace and newlines from text fields."""
    if not value:
        return None
    return " ".join(value.split())