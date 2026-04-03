// src/pages/Invoices.jsx
import { useState, useEffect } from "react"
import axios from "axios"

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"

export default function Invoices() {
  const [invoices, setInvoices] = useState([])
  const [loading, setLoading]   = useState(true)

  useEffect(() => {
    axios.get(`${API}/api/invoices/?user_id=demo-user`)
      .then(r => setInvoices(r.data.invoices))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p>Loading invoices...</p>

  if (!invoices.length) return (
    <div style={{ textAlign: "center", padding: "60px 20px", color: "#6b7280" }}>
      <div style={{ fontSize: 48, marginBottom: 12 }}>📭</div>
      <p style={{ fontSize: 18, fontWeight: 600 }}>No invoices yet</p>
      <p>Upload an invoice to get started</p>
    </div>
  )

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>
        All Invoices
        <span style={{
          marginLeft: 10, fontSize: 14, fontWeight: 500,
          background: "#e0e7ff", color: "#4338ca",
          padding: "2px 10px", borderRadius: 20,
        }}>
          {invoices.length}
        </span>
      </h2>

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {invoices.map(inv => (
          <div key={inv.id} style={{
            padding: "16px 20px",
            border: "1px solid #e5e7eb",
            borderRadius: 10,
            background: "white",
            display: "flex",
            alignItems: "center",
            gap: 16,
          }}>
            {/* Icon */}
            <div style={{
              width: 40, height: 40, borderRadius: 8,
              background: "#eef2ff", display: "flex",
              alignItems: "center", justifyContent: "center",
              fontSize: 20, flexShrink: 0,
            }}>
              🧾
            </div>

            {/* Info */}
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, fontSize: 15 }}>
                {inv.vendor_name || "Unknown Vendor"}
              </div>
              <div style={{ color: "#6b7280", fontSize: 13, marginTop: 2 }}>
                {inv.invoice_number || "No invoice number"} •{" "}
                {inv.extracted_data?.invoice_date || "No date"}
              </div>
            </div>

            {/* Amount */}
            <div style={{ textAlign: "right" }}>
              <div style={{ fontWeight: 700, fontSize: 17, color: "#4F46E5" }}>
                {inv.extracted_data?.currency}{" "}
                {inv.extracted_data?.total_amount?.toLocaleString() ?? "—"}
              </div>
              {inv.is_duplicate && (
                <span style={{
                  fontSize: 11, padding: "2px 8px",
                  background: "#fef3c7", color: "#92400e",
                  borderRadius: 4, fontWeight: 500,
                }}>
                  DUPLICATE
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}