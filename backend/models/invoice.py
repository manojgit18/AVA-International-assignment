# backend/models/invoice.py

from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import date

class LineItem(BaseModel):
    description: str
    quantity:    Optional[float] = None
    unit_price:  Optional[float] = None
    total:       Optional[float] = None

class ExtractedInvoice(BaseModel):
    invoice_number: Optional[str] = None
    vendor_name:    Optional[str] = None
    invoice_date:   Optional[str] = None   # kept as string; validated separately
    due_date:       Optional[str] = None
    total_amount:   Optional[float] = None
    currency:       Optional[str] = "USD"
    line_items:     Optional[List[LineItem]] = []
    confidence_scores: Optional[dict] = {}

    @validator("currency")
    def currency_uppercase(cls, v):
        # Always store currency as uppercase e.g. "usd" → "USD"
        return v.upper() if v else "USD"

    @validator("total_amount")
    def total_must_be_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError("total_amount cannot be negative")
        return v

class UploadResponse(BaseModel):
    file_id:    str
    invoice_id: str
    status:     str
    extracted:  ExtractedInvoice