"use client";

import { useEffect, useState, useRef } from "react";
import { createChart } from "lightweight-charts";

export default function PortfolioPage() {
  const [metrics, setMetrics] = useState(null);
  const [trades, setTrades] = useState([]);
  const [curve, setCurve] = useState([]);
  const [loading, setLoading] = useState(true);
  const chartContainerRef = useRef(null);

  useEffect(() => {
    async function loadPnL() {
      try {
        const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
        const res = await fetch(`${API}/portfolio/pnl`);
        const data = await res.json();
        setMetrics(data.metrics);
        setTrades(data.recent_trades);
        setCurve(data.equity_curve);
      } catch (err) {
        console.error("Failed to load PnL details", err);
      } finally {
        setLoading(false);
      }
    }
    loadPnL();
  }, []);

  useEffect(() => {
    if (!chartContainerRef.current || curve.length === 0) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 350,
      layout: {
        background: { type: 'solid', color: 'transparent' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: 'rgba(42, 46, 57, 0.5)' },
        horzLines: { color: 'rgba(42, 46, 57, 0.5)' },
      },
      timeScale: {
        timeVisible: true,
      }
    });

    const lineSeries = chart.addLineSeries({
      color: '#ff00ff', // magenta theme
      lineWidth: 2,
    });

    // map the curve data to match lightweight-charts {time, value}
    // ensure time is a string (YYYY-MM-DD) or timestamp
    const formattedData = curve.map(c => {
      // Return exactly as needed by lightweight-charts
      return { time: c.time, value: c.value };
    }).filter(c => c.time);
    
    // Sort by time just in case
    formattedData.sort((a,b) => new Date(a.time) - new Date(b.time));

    // Also deduplicate dates for lightweight-charts
    const uniqueFormatted = [];
    const seen = new Set();
    for (const item of formattedData) {
        const d = item.time.split(" ")[0]; // Just take YYYY-MM-DD
        if (!seen.has(d)) {
            seen.add(d);
            uniqueFormatted.push({ time: d, value: item.value });
        }
    }

    lineSeries.setData(uniqueFormatted);

    return () => {
      chart.remove();
    };
  }, [curve]);

  return (
    <div className="terminal-root" style={{ padding: "20px" }}>
      <header className="top-bar" style={{ marginBottom: "20px" }}>
        <div className="top-bar-left">
          <span className="brand">⚡ QUANT AI 360</span>
          <span className="brand-sub">Portfolio PnL</span>
        </div>
        <div className="top-bar-center">
          <a href="/" style={{ marginRight: "12px", color: "var(--accent-blue)" }}>← Back to Dashboard</a>
        </div>
      </header>

      {loading && <p>Loading PnL data...</p>}
      
      {!loading && metrics && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr 1fr", gap: "15px", marginBottom: "20px" }}>
          <div className="price-card">
            <div className="label">Total Return</div>
            <div className="value" style={{ color: metrics.total_return_pct >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
              {metrics.total_return_pct.toFixed(2)}%
            </div>
          </div>
          <div className="price-card">
            <div className="label">Win Rate</div>
            <div className="value">{metrics.win_rate.toFixed(2)}%</div>
          </div>
          <div className="price-card">
            <div className="label">Profit Factor</div>
            <div className="value">{metrics.profit_factor.toFixed(2)}</div>
          </div>
          <div className="price-card">
            <div className="label">Total Trades</div>
            <div className="value">{metrics.total_trades}</div>
          </div>
          <div className="price-card">
            <div className="label">Avg Win</div>
            <div className="value" style={{ color: 'var(--accent-green)' }}>{metrics.avg_win_pct.toFixed(2)}%</div>
          </div>
           <div className="price-card">
            <div className="label">Avg Loss</div>
            <div className="value" style={{ color: 'var(--accent-red)' }}>{metrics.avg_loss_pct.toFixed(2)}%</div>
          </div>
        </div>
      )}

      {!loading && (
        <div className="chart-panel" style={{ padding: "15px", marginBottom: "20px", height: "400px" }}>
           <h3 style={{ margin: "0 0 10px 0", color: "#fff", fontSize: "14px", borderBottom: "1px solid #333", paddingBottom: "10px" }}>System Equity Curve (Base = 100)</h3>
           {curve.length > 0 ? (
               <div ref={chartContainerRef} style={{ width: "100%", height: "350px" }} />
           ) : (
               <p>No equity curve data available</p>
           )}
        </div>
      )}

      {!loading && trades.length > 0 && (
        <div className="chart-panel" style={{ padding: "15px" }}>
          <h3 style={{ margin: "0 0 10px 0", color: "#fff", fontSize: "14px", borderBottom: "1px solid #333", paddingBottom: "10px" }}>Recent Trades</h3>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
            <thead>
              <tr style={{ background: "#1a1a1a", textAlign: "left" }}>
                <th style={{ padding: "8px", borderBottom: "1px solid #333" }}>Date</th>
                <th style={{ padding: "8px", borderBottom: "1px solid #333" }}>Stock</th>
                <th style={{ padding: "8px", borderBottom: "1px solid #333" }}>Strategy</th>
                <th style={{ padding: "8px", borderBottom: "1px solid #333" }}>Direction</th>
                <th style={{ padding: "8px", borderBottom: "1px solid #333" }}>Return</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((t, idx) => (
                <tr key={idx} style={{ borderBottom: "1px solid #222" }}>
                  <td style={{ padding: "8px" }}>{t.exit_date || t.entry_date}</td>
                  <td style={{ padding: "8px", fontWeight: "bold" }}>{t.symbol}</td>
                  <td style={{ padding: "8px", color: "var(--accent-blue)" }}>{t.setup}</td>
                  <td style={{ padding: "8px" }}>{t.direction}</td>
                  <td style={{ padding: "8px", color: t.profit_loss_pct >= 0 ? "var(--accent-green)" : "var(--accent-red)" }}>
                    {t.profit_loss_pct?.toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}