// src/pages/Analytics.jsx
import { useState, useEffect } from "react"
import axios from "axios"
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid,
} from "recharts"

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"

export default function Analytics() {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get(`${API}/api/analytics/summary?user_id=demo-user`)
      .then(r => setData(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p>Loading analytics...</p>
  if (!data)   return <p>No analytics data available</p>

  const vendorData  = Object.entries(data.vendor_spend  || {}).map(([name, total])  => ({ name, total }))
  const monthlyData = Object.entries(data.monthly_trends || {}).map(([month, total]) => ({ month, total }))

  const cards = [
    { label: "Total Invoices", value: data.total_invoices,                    color: "#4F46E5", bg: "#eef2ff" },
    { label: "Total Spend",    value: `$${data.total_spend?.toLocaleString()}`, color: "#16a34a", bg: "#f0fdf4" },
    { label: "Vendors",        value: Object.keys(data.vendor_spend || {}).length, color: "#ea580c", bg: "#fff7ed" },
  ]

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Analytics Dashboard</h2>

      {/* Summary cards */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(3, 1fr)",
        gap: 16, marginBottom: 32,
      }}>
        {cards.map(({ label, value, color, bg }) => (
          <div key={label} style={{
            padding: 20, borderRadius: 12,
            border: "1px solid #e5e7eb",
            background: bg,
          }}>
            <div style={{ fontSize: 13, color: "#6b7280", fontWeight: 500 }}>
              {label}
            </div>
            <div style={{ fontSize: 32, fontWeight: 700, color, marginTop: 6 }}>
              {value}
            </div>
          </div>
        ))}
      </div>

      {/* Vendor chart */}
      {vendorData.length > 0 && (
        <div style={{
          background: "white", borderRadius: 12,
          border: "1px solid #e5e7eb", padding: 20, marginBottom: 24,
        }}>
          <h4 style={{ margin: "0 0 16px" }}>Spend by Vendor</h4>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={vendorData} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip formatter={v => [`$${v.toLocaleString()}`, "Spend"]} />
              <Bar dataKey="total" fill="#4F46E5" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Monthly chart */}
      {monthlyData.length > 0 && (
        <div style={{
          background: "white", borderRadius: 12,
          border: "1px solid #e5e7eb", padding: 20, marginBottom: 24,
        }}>
          <h4 style={{ margin: "0 0 16px" }}>Monthly Spend Trends</h4>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={monthlyData} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip formatter={v => [`$${v.toLocaleString()}`, "Spend"]} />
              <Bar dataKey="total" fill="#16a34a" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Currency breakdown */}
      {Object.keys(data.currency_totals || {}).length > 0 && (
        <div style={{
          background: "white", borderRadius: 12,
          border: "1px solid #e5e7eb", padding: 20,
        }}>
          <h4 style={{ margin: "0 0 12px" }}>Currency Breakdown</h4>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            {Object.entries(data.currency_totals).map(([currency, total]) => (
              <div key={currency} style={{
                padding: "10px 20px",
                background: "#f3f4f6", borderRadius: 8,
                fontWeight: 600, fontSize: 15,
              }}>
                {currency}
                <span style={{ color: "#4F46E5", marginLeft: 8 }}>
                  ${total.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}