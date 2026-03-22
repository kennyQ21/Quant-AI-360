"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { createChart, CandlestickSeries, LineSeries, HistogramSeries, AreaSeries } from "lightweight-charts";
import StockSearch from "./components/StockSearch";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function apiFetch(path) {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

function Loading() {
  return <div className="loading-spinner"><div className="spinner" /></div>;
}

function ErrorBox({ msg }) {
  return <div className="error-box">⚠ {msg}</div>;
}

export default function Home() {
  const [symbol, setSymbol] = useState("RELIANCE.NS");
  const [inputSymbol, setInputSymbol] = useState("RELIANCE.NS");
  const [candles, setCandles] = useState([]);
  const [a, setA] = useState(null);  // analysis
  const [loading, setLoading] = useState({ candles: false, analysis: false });
  const [errors, setErrors] = useState({ candles: null, analysis: null });

  const fetchAll = useCallback(async (sym) => {
    setLoading({ candles: true, analysis: true });
    setErrors({ candles: null, analysis: null });
    setA(null);

    // Fetch candle data
    apiFetch(`/stock/${sym}?period=6mo`)
      .then(d => setCandles(d.candles || d.data || []))
      .catch(e => setErrors(prev => ({ ...prev, candles: e.message })))
      .finally(() => setLoading(prev => ({ ...prev, candles: false })));

    // Fetch 360 analysis
    apiFetch(`/stock/${sym}/analysis-360`)
      .then(d => setA(d))
      .catch(e => setErrors(prev => ({ ...prev, analysis: e.message })))
      .finally(() => setLoading(prev => ({ ...prev, analysis: false })));
  }, []);

  useEffect(() => { fetchAll(symbol); }, [symbol, fetchAll]);

  const handleSearch = (sym) => {
    setSymbol(sym);
    setInputSymbol(sym);
  };

  const handleRefresh = () => fetchAll(symbol);

  const changeColor = a?.change_pct >= 0 ? "var(--accent-green)" : "var(--accent-red)";

  return (
    <div className="terminal-root">
      {/* ── TOP BAR ── */}
      <header className="top-bar">
        <div className="top-bar-left">
          <span className="brand">⚡ QUANT AI 360</span>
          <span className="brand-sub">Elite Trading Terminal</span>
        </div>
        <div className="top-bar-center">
          <StockSearch onSelect={handleSearch} />
          <button className="refresh-btn" onClick={handleRefresh} title="Refresh">↻</button>
        </div>
        <div className="top-bar-right">
          {a && (
            <>
              <span className="ticker-symbol">{a.symbol}</span>
              <span className="ticker-price">₹{a.price?.toLocaleString("en-IN")}</span>
              <span style={{ color: changeColor, fontWeight: 700, fontSize: "16px" }}>
                {a.change_pct >= 0 ? "▲" : "▼"} {Math.abs(a.change_pct || 0).toFixed(2)}%
              </span>
            </>
          )}
        </div>
      </header>

      <div className="terminal-body">
        {/* ── LEFT COLUMN ── */}
        <aside className="left-col">
          {/* Watchlist */}
          <div className="card">
            <div className="card-header"><span className="card-title">📋 WATCHLIST</span></div>
            <div className="card-content" style={{ padding: "16px" }}>
              {["RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS","SBIN.NS","BHARTIARTL.NS"].map(s => (
                <div key={s} onClick={() => handleSearch(s)}
                  className={`watchlist-item${s === symbol ? " active" : ""}`}>
                  {s.replace(".NS", "")}
                </div>
              ))}
            </div>
          </div>
        </aside>

        {/* ── CENTER COLUMN ── */}
        <main className="center-col">
          {/* Chart */}
          <div className="card chart-card">
            <div className="card-header">
              <span className="card-title">📊 {symbol} — Price Chart</span>
              {a && <span style={{ fontSize: "18px", color: "var(--text-muted)" }}>{a.company_name}</span>}
            </div>
            <ChartPanel symbol={symbol} />
          </div>

          {/* Stock Story */}
          <div className="card story-card">
            <div className="card-header">
              <span className="card-title" style={{ color: "var(--accent-purple)", fontWeight: "800" }}>🧠 STOCK STORY</span>
            </div>
            <div className="card-content" style={{ fontSize: "16px", color: "var(--text-primary)", lineHeight: "1.65" }}>
              {loading.analysis ? <Loading /> : errors.analysis ? <ErrorBox msg={errors.analysis} /> :
                a?.story_sections ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                    {[
                      { icon: "📐", label: "Structure", key: "structure" },
                      { icon: "🔶", label: "Fibonacci", key: "fibonacci" },
                      { icon: "💧", label: "Liquidity", key: "liquidity" },
                      { icon: "📉", label: "Rel. Strength", key: "relative_strength" },
                      { icon: "⚡", label: "Conclusion", key: "conclusion" },
                    ].map(({ icon, label, key }) => (
                      <div key={key} style={{ display: "flex", gap: "24px", alignItems: "flex-start" }}>
                        <span style={{ fontSize: "18px", minWidth: "16px", marginTop: "1px" }}>{icon}</span>
                        <div>
                          <span style={{ fontSize: "16px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.8px", marginRight: "6px" }}>{label}</span>
                          <span style={{ color: key === "conclusion" ? "var(--text-primary)" : "var(--text-secondary)" }}>{a.story_sections[key] || "—"}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : <div className="text-muted">Analyzing structure...</div>
              }
            </div>
          </div>

          {/* High Probability Zone */}
          <div className="card confluence-card">
            <div className="card-header">
              <span className="card-title" style={{ color: "var(--accent-yellow)", fontWeight: "800" }}>🔥 HIGH PROBABILITY ZONE</span>
            </div>
            <div className="card-content">
              {loading.analysis ? <Loading /> : errors.analysis ? <ErrorBox msg={errors.analysis} /> : a && (
                <>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
                    <div>
                      <div style={{ fontSize: "16px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "2px" }}>Confluence Score</div>
                      <span style={{ fontSize: "36px", fontWeight: "900", color: (a.trade_quality?.score ?? 0) >= 7 ? "var(--accent-green)" : (a.trade_quality?.score ?? 0) >= 4 ? "var(--accent-yellow)" : "var(--accent-red)" }}>
                        {a.trade_quality?.score ?? 0}<span style={{ fontSize: "17px", color: "var(--text-muted)" }}>/10</span>
                      </span>
                    </div>
                    <span style={{ padding: "8px 16px", borderRadius: "20px", fontSize: "18px", fontWeight: "800",
                      background: a.fibonacci?.confidence === "High" ? "rgba(16,185,129,0.15)" : a.fibonacci?.confidence === "Medium" ? "rgba(234,179,8,0.15)" : "rgba(239,68,68,0.15)",
                      color: a.fibonacci?.confidence === "High" ? "var(--accent-green)" : a.fibonacci?.confidence === "Medium" ? "var(--accent-yellow)" : "var(--accent-red)" }}>
                      {(a.fibonacci?.confidence || "LOW").toUpperCase()}
                    </span>
                  </div>

                  {a.fibonacci?.zone === "failed_retracement" ? (
                    <div style={{ padding: "16px 20px", background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.4)", borderRadius: "var(--radius-sm)", color: "var(--accent-red)", fontSize: "18px", marginBottom: "24px" }}>
                      <strong>⚠️ Fib Failure</strong> — Break below 0.786 confirmed. Structural breakdown expected.
                    </div>
                  ) : a.fibonacci?.zone && a.fibonacci.zone !== "unknown" ? (
                    <div style={{ padding: "16px 20px", background: "rgba(234,179,8,0.10)", border: "1px solid rgba(234,179,8,0.3)", borderRadius: "var(--radius-sm)", marginBottom: "24px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ color: "var(--accent-yellow)", fontWeight: "700", fontSize: "18px" }}>📍 {a.fibonacci.zone.replace(/_/g, " ").toUpperCase()}</span>
                      {a.fibonacci?.levels && <span style={{ color: "var(--text-muted)", fontSize: "17px" }}>₹{Math.round(a.fibonacci.levels["0.618"])} – ₹{Math.round(a.fibonacci.levels["0.5"])}</span>}
                    </div>
                  ) : null}

                  <div style={{ fontSize: "17px", fontWeight: "700", color: "var(--text-muted)", marginBottom: "12px", textTransform: "uppercase", letterSpacing: "1px" }}>Weighted Breakdown</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "14px", marginBottom: "24px" }}>
                    {a.confluence_breakdown ? Object.entries(a.confluence_breakdown).map(([key, v]) => (
                      <div key={key} style={{ display: "flex", alignItems: "center", gap: "24px", fontSize: "18px" }}>
                        <span style={{ color: v.earned > 0 ? "var(--accent-green)" : "var(--accent-red)", fontSize: "16px", minWidth: "10px" }}>{v.earned > 0 ? "✔" : "✖"}</span>
                        <span style={{ textTransform: "capitalize", color: "var(--text-muted)", minWidth: "70px" }}>{key}:</span>
                        <div style={{ flex: 1, height: "3px", background: "var(--border-color)", borderRadius: "2px" }}>
                          <div style={{ height: "100%", width: `${(v.earned / v.max) * 100}%`, background: v.earned > 0 ? "var(--accent-green)" : "transparent", borderRadius: "2px" }} />
                        </div>
                        <span style={{ color: v.earned > 0 ? "var(--text-primary)" : "var(--text-muted)", minWidth: "28px", textAlign: "right" }}>{v.earned}/{v.max}</span>
                        <span style={{ color: "var(--text-muted)", fontSize: "16px", }}>{v.label}</span>
                      </div>
                    )) : null}
                  </div>

                  {a.fibonacci?.high && a.fibonacci?.low && (
                    <div style={{ padding: "16px", background: "rgba(255,255,255,0.04)", borderRadius: "var(--radius-sm)", fontSize: "17px", color: "var(--text-muted)", marginBottom: "20px" }}>
                      <span style={{ fontWeight: "700" }}>Swing:&nbsp;</span>₹{Math.round(a.fibonacci.high)} → ₹{Math.round(a.fibonacci.low)}
                      {a.fibonacci?.levels && <span style={{ marginLeft: "12px" }}><span style={{ fontWeight: "700" }}>Golden Zone:&nbsp;</span>₹{Math.round(a.fibonacci.levels["0.618"])} – ₹{Math.round(a.fibonacci.levels["0.5"])}</span>}
                    </div>
                  )}
                  <div style={{ paddingTop: "16px", borderTop: "1px dashed var(--border-color)", fontSize: "18px", color: "var(--text-secondary)", fontStyle: "italic", lineHeight: "1.6" }}>
                    {a.fibonacci?.interpretation || "Awaiting structural data."}
                  </div>
                </>
              )}
            </div>
          </div>
        </main>

        {/* ── RIGHT COLUMN ── */}
        <aside className="right-col">
          {/* Decision Context */}
          <div className="card" style={{ borderTop: "3px solid var(--accent-purple)" }}>
            <div className="card-header"><span className="card-title">🧭 DECISION CONTEXT</span></div>
            <div className="card-content">
              {loading.analysis ? <Loading /> : errors.analysis ? <ErrorBox msg={errors.analysis} /> : a?.decision_context ? (
                <div>
                  <div style={{ display: "flex", gap: "24px", marginBottom: "24px", flexWrap: "wrap" }}>
                    <span style={{ padding: "8px 16px", borderRadius: "20px", fontSize: "17px", fontWeight: "700",
                      background: a.decision_context.bias === "Bearish" ? "rgba(239,68,68,0.15)" : a.decision_context.bias?.includes("Bullish") ? "rgba(16,185,129,0.15)" : "rgba(234,179,8,0.15)",
                      color: a.decision_context.bias === "Bearish" ? "var(--accent-red)" : a.decision_context.bias?.includes("Bullish") ? "var(--accent-green)" : "var(--accent-yellow)" }}>
                      {a.decision_context.bias}
                    </span>
                    <span style={{ padding: "8px 16px", borderRadius: "20px", fontSize: "17px", fontWeight: "700", background: "rgba(255,255,255,0.05)", color: "var(--text-muted)" }}>
                      {a.decision_context.setup_quality} ({a.decision_context.score}/10)
                    </span>
                    <span style={{ padding: "8px 16px", borderRadius: "20px", fontSize: "17px", fontWeight: "700",
                      background: a.decision_context.risk === "High" ? "rgba(239,68,68,0.15)" : "rgba(255,255,255,0.05)",
                      color: a.decision_context.risk === "High" ? "var(--accent-red)" : "var(--text-muted)" }}>
                      Risk: {a.decision_context.risk}
                    </span>
                  </div>
                  <div style={{ fontSize: "16px", color: "var(--text-primary)", fontWeight: "600", marginBottom: "12px", lineHeight: "1.5" }}>
                    {a.decision_context.recommendation}
                  </div>
                  <div style={{ fontSize: "17px", color: "var(--text-muted)", fontStyle: "italic", paddingTop: "16px", borderTop: "1px dashed var(--border-color)" }}>
                    {a.decision_context.action_threshold}
                  </div>
                </div>
              ) : <div className="text-muted">Awaiting analysis.</div>}
            </div>
          </div>

          {/* Trade Quality */}
          <div className="card" style={{ borderTop: "2px solid var(--accent-blue)" }}>
            <div className="card-header"><span className="card-title">📊 Trade Quality</span></div>
            <div className="card-content">
              {loading.analysis ? <Loading /> : errors.analysis ? <ErrorBox msg={errors.analysis} /> : a?.trade_quality ? (
                <div>
                  {[
                    { label: "Signal", value: a.trade_quality.signal_strength },
                    { label: "Risk", value: a.trade_quality.risk },
                    { label: "Clarity", value: a.trade_quality.clarity },
                  ].map(({ label, value }) => (
                    <div key={label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
                      <span style={{ fontSize: "18px", color: "var(--text-muted)" }}>{label}</span>
                      <span style={{ fontSize: "18px", fontWeight: "700", padding: "2px 8px", borderRadius: "4px",
                        background: value === "Strong" || value === "Low" || value === "Clear" ? "rgba(16,185,129,0.15)" : value === "High" ? "rgba(239,68,68,0.15)" : "rgba(234,179,8,0.15)",
                        color: value === "Strong" || value === "Low" || value === "Clear" ? "var(--accent-green)" : value === "High" ? "var(--accent-red)" : "var(--accent-yellow)" }}>
                        {value}
                      </span>
                    </div>
                  ))}
                  <div style={{ fontSize: "18px", color: "var(--text-secondary)", fontStyle: "italic", borderTop: "1px dashed var(--border-color)", paddingTop: "16px" }}>
                    {a.trade_quality.interpretation}
                  </div>
                </div>
              ) : null}
            </div>
          </div>

          {/* Relative Strength */}
          <div className="card" style={{ borderTop: "2px solid var(--accent-purple)" }}>
            <div className="card-header"><span className="card-title">📈 Relative Strength</span></div>
            <div className="card-content">
              {loading.analysis ? <Loading /> : errors.analysis ? <ErrorBox msg={errors.analysis} /> : a?.relative_strength ? (
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "16px" }}>
                    <div>
                      <div style={{ fontSize: "16px", color: "var(--text-muted)", textTransform: "uppercase" }}>vs NIFTY (3M)</div>
                      <span style={{ fontSize: "36px", fontWeight: "800", color: a.relative_strength.outperforming ? "var(--accent-green)" : "var(--accent-red)" }}>
                        {a.relative_strength.outperforming ? "+" : ""}{a.relative_strength.rs_ratio}%
                      </span>
                    </div>
                    <span style={{ alignSelf: "flex-end", fontSize: "18px", fontWeight: "700",
                      color: a.relative_strength.outperforming ? "var(--accent-green)" : "var(--accent-red)" }}>
                      {a.relative_strength.outperforming ? "▲ OUTPERFORMING" : "▼ UNDERPERFORMING"}
                    </span>
                  </div>
                  <div style={{ fontSize: "18px", color: "var(--text-secondary)", fontStyle: "italic", borderTop: "1px dashed var(--border-color)", paddingTop: "16px", lineHeight: "1.6" }}>
                    {a.relative_strength.interpretation}
                  </div>
                </div>
              ) : null}
            </div>
          </div>

          {/* Market Impact */}
          <div className="card" style={{ borderTop: "2px solid var(--accent-red)" }}>
            <div className="card-header"><span className="card-title">🌍 Market Impact</span></div>
            <div className="card-content">
              {loading.analysis ? <Loading /> : errors.analysis ? <ErrorBox msg={errors.analysis} /> : a && (
                <div>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "24px" }}>
                      <span style={{ fontSize: "18px", fontWeight: "800", color: a.market_context?.regime === "Bearish" ? "var(--accent-red)" : a.market_context?.regime === "Bullish" ? "var(--accent-green)" : "var(--accent-yellow)" }}>
                        {a.market_context?.regime || "UNKNOWN"}
                      </span>
                      <span style={{ fontSize: "18px", color: "var(--text-muted)", background: "rgba(255,255,255,0.05)", padding: "2px 8px", borderRadius: "4px", border: "1px solid var(--border-color)" }}>
                        Vol: {a.market_context?.volatility || "—"}
                      </span>
                    </div>
                    {a.market_alignment && (
                      <div style={{ textAlign: "right" }}>
                        <div style={{ fontSize: "9px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.8px" }}>Alignment</div>
                        <span style={{ fontSize: "16px", fontWeight: "800", color: a.market_alignment.score >= 4 ? "var(--accent-green)" : a.market_alignment.score >= 2 ? "var(--accent-yellow)" : "var(--accent-red)" }}>
                          {a.market_alignment.score}<span style={{ fontSize: "17px", color: "var(--text-muted)" }}>/{a.market_alignment.max}</span>
                        </span>
                      </div>
                    )}
                  </div>
                  <div style={{ fontSize: "18px", color: "var(--text-muted)", marginBottom: "16px" }}>Sector: {a.market_context?.sector || "—"}</div>
                  <div style={{ fontSize: "18px", color: "var(--text-secondary)", fontStyle: "italic", borderTop: "1px dashed var(--border-color)", paddingTop: "16px", lineHeight: "1.6" }}>
                    {a.market_alignment?.interpretation || a.market_context?.interpretation || "Awaiting macroeconomic inputs."}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* News */}
          <div className="card" style={{ borderTop: "2px solid var(--accent-blue)" }}>
            <div className="card-header">
              <span className="card-title">📰 News</span>
              {a?.sentiment && (
                <span style={{ fontSize: "17px", fontWeight: "700", padding: "2px 8px", borderRadius: "4px",
                  background: a.sentiment.label === "Bullish" ? "rgba(16,185,129,0.15)" : a.sentiment.label === "Bearish" ? "rgba(239,68,68,0.15)" : "rgba(255,255,255,0.05)",
                  color: a.sentiment.label === "Bullish" ? "var(--accent-green)" : a.sentiment.label === "Bearish" ? "var(--accent-red)" : "var(--text-muted)" }}>
                  {a.sentiment.label}
                </span>
              )}
            </div>
            <div className="card-content">
              {loading.analysis ? <Loading /> : errors.analysis ? <ErrorBox msg={errors.analysis} /> :
                (a?.news?.headlines?.length > 0) ? a.news.headlines.map((h, i) => (
                  <div key={i} style={{ fontSize: "18px", color: "var(--text-secondary)", padding: "6px 0", borderBottom: "1px solid var(--border-color)", lineHeight: "1.4" }}>{h}</div>
                )) : <div className="text-muted">No recent news available.</div>
              }
            </div>
          </div>

          {/* Scenarios */}
          <div className="card" style={{ borderTop: "2px solid var(--accent-green)" }}>
            <div className="card-header"><span className="card-title">🔮 Scenarios</span></div>
            <div className="card-content">
              {loading.analysis ? <Loading /> : errors.analysis ? <ErrorBox msg={errors.analysis} /> :
                (a?.scenarios?.length > 0) ? a.scenarios.map((s, i) => (
                  <div key={i} style={{ marginBottom: "24px", padding: "10px", background: "rgba(255,255,255,0.04)", borderRadius: "var(--radius-sm)", border: `1px solid ${s.type === "Bull" ? "rgba(16,185,129,0.3)" : s.type === "Bear" ? "rgba(239,68,68,0.3)" : "rgba(255,255,255,0.1)"}` }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                      <span style={{ fontSize: "18px", fontWeight: "700", color: s.type === "Bull" ? "var(--accent-green)" : s.type === "Bear" ? "var(--accent-red)" : "var(--text-muted)" }}>
                        {s.type === "Bull" ? "🟢" : s.type === "Bear" ? "🔴" : "⚪"} {s.type}
                      </span>
                      <span style={{ fontSize: "17px", fontWeight: "700", color: "var(--text-muted)" }}>{s.probability}%</span>
                    </div>
                    <div style={{ fontSize: "17px", color: "var(--text-secondary)", lineHeight: "1.5" }}>{s.description}</div>
                    {s.trigger && <div style={{ fontSize: "16px", color: "var(--accent-yellow)", marginTop: "4px", fontStyle: "italic" }}>Trigger: {s.trigger}</div>}
                  </div>
                )) : <div className="text-muted">Awaiting scenario data.</div>
              }
            </div>
          </div>

        </aside>
      </div>
    </div>
  );
}

/* ── Candlestick Chart Panel ── */
function ChartPanel({ symbol }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    const c = createChart(containerRef.current, {
      layout: { background: { color: "#0d1117" }, textColor: "#8b949e" },
      grid: { vertLines: { color: "#21262d" }, horzLines: { color: "#21262d" } },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: "#30363d" },
      timeScale: { borderColor: "#30363d", timeVisible: true },
      width: containerRef.current.clientWidth,
      height: 420,
    });
    chartRef.current = c;

    const series = c.addCandlestickSeries({
      upColor: "#26a69a", downColor: "#ef5350",
      borderUpColor: "#26a69a", borderDownColor: "#ef5350",
      wickUpColor: "#26a69a", wickDownColor: "#ef5350",
    });

    fetch(`${API}/stock/${symbol}?period=6mo`)
      .then(r => r.json())
      .then(d => {
        const rows = (d.candles || d.data || [])
          .filter(r => r.open && r.high && r.low && r.close)
          .map(r => ({
            time: typeof r.time === "number" ? r.time : Math.floor(new Date(r.date || r.time).getTime() / 1000),
            open: r.open, high: r.high, low: r.low, close: r.close
          }))
          .sort((a, b) => a.time - b.time);
        if (rows.length > 0) series.setData(rows);
        c.timeScale().fitContent();
      })
      .catch(() => {});

    const ro = new ResizeObserver(() => {
      if (containerRef.current && chartRef.current)
        chartRef.current.applyOptions({ width: containerRef.current.clientWidth });
    });
    ro.observe(containerRef.current);
    return () => { ro.disconnect(); if (chartRef.current) { chartRef.current.remove(); chartRef.current = null; } };
  }, [symbol]);

  return <div ref={containerRef} style={{ width: "100%", height: "420px" }} />;
}
