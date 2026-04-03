// src/App.jsx
import { useState } from "react"
import Upload from "./pages/Upload.jsx"
import Invoices from "./pages/Invoices.jsx"
import Analytics from "./pages/Analytics.jsx"
import InvoiceDetail from "./pages/InvoiceDetail.jsx"

export default function App() {
  const [page, setPage] = useState("upload")
  const [selectedInvoice, setSelectedInvoice] = useState(null)

  const navStyle = (p) => ({
    padding: "8px 20px",
    background: page === p ? "#4F46E5" : "#f3f4f6",
    color: page === p ? "white" : "#374151",
    border: "none",
    borderRadius: 8,
    cursor: "pointer",
    fontWeight: 600,
    textTransform: "capitalize",
    fontSize: 14,
  })

  return (
    <div style={{
      fontFamily: "Inter, sans-serif",
      maxWidth: 960,
      margin: "0 auto",
      padding: "24px 20px",
    }}>
      {/* Header */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        marginBottom: 28,
        paddingBottom: 16,
        borderBottom: "2px solid #e5e7eb",
      }}>
        <div style={{
          width: 36, height: 36,
          background: "#4F46E5",
          borderRadius: 8,
          display: "flex", alignItems: "center", justifyContent: "center",
          color: "white", fontWeight: 700, fontSize: 18,
        }}>
          Invoicer
        </div>

        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>
          Invoice Extractor AI
        </h1>

        <div style={{ flex: 1 }} />

        {["upload", "invoices", "analytics"].map(p => (
          <button key={p} onClick={() => setPage(p)} style={navStyle(p)}>
            {p}
          </button>
        ))}
      </div>

      {/* Page content */}
      {page === "upload" && <Upload />}

      {page === "invoices" && (
        <Invoices
          onSelectInvoice={(inv) => {
            setSelectedInvoice(inv)
            setPage("detail")
          }}
        />
      )}

      {page === "analytics" && <Analytics />}

      {page === "detail" && (
        <InvoiceDetail
          invoice={selectedInvoice}
          onBack={() => setPage("invoices")}
        />
      )}
    </div>
  )
}