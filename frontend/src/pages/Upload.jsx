// src/pages/Upload.jsx
import { useState } from "react";
import axios from "axios";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  async function handleUpload() {
    if (!file) return alert("Please select a file first");
    setLoading(true);
    setError(null);
    setResult(null);

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await axios.post(
        `${API}/api/upload/?user_id=demo-user`,
        form,
      );
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  }

  const fields = [
    ["Invoice Number", result?.extracted?.invoice_number],
    ["Vendor Name", result?.extracted?.vendor_name],
    ["Invoice Date", result?.extracted?.invoice_date],
    ["Due Date", result?.extracted?.due_date],
    ["Total Amount", result?.extracted?.total_amount],
    ["Currency", result?.extracted?.currency],
  ];

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Upload Invoice</h2>
      <p style={{ color: "#6b7280", marginTop: -8 }}>
        Supports JPG, PNG, PDF — max 10MB
      </p>

      {/* Dropzone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${dragOver ? "#4F46E5" : "#d1d5db"}`,
          borderRadius: 12,
          padding: "40px 20px",
          textAlign: "center",
          background: dragOver ? "#eef2ff" : file ? "#f0fdf4" : "#fafafa",
          marginBottom: 16,
          transition: "all 0.2s",
          cursor: "pointer",
        }}
      >
        <div style={{ fontSize: 36, marginBottom: 8 }}>📄</div>
        <p style={{ margin: 0, color: "#374151", fontWeight: 500 }}>
          Drag and drop your invoice here
        </p>
        <p style={{ margin: "4px 0 12px", color: "#9ca3af", fontSize: 14 }}>
          or click to browse
        </p>
        <input
          type="file"
          accept=".jpg,.jpeg,.png,.pdf"
          onChange={(e) => setFile(e.target.files[0])}
          style={{ margin: "0 auto", display: "block" }}
        />
        {file && (
          <p style={{ color: "#16a34a", marginTop: 10, fontWeight: 500 }}>
            ✓ {file.name} ({(file.size / 1024).toFixed(1)} KB)
          </p>
        )}
      </div>

      {/* Upload button */}
      <button
        onClick={handleUpload}
        disabled={loading || !file}
        style={{
          padding: "11px 32px",
          background: loading || !file ? "#9ca3af" : "#4F46E5",
          color: "white",
          border: "none",
          borderRadius: 8,
          cursor: loading || !file ? "not-allowed" : "pointer",
          fontWeight: 600,
          fontSize: 15,
        }}
      >
        {loading ? "⏳ Processing..." : "Extract Invoice Data"}
      </button>

      {/* Error */}
      {error && (
        <div
          style={{
            marginTop: 16,
            padding: 14,
            background: "#fef2f2",
            border: "1px solid #fca5a5",
            borderRadius: 8,
            color: "#dc2626",
          }}
        >
          ❌ {error}
        </div>
      )}

      {/* Result */}
      {result && (
        <div style={{ marginTop: 28 }}>
          <h3 style={{ color: "#16a34a", marginBottom: 16 }}>
            ✅ Extraction Complete
          </h3>

          {/* Fields grid */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: 12,
              marginBottom: 20,
            }}
          >
            {fields.map(([label, value]) => (
              <div
                key={label}
                style={{
                  padding: 14,
                  background: "#f9fafb",
                  borderRadius: 8,
                  border: "1px solid #e5e7eb",
                }}
              >
                <div
                  style={{
                    fontSize: 11,
                    color: "#6b7280",
                    textTransform: "uppercase",
                    letterSpacing: 0.5,
                  }}
                >
                  {label}
                </div>
                <div style={{ fontWeight: 600, marginTop: 4, fontSize: 15 }}>
                  {/* Result */}
                  {result && (
                    <div style={{ marginTop: 28 }}>
                      {/* Status banner */}
                      {result.extracted.vendor_name ||
                      result.extracted.total_amount ? (
                        <div
                          style={{
                            padding: "12px 16px",
                            background: "#f0fdf4",
                            border: "1px solid #86efac",
                            borderRadius: 8,
                            color: "#16a34a",
                            fontWeight: 600,
                            marginBottom: 20,
                          }}
                        >
                          ✅ Invoice extracted successfully
                        </div>
                      ) : (
                        <div
                          style={{
                            padding: "12px 16px",
                            background: "#fefce8",
                            border: "1px solid #fde047",
                            borderRadius: 8,
                            color: "#854d0e",
                            fontWeight: 600,
                            marginBottom: 20,
                          }}
                        >
                          ⚠️ Invoice uploaded but AI parsing returned no data.
                          This is usually a quota issue — try again later or
                          check your API key.
                        </div>
                      )}

                      {/* Fields grid */}
                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns:
                            "repeat(auto-fit, minmax(200px, 1fr))",
                          gap: 12,
                          marginBottom: 20,
                        }}
                      >
                        {fields.map(([label, value]) => (
                          <div
                            key={label}
                            style={{
                              padding: 14,
                              background: "#f9fafb",
                              borderRadius: 8,
                              border: "1px solid #e5e7eb",
                            }}
                          >
                            <div
                              style={{
                                fontSize: 11,
                                color: "#6b7280",
                                textTransform: "uppercase",
                                letterSpacing: 0.5,
                              }}
                            >
                              {label}
                            </div>
                            <div
                              style={{
                                fontWeight: 600,
                                marginTop: 4,
                                fontSize: 15,
                              }}
                            >
                              {value !== null && value !== undefined ? (
                                value
                              ) : (
                                <span
                                  style={{ color: "#9ca3af", fontWeight: 400 }}
                                >
                                  Not found
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* File info */}
                      <div
                        style={{
                          padding: "10px 14px",
                          background: "#f3f4f6",
                          borderRadius: 8,
                          fontSize: 13,
                          color: "#6b7280",
                        }}
                      >
                        File ID: {result.file_id} | Invoice ID:{" "}
                        {result.invoice_id} | Status: {result.status}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Confidence scores */}
          {result.extracted.confidence_scores &&
            Object.keys(result.extracted.confidence_scores).length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <h4 style={{ marginBottom: 10 }}>Confidence Scores</h4>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {Object.entries(result.extracted.confidence_scores).map(
                    ([field, score]) => (
                      <div
                        key={field}
                        style={{
                          padding: "4px 12px",
                          background:
                            score >= 0.8
                              ? "#dcfce7"
                              : score >= 0.5
                                ? "#fef9c3"
                                : "#fee2e2",
                          color:
                            score >= 0.8
                              ? "#166534"
                              : score >= 0.5
                                ? "#854d0e"
                                : "#991b1b",
                          borderRadius: 20,
                          fontSize: 13,
                          fontWeight: 500,
                        }}
                      >
                        {field}: {(score * 100).toFixed(0)}%
                      </div>
                    ),
                  )}
                </div>
              </div>
            )}

          {/* Line items */}
          {result.extracted.line_items?.length > 0 && (
            <div>
              <h4 style={{ marginBottom: 10 }}>Line Items</h4>
              <table
                style={{
                  width: "100%",
                  borderCollapse: "collapse",
                  fontSize: 14,
                }}
              >
                <thead>
                  <tr style={{ background: "#f3f4f6" }}>
                    {["Description", "Qty", "Unit Price", "Total"].map((h) => (
                      <th
                        key={h}
                        style={{
                          padding: "10px 14px",
                          textAlign: "left",
                          color: "#374151",
                          fontWeight: 600,
                        }}
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.extracted.line_items.map((item, i) => (
                    <tr
                      key={i}
                      style={{
                        borderTop: "1px solid #e5e7eb",
                        background: i % 2 === 0 ? "white" : "#fafafa",
                      }}
                    >
                      <td style={{ padding: "10px 14px" }}>
                        {item.description}
                      </td>
                      <td style={{ padding: "10px 14px" }}>{item.quantity}</td>
                      <td style={{ padding: "10px 14px" }}>
                        {item.unit_price}
                      </td>
                      <td style={{ padding: "10px 14px", fontWeight: 600 }}>
                        {item.total}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
