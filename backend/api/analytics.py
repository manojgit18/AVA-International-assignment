# backend/api/analytics.py

from fastapi import APIRouter
from services.supabase_client import get_supabase

router = APIRouter()


@router.get("/summary")
def get_summary(user_id: str = "demo-user"):
    """Total invoices, total spend, currency breakdown."""
    supabase = get_supabase()

    result = supabase.table("invoices").select(
        "id, vendor_name, extracted_data(total_amount, currency, invoice_date)"
    ).eq("user_id", user_id).execute()

    invoices = result.data
    total_invoices = len(invoices)

    # Total spend
    total_spend = sum(
        i["extracted_data"]["total_amount"]
        for i in invoices
        if i.get("extracted_data") and i["extracted_data"].get("total_amount")
    )

    # Spend by vendor
    vendor_spend = {}
    for i in invoices:
        vendor = i.get("vendor_name") or "Unknown"
        amount = (i.get("extracted_data") or {}).get("total_amount") or 0
        vendor_spend[vendor] = round(vendor_spend.get(vendor, 0) + amount, 2)

    # Spend by currency
    currency_totals = {}
    for i in invoices:
        ed = i.get("extracted_data") or {}
        currency = ed.get("currency") or "USD"
        amount = ed.get("total_amount") or 0
        currency_totals[currency] = round(
            currency_totals.get(currency, 0) + amount, 2
        )

    # Monthly trends
    monthly = {}
    for i in invoices:
        ed = i.get("extracted_data") or {}
        date = ed.get("invoice_date")
        amount = ed.get("total_amount") or 0
        if date:
            month = date[:7]  # "2024-03"
            monthly[month] = round(monthly.get(month, 0) + amount, 2)

    return {
        "total_invoices": total_invoices,
        "total_spend":    round(total_spend, 2),
        "vendor_spend":   vendor_spend,
        "currency_totals": currency_totals,
        "monthly_trends": dict(sorted(monthly.items()))
    }


@router.get("/vendors")
def get_vendor_breakdown(user_id: str = "demo-user"):
    """Detailed vendor breakdown with invoice counts."""
    supabase = get_supabase()

    result = supabase.table("invoices").select(
        "vendor_name, extracted_data(total_amount, invoice_date)"
    ).eq("user_id", user_id).execute()

    vendors = {}
    for i in result.data:
        vendor = i.get("vendor_name") or "Unknown"
        amount = (i.get("extracted_data") or {}).get("total_amount") or 0
        if vendor not in vendors:
            vendors[vendor] = {"vendor_name": vendor, "invoice_count": 0, "total_spend": 0}
        vendors[vendor]["invoice_count"] += 1
        vendors[vendor]["total_spend"] = round(
            vendors[vendor]["total_spend"] + amount, 2
        )

    return {"vendors": list(vendors.values())}