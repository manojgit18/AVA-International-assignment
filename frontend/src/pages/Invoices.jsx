// src/pages/Invoices.jsx
import { useState, useEffect } from "react"
import axios from "axios"

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"

export default function Invoices({ onSelectInvoice }) {
  const [invoices, setInvoices] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get(`${API}/api/invoices/?user_id=demo-user`)
      .then(r => setInvoices(r.data.invoices))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p>Loading invoices...</p>

  if (!invoices.length) return <p>No invoices found</p>

  return (
    <div>
      <h2>All Invoices ({invoices.length})</h2>

      {invoices.map(inv => (
        <div
          key={inv.id}
          onClick={() => onSelectInvoice(inv)}
          style={{
            padding: "16px",
            border: "1px solid #e5e7eb",
            borderRadius: 10,
            marginBottom: 10,
            cursor: "pointer",
            background: "white"
          }}
        >
          <strong>{inv.vendor_name || "Unknown Vendor"}</strong>
          <div style={{ fontSize: 13, color: "#6b7280" }}>
            {inv.invoice_number} • {inv.extracted_data?.invoice_date}
          </div>

          <div style={{ fontWeight: 700, color: "#4F46E5" }}>
            {inv.extracted_data?.currency}{" "}
            {inv.extracted_data?.total_amount}
          </div>
        </div>
      ))}
    </div>
  )
}