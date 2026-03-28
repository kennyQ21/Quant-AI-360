"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { createChart } from "lightweight-charts";
import StockSearch from "./components/StockSearch";
import PriceActionPanel from "./components/PriceActionPanel";

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

function ChartPanel({ symbol, companyName }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const [period, setPeriod] = useState("2y");
  
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
      height: 500,
    });
    chartRef.current = c;

    const series = c.addCandlestickSeries({
      upColor: "#26a69a", downColor: "#ef5350",
      borderUpColor: "#26a69a", borderDownColor: "#ef5350",
      wickUpColor: "#26a69a", wickDownColor: "#ef5350",
    });

    const volSeries = c.addHistogramSeries({
      color: '#26a69a',
      priceFormat: { type: 'volume' },
      priceScaleId: '',
    });
    
    c.priceScale('').applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    fetch(`${API}/stock/${symbol}?period=${period}`)
      .then(r => r.json())
      .then(d => {
        const rows = (d.candles || d.data || [])
          .filter(r => r.open && r.high && r.low && r.close)
          .map(r => ({
            time: typeof r.time === "number" ? r.time : Math.floor(new Date(r.date || r.time).getTime() / 1000),
            open: r.open, high: r.high, low: r.low, close: r.close,
            value: r.volume || 0,
            color: r.close >= r.open ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)'
          }))
          .sort((a, b) => a.time - b.time);
          
        if (rows.length > 0) {
          series.setData(rows);
          volSeries.setData(rows.map(r => ({ time: r.time, value: r.value, color: r.color })));
        }
        c.timeScale().fitContent();
      })
      .catch(() => {});

    const ro = new ResizeObserver(() => {
      if (containerRef.current && chartRef.current)
        chartRef.current.applyOptions({ width: containerRef.current.clientWidth });
    });
    ro.observe(containerRef.current);
    
    return () => ro.disconnect();
  }, [symbol, period]);

  return (
    <div style={{ position: "relative" }}>
      <div style={{ position: "absolute", top: "10px", left: "10px", zIndex: 10, display: "flex", gap: "8px" }}>
        {["1mo", "3mo", "6mo", "1y", "2y", "max"].map(p => (
          <button 
            key={p} 
            onClick={() => setPeriod(p)}
            style={{
              background: period === p ? "var(--accent-blue)" : "rgba(255,255,255,0.1)",
              border: "none", color: "#fff", padding: "4px 10px", borderRadius: "4px",
              cursor: "pointer", fontSize: "12px", fontWeight: "bold"
            }}
          >
            {p.toUpperCase()}
          </button>
        ))}
      </div>
      <div ref={containerRef} style={{ width: "100%", height: "500px" }} />
    </div>
  );
}

export default function Home() {
  const [symbol, setSymbol] = useState("RELIANCE.NS");

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const sym = params.get("symbol");
      if (sym) {
        setSymbol(sym);
      }
    }
  }, []);

  const [a, setA] = useState(null);
  const [showNewsModal, setShowNewsModal] = useState(false);
  const [loading, setLoading] = useState({ candles: false, analysis: false });
  const [errors, setErrors] = useState({ candles: null, analysis: null });

  const fetchAll = useCallback(async (sym) => {
    setLoading({ candles: true, analysis: true });
    setErrors({ candles: null, analysis: null });
    setA(null);

    apiFetch(`/stock/${sym}?period=6mo`)
      .catch(e => setErrors(prev => ({ ...prev, candles: e.message })))
      .finally(() => setLoading(prev => ({ ...prev, candles: false })));

    apiFetch(`/stock/${sym}/analysis-360`)
      .then(d => setA(d))
      .catch(e => setErrors(prev => ({ ...prev, analysis: e.message })))
      .finally(() => setLoading(prev => ({ ...prev, analysis: false })));
  }, []);

  useEffect(() => { fetchAll(symbol); }, [symbol, fetchAll]);

  const handleSearch = (sym) => setSymbol(sym);
  const handleRefresh = () => fetchAll(symbol);
  const changeColor = a?.change_pct >= 0 ? "var(--accent-green)" : "var(--accent-red)";

  return (
    <div className="terminal-root">
      <header className="top-bar">
        <div className="top-bar-left">
          <span className="brand">⚡ QUANT AI 360</span>
          <span className="brand-sub">Elite Trading Terminal</span>
        </div>
        <div className="top-bar-center">
          <StockSearch onSelect={handleSearch} />
          <button className="refresh-btn" onClick={handleRefresh} title="Refresh">↻</button>
          <a href="/scanner" style={{ marginLeft: "12px", padding: "6px 12px", borderRadius: "4px", border: "1px solid var(--accent-blue)", color: "var(--accent-blue)", textDecoration: "none", fontSize: "12px", fontWeight: 600, transition: "all 0.2s" }} 
            onMouseOver={(e) => e.target.style.backgroundColor = "rgba(50,150,250,0.2)"}
            onMouseOut={(e) => e.target.style.backgroundColor = "transparent"}>
            🔍 Scanner
          </a>
          <a href="/portfolio" style={{ marginLeft: "12px", padding: "6px 12px", borderRadius: "4px", border: "1px solid var(--accent-magenta)", color: "var(--accent-magenta)", textDecoration: "none", fontSize: "12px", fontWeight: 600, transition: "all 0.2s" }} 
            onMouseOver={(e) => e.target.style.backgroundColor = "rgba(250,50,250,0.2)"}
            onMouseOut={(e) => e.target.style.backgroundColor = "transparent"}>
            📈 PnL & Trades
          </a>
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
        <div style={{ padding: "24px 24px 0", display: "flex", flexDirection: "column", gap: "24px" }}>
          <div className="card chart-card" style={{ width: "100%" }}>
            <div className="card-header">
              <span className="card-title">📊 {symbol} — Price Chart</span>
              {a && <span style={{ fontSize: "18px", color: "var(--text-muted)", marginLeft: "12px" }}>{a.company_name}</span>}
            </div>
            <ChartPanel symbol={symbol} />
            <div style={{ padding: "16px", borderTop: "1px solid #30363d" }}>
              <PriceActionPanel symbol={symbol} />
            </div>
          </div>
        </div>

      <div className="terminal-body">
        <aside className="left-col">
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

        <main className="center-col">

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

          <div className="card confluence-card">
            <div className="card-header">
              <span className="card-title" style={{ color: "var(--accent-yellow)", fontWeight: "800" }}>🔥 HIGH PROBABILITY ZONE</span>
            </div>
            <div className="card-content">
              {loading.analysis ? <Loading /> : errors.analysis ? <ErrorBox msg={errors.analysis} /> : a && (
                <>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
                    <div>
                      <div style={{ fontSize: "16px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "2px" }}>Confidence</div>
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
                  {a.fibonacci?.zone && (
                    <div style={{ padding: "16px 20px", background: "rgba(234,179,8,0.10)", border: "1px solid rgba(234,179,8,0.3)", borderRadius: "var(--radius-sm)", marginBottom: "24px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ color: "var(--accent-yellow)", fontWeight: "700", fontSize: "18px" }}>📍 {a.fibonacci.zone.replace(/_/g, " ").toUpperCase()}</span>
                      {a.fibonacci?.levels && <span style={{ color: "var(--text-muted)", fontSize: "17px" }}>₹{Math.round(a.fibonacci.levels["0.618"])} – ₹{Math.round(a.fibonacci.levels["0.5"])}</span>}
                    </div>
                  )}
                    <div style={{ padding: "16px", marginTop: "8px", background: "rgba(0,0,0,0.2)", borderRadius: "var(--radius-sm)", border: "1px solid rgba(255,255,255,0.05)" }}>
                      <div style={{ fontSize: "14px", color: "var(--text-muted)", lineHeight: "1.6" }}>
                        <strong style={{ color: "var(--text-bright)" }}>💡 What this means:</strong>
                        <div style={{ marginTop: "8px" }}>
                          • <strong>Confidence:</strong> {a.fibonacci?.confidence === "High" ? "Strong structural and momentum alignment. Higher probability of the zone holding." : a.fibonacci?.confidence === "Medium" ? "Adequate structure but missing some momentum alignment. Normal risk applies." : "Weak alignment. Zone may fail or price may consolidate."}
                        </div>
                        {a.fibonacci?.zone && (
                          <div style={{ marginTop: "4px" }}>
                            • <strong>Zone:</strong> Price is testing the <em>{a.fibonacci.zone.replace(/_/g, " ")}</em>. {a.fibonacci.zone.includes("golden") ? "This is statistically the highest probability reversal area (0.5 - 0.618 retracement)." : "This acts as a key structural support/resistance area."}
                          </div>
                        )}
                      </div>
                    </div>                </>
              )}
            </div>
          </div>

          <div className="card" style={{ borderTop: "2px solid var(--accent-red)" }}>
            <div className="card-header"><span className="card-title">🌍 Market Impact</span></div>
            <div className="card-content">
              {loading.analysis ? <Loading /> : errors.analysis ? <ErrorBox msg={errors.analysis} /> : a && (
                <div>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "24px" }}>
                      <span style={{ fontSize: "18px", fontWeight: "800", color: a.market_regime?.regime === "Bearish" ? "var(--accent-red)" : a.market_regime?.regime === "Bullish" ? "var(--accent-green)" : "var(--accent-yellow)" }}>
                        {a.market_regime?.regime || "UNKNOWN"}
                      </span>
                      <span style={{ fontSize: "18px", color: "var(--text-muted)", background: "rgba(255,255,255,0.05)", padding: "2px 8px", borderRadius: "4px", border: "1px solid var(--border-color)" }}>
                        Vol: {a.market_regime?.volatility || "—"}
                      </span>
                    </div>
                  </div>
                  <div style={{ fontSize: "18px", color: "var(--text-muted)", marginBottom: "16px" }}>Sector: {a.market_regime?.sector || "—"}</div>
                  
                  <div style={{ padding: "16px", marginTop: "8px", background: "rgba(0,0,0,0.2)", borderRadius: "var(--radius-sm)", border: "1px solid rgba(255,255,255,0.05)" }}>
                    <div style={{ fontSize: "14px", color: "var(--text-muted)", lineHeight: "1.6" }}>
                      <strong style={{ color: "var(--text-bright)" }}>💡 What this means:</strong>
                      <div style={{ marginTop: "8px" }}>
                        • <strong>Regime:</strong> The broader market is currently <em>{a.market_regime?.regime}</em>. {
                          a.market_regime?.regime === "Bullish" ? "A rising tide lifts all boats; long setups have a higher statistical edge here." :
                          a.market_regime?.regime === "Bearish" ? "The market trend is down. Long setups are counter-trend and riskier. Short setups or cash are preferred." :
                          "The market is choppy/sideways. Breakouts are prone to failure; mean-reversion strategies work best."
                        }
                      </div>
                      <div style={{ marginTop: "4px" }}>
                        • <strong>Volatility:</strong> <em>{a.market_regime?.volatility}</em> volatility implies {
                          a.market_regime?.volatility === "High" ? "wider price swings. Position sizing should be reduced to account for larger stop losses." :
                          a.market_regime?.volatility === "Low" ? "tighter price action. Good for building momentum, but beware of sudden expansions." :
                          "normal price fluctuations for this asset."
                        }
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="card" style={{ borderTop: "2px solid var(--accent-blue)" }}>
            <div className="card-header">
              <span className="card-title">📰 News</span>
              {a?.news?.analysis?.overall_sentiment && (
                <span style={{ fontSize: "17px", fontWeight: "700", padding: "2px 8px", borderRadius: "4px",
                  background: a.news.analysis.overall_sentiment === "Bullish" ? "rgba(16,185,129,0.15)" : a.news.analysis.overall_sentiment === "Bearish" ? "rgba(239,68,68,0.15)" : "rgba(255,255,255,0.05)",
                  color: a.news.analysis.overall_sentiment === "Bullish" ? "var(--accent-green)" : a.news.analysis.overall_sentiment === "Bearish" ? "var(--accent-red)" : "var(--text-muted)" }}>
                  {a.news.analysis.overall_sentiment}
                </span>
              )}
            </div>
            <div className="card-content">
              {loading.analysis ? <Loading /> : errors.analysis ? <ErrorBox msg={errors.analysis} /> :
                (a?.news?.articles?.length > 0) ? (
                  <>
                    {a.news.articles.slice(0, 3).map((n, i) => (
                      <div key={i} style={{ fontSize: "16px", color: "var(--text-secondary)", padding: "10px 0", borderBottom: "1px solid var(--border-color)", lineHeight: "1.4" }}>
                        <div style={{ fontWeight: "600", color: "var(--foreground)", marginBottom: "4px" }}>{n.title}</div>
                        <div style={{ fontSize: "14px", color: "var(--text-muted)", marginBottom: "4px" }}>{n.summary?.substring(0, 100)}{n.summary?.length > 100 ? "..." : ""}</div>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "var(--text-muted)" }}>
                          <span>{n.provider}</span>
                          <span style={{ color: n.sentiment === "Bullish" ? "var(--accent-green)" : n.sentiment === "Bearish" ? "var(--accent-red)" : "var(--text-muted)" }}>{n.sentiment}</span>
                        </div>
                      </div>
                    ))}
                    {a.news.articles.length > 3 && (
                      <button 
                        onClick={() => setShowNewsModal(true)}
                        style={{ width: "100%", padding: "12px", background: "linear-gradient(135deg, var(--accent-blue), #1e3a8a)", color: "white", border: "none", borderRadius: "8px", marginTop: "16px", cursor: "pointer", fontWeight: "600", fontSize: "15px", transition: "all 0.2s" }}
                      >
                        View All Articles & Analysis ({a.news.count})
                      </button>
                    )}
                  </>
                ) : <div className="text-muted">No recent news available.</div>
              }
            </div>
          </div>

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
                  </div>
                )) : <div className="text-muted">Awaiting scenario data.</div>
              }
            </div>
          </div>
        </main>
      </div>

      {showNewsModal && a?.news?.articles && (
        <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', backgroundColor: 'rgba(0,0,0,0.8)', zIndex: 9999, overflowY: 'auto', padding: '40px' }}>
          <div style={{ maxWidth: '800px', margin: '0 auto', backgroundColor: '#171717', borderRadius: '12px', padding: '30px', position: 'relative', border: '1px solid #333' }}>
            <button onClick={() => setShowNewsModal(false)} style={{ position: 'absolute', top: '20px', right: '20px', background: 'none', border: 'none', color: '#fff', fontSize: '24px', cursor: 'pointer' }}>✖</button>
            <h2 style={{ borderBottom: '2px solid var(--accent-blue)', paddingBottom: '16px', marginBottom: '20px' }}>{symbol} - Full News Analysis</h2>
            {a.news.articles.map((n, i) => (
              <div key={i} style={{ marginBottom: '24px', padding: '16px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
                <h3 style={{ margin: '0 0 8px 0', fontSize: '18px' }}><a href={n.link} target="_blank" rel="noreferrer" style={{ color: '#fff', textDecoration: 'none' }}>{n.title}</a></h3>
                <p style={{ margin: '0 0 12px 0', color: '#a3a3a3', lineHeight: '1.5' }}>{n.summary}</p>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px' }}>
                  <span style={{ color: '#737373' }}>{n.provider} • {new Date(n.pub_date * 1000).toLocaleDateString()}</span>
                  <span style={{ color: n.sentiment === 'Bullish' ? 'var(--accent-green)' : n.sentiment === 'Bearish' ? 'var(--accent-red)' : 'var(--text-muted)', fontWeight: 'bold' }}>{n.sentiment}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
