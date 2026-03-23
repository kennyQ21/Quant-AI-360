"use client";
import { useState, useEffect } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export default function ScannerPage() {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filterScore, setFilterScore] = useState(50);
  const [selectedStock, setSelectedStock] = useState(null);
  const [customSymbols, setCustomSymbols] = useState("nifty50");

  const handleQuickSelect = (idx) => {
    const val = idx.toLowerCase();
    setCustomSymbols(val);
    setTimeout(() => {
      const btn = document.getElementById('scan-button');
      if (btn) btn.click();
    }, 100);
  };

  const runScan = async () => {
    setLoading(true);
    setError(null);
    setScans([]);

    let symbolsToScan = customSymbols;
    const rawVal = customSymbols.trim().toLowerCase();
    const isIndex = ['nifty50', 'nifty 50', 'nifty500', 'nifty 500', 'nifty midcap 200', 'nifty midcap 150', 'nifty smallcap 100'].includes(rawVal);
    
    if (isIndex) {
        try {
            const res = await fetch(`${API}/market/indices/${encodeURIComponent(rawVal)}`);
            if (res.ok) {
                const data = await res.json();
                if (data.symbols && data.symbols.length > 0) {
                    symbolsToScan = data.symbols.join(",");
                }
            }
        } catch (e) {
            console.error("Failed to fetch index symbols", e);
        }
    }

    try {
      const symbolList = symbolsToScan.split(",").map(s => s.trim()).filter(Boolean);
      const chunkSize = 20;
      const chunks = [];
      for (let i = 0; i < symbolList.length; i += chunkSize) {
          chunks.push(symbolList.slice(i, i + chunkSize));
      }
      
      let allScans = [];
      for (const chunk of chunks) {
          const chunkStr = chunk.join(",");
          const response = await fetch(`${API}/scanner/stocks?symbols=${encodeURIComponent(chunkStr)}`);
          if (!response.ok) continue;
          const data = await response.json();
          const newScans = data.scans || [];
          allScans = [...allScans, ...newScans];
          setScans([...allScans]); // Force re-render
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runScan();
  }, []);

  const filteredScans = scans.filter(s => (s.score || 0) >= filterScore);

  const signalColor = (signal) => {
    if (!signal) return "rgba(100,100,100,0.3)";
    if (signal.includes("Full")) return "rgba(100,200,100,0.2)";
    if (signal.includes("AMD") || signal.includes("VCP")) return "rgba(100,150,200,0.2)";
    if (signal.includes("FVG")) return "rgba(150,100,200,0.2)";
    if (signal.includes("Liquidity")) return "rgba(200,150,100,0.2)";
    return "rgba(100,100,100,0.2)";
  };

  const scoreGradient = (score) => {
    if (score >= 75) return "#4CAF50";  // Green
    if (score >= 60) return "#FFC107";  // Yellow
    if (score >= 50) return "#FF9800";  // Orange
    return "#F44336";  // Red
  };

  return (
    <div className="terminal-root">
      {/* Header */}
      <header className="top-bar">
        <div className="top-bar-left">
          <span className="brand">🔍 SCANNER</span>
          <span className="brand-sub">Multi-Stock Setup Detection</span>
        </div>
      </header>

      <div className="terminal-body" style={{ overflowY: "auto", paddingBottom: "20px" }}>
        {/* Control Panel */}
        <div className="card" style={{ margin: "20px" }}>
          <div className="card-header">
            <span className="card-title">⚙️ SCANNER SETTINGS</span>
          </div>
          <div className="card-content" style={{ padding: "16px" }}>
            <div style={{ marginBottom: "16px" }}>
              <label style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-muted)", marginBottom: "8px", display: "block" }}>🎯 QUICK SELECT INDEX:</label>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                {["Nifty 50", "Nifty 500", "Nifty Midcap 150", "Nifty Smallcap 100"].map(idx => {
                   const isActive = customSymbols.toLowerCase() === idx.toLowerCase();
                   return (
                  <button
                    key={idx}
                    onClick={() => handleQuickSelect(idx)}
                    style={{
                      padding: "8px 16px",
                      backgroundColor: isActive ? "var(--accent-blue)" : "rgba(100,100,100,0.1)",
                      color: isActive ? "#fff" : "var(--text-primary)",
                      border: isActive ? "1px solid var(--accent-blue)" : "1px solid rgba(100,100,100,0.4)",
                      borderRadius: "6px",
                      cursor: "pointer",
                      fontSize: "13px",
                      fontWeight: isActive ? 700 : 500,
                      transition: "all 0.2s"
                    }}
                  >
                    {idx}
                  </button>
                )})}
              </div>
            </div>
            <div style={{ marginBottom: "12px" }}>
              <label style={{ fontSize: "12px", fontWeight: 600 }}>Stock Symbols (Index Name or Comma-separated):</label>
              <textarea
                value={customSymbols}
                onChange={(e) => setCustomSymbols(e.target.value)}
                style={{
                  width: "100%",
                  height: "60px",
                  padding: "8px",
                  backgroundColor: "rgba(0,0,0,0.3)",
                  color: "var(--text-primary)",
                  border: "1px solid rgba(100,100,100,0.3)",
                  borderRadius: "4px",
                  fontSize: "11px",
                  fontFamily: "monospace",
                  marginTop: "4px"
                }}
              />
            </div>

            <div style={{ display: "flex", gap: "12px", alignItems: "center", marginBottom: "12px" }}>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: "12px", fontWeight: 600 }}>Min Score:</label>
                <div style={{ display: "flex", gap: "8px", alignItems: "center", marginTop: "4px" }}>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={filterScore}
                    onChange={(e) => setFilterScore(Number(e.target.value))}
                    style={{ flex: 1 }}
                  />
                  <span style={{ fontWeight: 700, color: scoreGradient(filterScore) }}>{filterScore}</span>
                </div>
              </div>
              <button
                id="scan-button"
                onClick={runScan}
                disabled={loading}
                style={{
                  padding: "8px 16px",
                  backgroundColor: loading ? "rgba(100,100,100,0.3)" : "var(--accent-green)",
                  color: "black",
                  border: "none",
                  borderRadius: "4px",
                  cursor: loading ? "not-allowed" : "pointer",
                  fontWeight: 700,
                  fontSize: "12px"
                }}
              >
                {loading ? "Scanning..." : "▶ SCAN"}
              </button>
            </div>

            {error && <div style={{ color: "var(--accent-red)", fontSize: "12px" }}>⚠ {error}</div>}
          </div>
        </div>

        {/* Results Grid */}
        <div style={{ margin: "20px", display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "16px" }}>
          {filteredScans.length > 0 ? (
            filteredScans.map((scan) => (
              <div
                key={scan.symbol}
                onClick={() => setSelectedStock(scan.symbol)}
                style={{
                  padding: "16px",
                  backgroundColor: signalColor(scan.signal),
                  borderRadius: "8px",
                  border: `2px solid ${scoreGradient(scan.score)}`,
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                  transform: selectedStock === scan.symbol ? "scale(1.02)" : "scale(1)",
                  boxShadow: selectedStock === scan.symbol ? `0 0 12px ${scoreGradient(scan.score)}` : "none"
                }}
              >
                <div style={{ marginBottom: "8px" }}>
                  <div style={{ fontSize: "14px", fontWeight: 700 }}>{scan.symbol.replace(".NS", "")}</div>
                  <div style={{ fontSize: "11px", color: "rgba(200,200,200,0.7)" }}>₹{scan.price?.toFixed(2)}</div>
                </div>

                <div style={{
                  padding: "8px",
                  backgroundColor: "rgba(0,0,0,0.3)",
                  borderRadius: "4px",
                  marginBottom: "8px"
                }}>
                  <div style={{ fontSize: "11px", fontWeight: 600, marginBottom: "4px" }}>{scan.signal}</div>
                  <div style={{
                    fontSize: "13px",
                    fontWeight: 700,
                    color: scoreGradient(scan.score)
                  }}>
                    Score: {Math.round(scan.score)}/100
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px", fontSize: "10px" }}>
                  <div>
                    <span style={{ display: "block", color: "rgba(200,200,200,0.6)" }}>Entry</span>
                    <span style={{ fontWeight: 600 }}>₹{scan.entry?.toFixed(2)}</span>
                  </div>
                  <div>
                    <span style={{ display: "block", color: "rgba(200,200,200,0.6)" }}>SL</span>
                    <span style={{ fontWeight: 600 }}>₹{scan.stop_loss?.toFixed(2)}</span>
                  </div>
                  <div>
                    <span style={{ display: "block", color: "rgba(200,200,200,0.6)" }}>T1</span>
                    <span style={{ fontWeight: 600 }}>₹{scan.target1?.toFixed(2)}</span>
                  </div>
                  <div>
                    <span style={{ display: "block", color: "rgba(200,200,200,0.6)" }}>T2</span>
                    <span style={{ fontWeight: 600 }}>₹{scan.target2?.toFixed(2)}</span>
                  </div>
                </div>

                <div style={{
                  marginTop: "8px",
                  paddingTop: "8px",
                  borderTop: "1px solid rgba(100,100,100,0.2)",
                  fontSize: "10px",
                  fontWeight: 600,
                  color: scan.direction === "LONG" ? "var(--accent-green)" : "var(--accent-red)"
                }}>
                  {scan.direction === "LONG" ? "▲" : "▼"} {scan.direction}
                </div>
              </div>
            ))
          ) : (
            <div style={{ gridColumn: "1 / -1", textAlign: "center", padding: "40px", color: "rgba(200,200,200,0.6)" }}>
              {scans.length === 0 ? "Run scanner to find setups" : "No setups match the score filter"}
            </div>
          )}
        </div>

        {/* Stock Details if Selected */}
        {selectedStock && (
          <div style={{ margin: "20px", padding: "16px", backgroundColor: "rgba(100,100,100,0.1)", borderRadius: "8px" }}>
            <div style={{ fontSize: "14px", fontWeight: 700, marginBottom: "12px" }}>
              Selected: {selectedStock} — <a href={`/?symbol=${selectedStock}`} style={{ color: "var(--accent-blue)", textDecoration: "none" }}>View Full Analysis →</a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
