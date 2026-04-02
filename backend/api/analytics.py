# backend/api/analytics.py

from fastapi import APIRouter
from services.supabase_client import get_supabase

router = APIRouter()

@router.get("/summary")
def get_summary(user_id: str = "demo-user"):
    """Basic analytics — total invoices and total spend."""
    supabase = get_supabase()

    invoices = supabase.table("invoices").select(
        "id, vendor_name, extracted_data(total_amount, currency, invoice_date)"
    ).eq("user_id", user_id).execute()

    total_invoices = len(invoices.data)
    total_spend = sum(
        i["extracted_data"]["total_amount"]
        for i in invoices.data
        if i.get("extracted_data") and i["extracted_data"].get("total_amount")
    )

    return {
        "total_invoices": total_invoices,
        "total_spend": round(total_spend, 2)
    }