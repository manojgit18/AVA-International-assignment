// src/pages/InvoiceDetail.jsx
export default function InvoiceDetail({ invoice, onBack }) {
  if (!invoice) return <p>No invoice selected</p>

  const data = invoice.extracted_data || {}

  const fields = [
    ["Invoice Number", data.invoice_number],
    ["Vendor Name", data.vendor_name],
    ["Invoice Date", data.invoice_date],
    ["Due Date", data.due_date],
    ["Total Amount", data.total_amount],
    ["Currency", data.currency],
  ]

  return (
    <div>
      <button
        onClick={onBack}
        style={{
          marginBottom: 16,
          padding: "6px 12px",
          border: "1px solid #ddd",
          borderRadius: 6,
          cursor: "pointer"
        }}
      >
        ← Back to Invoices
      </button>

      <h2>Invoice Details</h2>

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        gap: 12
      }}>
        {fields.map(([label, value]) => (
          <div key={label} style={{
            padding: 12,
            border: "1px solid #eee",
            borderRadius: 8
          }}>
            <div style={{ fontSize: 12, color: "#6b7280" }}>{label}</div>
            <div style={{ fontWeight: 600 }}>{value || "Not found"}</div>
          </div>
        ))}
      </div>

      {/* Line items */}
      {data?.line_items?.length > 0 && (
        <div style={{ marginTop: 20 }}>
          <h4>Line Items</h4>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th>Description</th>
                <th>Qty</th>
                <th>Unit Price</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {data.line_items.map((item, i) => (
                <tr key={i}>
                  <td>{item.description}</td>
                  <td>{item.quantity}</td>
                  <td>{item.unit_price}</td>
                  <td>{item.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}