import React, { useState, useEffect } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export default function PriceActionPanel({ symbol }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedDetector, setExpandedDetector] = useState("confluence");

  useEffect(() => {
    if (!symbol) return;
    
    setLoading(true);
    fetch(`${API}/stock/${symbol}/price-action`)
      .then(r => r.json())
      .then(d => { setData(d); setError(null); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [symbol]);

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;
  if (error) return <div className="error-box">⚠ {error}</div>;
  if (!data) return <div className="card"><div className="card-content">Loading price action...</div></div>;

  const conf = data.confluence || {};
  const scoreColor = conf.score >= 75 ? "var(--accent-green)" : conf.score >= 50 ? "var(--accent-yellow)" : "var(--accent-red)";

  const DetectorSection = ({ title, key, detector, icon }) => {
    const isExpanded = expandedDetector === key;
    const isActive = detector && !detector.error;

    return (
      <div style={{ marginBottom: "8px", borderRadius: "4px", overflow: "hidden" }}>
        <div
          onClick={() => setExpandedDetector(isExpanded ? null : key)}
          style={{
            padding: "10px 12px",
            backgroundColor: "rgba(100,200,100,0.1)",
            borderLeft: `3px solid ${isActive ? "var(--accent-green)" : "var(--accent-red)"}`,
            cursor: "pointer",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            fontSize: "12px",
            fontWeight: 600
          }}
        >
          <span>{icon} {title}</span>
          <span style={{ fontSize: "10px" }}>{isExpanded ? "▼" : "▶"}</span>
        </div>
        {isExpanded && detector && (
          <div style={{
            padding: "10px",
            backgroundColor: "rgba(0,0,0,0.3)",
            fontSize: "11px",
            lineHeight: "1.6",
            borderTop: "1px solid rgba(100,100,100,0.2)"
          }}>
            {detector.error ? (
              <div style={{ color: "var(--accent-red)" }}>Error: {detector.error}</div>
            ) : (
              <pre style={{ fontSize: "10px", overflow: "auto", maxHeight: "200px" }}>
                {JSON.stringify(detector, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="card" style={{ gridColumn: "3 / 4", height: "fit-content" }}>
      <div className="card-header">
        <span className="card-title">🎯 PRICE ACTION</span>
      </div>
      <div className="card-content" style={{ padding: "12px", fontSize: "12px" }}>
        {/* Confluence Setup - Always Visible */}
        <div style={{
          padding: "12px",
          backgroundColor: "rgba(100,100,100,0.2)",
          borderRadius: "4px",
          marginBottom: "12px",
          border: `2px solid ${scoreColor}`
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
            <span style={{ fontWeight: 700 }}>⚡ {conf.signal_name || "No Setup"}</span>
            <span style={{ fontSize: "14px", fontWeight: 700, color: scoreColor }}>
              {Math.round(conf.score || 0)}/100
            </span>
          </div>
          {conf.direction && (
            <>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "11px" }}>
                <div>Dir: {conf.direction}</div>
                <div>E: ₹{conf.entry_price?.toFixed(2)}</div>
                <div>SL: ₹{conf.stop_loss?.toFixed(2)}</div>
                <div>T1: ₹{conf.target1?.toFixed(2)}</div>
              </div>
              {conf.breakdown && (
                <div style={{ marginTop: "8px", fontSize: "10px", color: "rgba(200,200,200,0.7)" }}>
                  {conf.breakdown}
                </div>
              )}
            </>
          )}
        </div>

        {/* Detector Sections */}
        <div style={{ fontSize: "10px", marginBottom: "16px" }}>
          <DetectorSection title="Order Flow" key="order_flow" detector={data.order_flow} icon="📊" />
          <DetectorSection title="Liquidity" key="liquidity" detector={data.liquidity} icon="💧" />
          <DetectorSection title="Fair Value Gap" key="fvg" detector={data.fvg} icon="⬜" />
          <DetectorSection title="Inverse FVG" key="ifvg" detector={data.ifvg} icon="⬛" />
          <DetectorSection title="AMD Model" key="amd" detector={data.amd} icon="📈" />
          <DetectorSection title="VCP Pattern" key="vcp" detector={data.vcp} icon="🔶" />
          <DetectorSection title="Breakout" key="breakout" detector={data.breakout} icon="🚀" />
        </div>

        <Link
          href={`/stock/${symbol}/price-action`}
          style={{
            display: "block",
            textAlign: "center",
            padding: "10px",
            backgroundColor: "#238636",
            color: "white",
            textDecoration: "none",
            borderRadius: "4px",
            fontWeight: "bold",
            fontSize: "12px"
          }}
        >
          🔍 Examine Detailed Strategy
        </Link>
      </div>
    </div>
  );
}
