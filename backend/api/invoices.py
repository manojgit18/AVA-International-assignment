# backend/api/invoices.py

from fastapi import APIRouter
from services.supabase_client import get_supabase

router = APIRouter()

@router.get("/")
def get_invoices(user_id: str = "demo-user"):
    """Get all invoices for a user."""
    supabase = get_supabase()
    result = supabase.table("invoices").select(
        "*, extracted_data(*)"
    ).eq("user_id", user_id).order("created_at", desc=True).execute()
    return {"invoices": result.data}


@router.get("/{invoice_id}")
def get_invoice(invoice_id: str):
    """Get a single invoice with its extracted data."""
    supabase = get_supabase()
    result = supabase.table("invoices").select(
        "*, extracted_data(*), files_metadata(*)"
    ).eq("id", invoice_id).single().execute()
    return result.data