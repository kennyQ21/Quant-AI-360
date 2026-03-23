"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export default function PriceActionDetailedPage() {
  const params = useParams();
  const symbol = params.symbol ? decodeURIComponent(params.symbol) : null;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!symbol) return;
    setLoading(true);
    fetch(`${API}/stock/${symbol}/price-action`)
      .then(r => r.json())
      .then(d => { setData(d); setError(null); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [symbol]);

  if (loading) {
    return (
      <div className="terminal-root" style={{ padding: "40px", display: "flex", justifyContent: "center" }}>
        <div className="loading-spinner"><div className="spinner" /></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="terminal-root" style={{ padding: "40px" }}>
        <div className="error-box">⚠ {error}</div>
        <Link href="/" style={{ color: "var(--accent-blue)", marginTop: "20px", display: "inline-block" }}>
          ← Back to Dashboard
        </Link>
      </div>
    );
  }

  const conf = data?.confluence || {};
  const scoreColor = conf.score >= 75 ? "var(--accent-green)" : conf.score >= 50 ? "var(--accent-yellow)" : "var(--accent-red)";

  return (
    <div className="terminal-root" style={{ padding: "40px", maxWidth: "1200px", margin: "0 auto", minHeight: "100vh" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px", borderBottom: "1px solid #30363d", paddingBottom: "16px" }}>
        <h1 style={{ fontSize: "24px", margin: 0 }}>Detailed Price Action: {symbol}</h1>
        <Link href="/" style={{ padding: "8px 16px", backgroundColor: "#30363d", color: "#fff", borderRadius: "4px", textDecoration: "none", fontSize: "14px", fontWeight: "bold" }}>
          ← Dashboard
        </Link>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "24px" }}>
        {/* Main Confluence Panel */}
        <div className="card">
          <div className="card-header"><span className="card-title">🚨 Confluence Strategy Rating</span></div>
          <div className="card-content" style={{ display: "flex", gap: "24px", alignItems: "center", padding: "20px" }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: "20px", fontWeight: 700, marginBottom: "8px" }}>⚡ {conf.signal_name || "No Setup Detected"}</div>
              <div style={{ color: "rgba(200,200,200,0.8)", fontSize: "14px" }}>{conf.breakdown || "Wait for better setups to form."}</div>
            </div>
            
            <div style={{ width: "200px", textAlign: "center", padding: "20px", backgroundColor: "rgba(100,100,100,0.1)", borderRadius: "8px", border: `2px solid ${scoreColor}` }}>
              <div style={{ fontSize: "36px", fontWeight: 800, color: scoreColor }}>{Math.round(conf.score || 0)}</div>
              <div style={{ fontSize: "12px", textTransform: "uppercase", letterSpacing: "1px", color: "gray" }}>Score / 100</div>
            </div>
          </div>
          
          {conf.direction && (
            <div style={{ padding: "0 20px 20px 20px", display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px", textAlign: "center" }}>
              <StatBox label="Direction" value={conf.direction} color={conf.direction === "LONG" ? "var(--accent-green)" : "var(--accent-red)"} />
              <StatBox label="Entry Price" value={`₹${conf.entry_price?.toFixed(2)}`} />
              <StatBox label="Stop Loss" value={`₹${conf.stop_loss?.toFixed(2)}`} color="var(--accent-red)" />
              <StatBox label="Target 1" value={`₹${conf.target1?.toFixed(2)}`} color="var(--accent-green)" />
            </div>
          )}
            
            {data?.risk_management && (
              <div style={{ padding: "0 20px 20px 20px" }}>
                <div style={{ padding: "16px", backgroundColor: "rgba(30, 40, 60, 0.5)", borderRadius: "8px", border: "1px solid rgba(100, 150, 255, 0.2)" }}>
                  <h3 style={{ marginTop: 0, marginBottom: "12px", fontSize: "14px", color: "#a5d6ff", display: "flex", alignItems: "center", gap: "8px" }}>
                    🛡️ Risk Management (Prop-Desk Level)
                  </h3>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px" }}>
                    <div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>Suggested Position</div>
                      <div style={{ fontSize: "16px", fontWeight: "bold" }}>{data.risk_management.suggested_shares} Shares</div>
                    </div>
                    <div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>Total Risk ($)</div>
                      <div style={{ fontSize: "16px", fontWeight: "bold", color: "var(--accent-red)" }}>₹{data.risk_management.actual_risk_dollars}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>Position Size</div>
                      <div style={{ fontSize: "16px", fontWeight: "bold" }}>₹{data.risk_management.position_size_dollars}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>Stop Out %</div>
                      <div style={{ fontSize: "16px", fontWeight: "bold" }}>{data.risk_management.stop_distance_pct}%</div>
                    </div>
                  </div>
                </div>
              </div>
            )}          </div>

          <h2 style={{ marginTop: "16px", marginBottom: "0", fontSize: "18px", color: "#8b949e", textTransform: "uppercase", letterSpacing: "1px" }}>Strategy Diagnostics (HTF & LTF)</h2>
          
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            
            {/* Order Flow Structure */}
            <StrategyCard title="Order Flow (HTF Structure)" icon="📊" data={data?.order_flow}>            {data?.order_flow && (
              <div style={{ display: "grid", gap: "12px" }}>
                <ProgressBar label="Structure Quality" value={data.order_flow.structure_quality || 0} max={100} />
                <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "8px" }}>
                  <Badge label="Trend" value={data.order_flow.trend || "Unknown"} />
                  <Badge label="Structure" value={data.order_flow.structure || "Unknown"} />
                  <Badge label="Last BOS" value={data.order_flow.last_bos || "None"} />
                </div>
              </div>
            )}
          </StrategyCard>

          {/* Liquidity */}
          <StrategyCard title="Liquidity Sweeps & Levels" icon="💧" data={data?.liquidity}>
            {data?.liquidity && (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px", height: "100%" }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: "8px" }}>
                  <StatBox label="Levels Detected" value={data.liquidity.total_liquidity_zones || data.liquidity.levels_detected || 0} sm />
                  <StatBox label="Highest Strength" value={data.liquidity.highest_strength || 0} sm color="var(--accent-blue)" />
                </div>
                
                {data.liquidity.liquidity_levels && data.liquidity.liquidity_levels.length > 0 && (
                   <div style={{ display: "flex", flexDirection: "column", gap: "6px", flex: 1, overflowY: "auto", maxHeight: "200px", paddingRight: "4px" }}>
                     <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px", borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "4px" }}>Top Levels</div>
                     {data.liquidity.liquidity_levels
                        .sort((a,b) => (b.strength || 0) - (a.strength || 0))
                        .slice(0, 4)
                        .map((l, i) => (
                           <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", backgroundColor: "rgba(255,255,255,0.05)", padding: "8px", borderRadius: "4px" }}>
                             <div>
                                <span style={{ fontSize: "12px", fontWeight: "bold" }}>₹{l.price?.toFixed(2)}</span>
                                <span style={{ fontSize: "10px", color: "gray", marginLeft: "6px" }}>{l.type}</span>
                             </div>
                             <div style={{ fontSize: "11px", color: l.strength >= 80 ? "var(--accent-green)" : l.strength >= 50 ? "var(--accent-yellow)" : "var(--accent-red)" }}>
                                Str: {l.strength}
                             </div>
                           </div>
                        ))}
                   </div>
                )}
              </div>
            )}
          </StrategyCard>

          {/* FVG */}
          <StrategyCard title="Fair Value Gaps (FVG)" icon="⬜" data={data?.fvg}>
            {data?.fvg && (
              <div style={{ display: "grid", gap: "16px" }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", textAlign: "center" }}>
                  <StatBox label="Total FVGs" value={data.fvg.total_fvgs || data.fvg.total_detected || 0} sm />
                  <StatBox label="Fresh" value={data.fvg.fresh_fvgs || 0} sm color="var(--accent-green)" />
                  <StatBox label="Tested" value={data.fvg.tested_fvgs || 0} sm color="var(--accent-yellow)" />
                  <StatBox label="Filled" value={data.fvg.filled_fvgs || 0} sm color="var(--accent-red)" />
                </div>
                {data.fvg.fvg_list && data.fvg.fvg_list.length > 0 && (
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                     <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px", borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "4px" }}>Recent FVGs</div>
                     {data.fvg.fvg_list.slice(-3).reverse().map((fvg, i) => (
                        <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", backgroundColor: "rgba(255,255,255,0.05)", padding: "8px", borderRadius: "4px" }}>
                          <div>
                            <span style={{ fontSize: "12px", fontWeight: "bold", color: fvg.direction === "BULLISH" ? "var(--accent-green)" : "var(--accent-red)" }}>{fvg.direction}</span>
                            <span style={{ fontSize: "11px", color: "gray", marginLeft: "6px" }}>₹{fvg.bottom?.toFixed(1)} - ₹{fvg.top?.toFixed(1)}</span>
                          </div>
                          <Badge label="State" value={fvg.state} />
                        </div>
                     ))}
                  </div>
                )}
              </div>
            )}
          </StrategyCard>

          {/* iFVG */}
          <StrategyCard title="Inverse FVGs (iFVG)" icon="⬛" data={data?.ifvg}>
            {data?.ifvg && (
              <div style={{ display: "grid", gap: "16px" }}>
                 <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", textAlign: "center" }}>
                   <StatBox label="Active Built" value={data.ifvg.active_ifvgs || 0} sm />
                   <StatBox label="Total Evaluated" value={data.ifvg.total_fvgs_evaluated || data.ifvg.total_detected || 0} sm />
                 </div>
              </div>
            )}
          </StrategyCard>

          {/* Breakout */}
          <StrategyCard title="Breakout Detection" icon="🚀" data={data?.breakout}>
            {data?.breakout && (
              <div style={{ display: "grid", gap: "16px" }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <Badge label="Phase" value={data.breakout.phase || "NONE"} />
                  <Badge label="Quality" value={data.breakout.setup_quality ? data.breakout.setup_quality.toFixed(1) : 0} />
                </div>
                
                {data.breakout.phase === "CONSOLIDATION" && data.breakout.consolidation && (
                   <div style={{ fontSize: "12px", backgroundColor: "rgba(0,0,0,0.2)", padding: "12px", borderRadius: "4px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                     <div><span style={{ color: "var(--text-muted)" }}>Range:</span> <strong style={{ color:"white" }}>{data.breakout.consolidation.range_pct?.toFixed(2)}%</strong></div>
                     <div><span style={{ color: "var(--text-muted)" }}>Duration:</span> <strong style={{ color:"white" }}>{data.breakout.consolidation.duration} bars</strong></div>
                     <div><span style={{ color: "var(--text-muted)" }}>High:</span> <strong style={{ color:"white" }}>₹{data.breakout.consolidation.high?.toFixed(2)}</strong></div>
                     <div><span style={{ color: "var(--text-muted)" }}>Low:</span> <strong style={{ color:"white" }}>₹{data.breakout.consolidation.low?.toFixed(2)}</strong></div>
                   </div>
                )}
                
                <div style={{ fontSize: "12px", display: "flex", justifyContent: "space-around", color: "var(--text-muted)", backgroundColor: "rgba(255,255,255,0.05)", padding: "8px", borderRadius: "4px" }}>
                  <div>Consolidation: {data.breakout.consolidation_detected ? "✅" : "❌"}</div>
                  <div>Breakout: {data.breakout.breakout_triggered ? "✅" : "❌"}</div>
                </div>
              </div>
            )}
          </StrategyCard>

          {/* AMD */}
          <StrategyCard title="AMD Model" icon="📈" data={data?.amd}>
            {data?.amd && (
              <div style={{ display: "grid", gap: "16px" }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <Badge label="Phase" value={data.amd.phase || "NONE"} />
                  <Badge label="Setup Name" value={data.amd.setup_name || "No Setup"} />
                  <Badge label="Quality" value={data.amd.setup_quality ? data.amd.setup_quality.toFixed(1) : 0} />
                </div>
                <ProgressBar label="Confidence Level" value={data.amd.confidence || 0} max={100} />
              </div>
            )}
          </StrategyCard>

          {/* VCP */}
          <StrategyCard title="VCP Pattern" icon="🔶" data={data?.vcp}>
             {data?.vcp && (
              <div style={{ display: "grid", gap: "16px" }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <Badge label="Phase" value={data.vcp.phase || "NONE"} />
                  <Badge label="Stage" value={data.vcp.stage || "NONE"} />
                </div>
                <div style={{ fontSize: "12px", color: "var(--text-muted)", backgroundColor: "rgba(0,0,0,0.2)", padding: "12px", borderRadius: "4px" }}>
                  <div style={{ marginBottom: "8px" }}><strong>Setup Name:</strong> <span style={{ color: "white" }}>{data.vcp.setup_name || "No VCP"}</span></div>
                  <div><strong>Pattern Detected:</strong> {data.vcp.pattern_detected ? "✅ Yes" : "❌ No"}</div>
                </div>
              </div>
            )}
          </StrategyCard>

        </div>
      </div>
    </div>
  );
}

// Helpers

function StatBox({ label, value, color = "#fff", sm = false }) {
  return (
    <div style={{ backgroundColor: "rgba(255,255,255,0.05)", padding: sm ? "8px" : "12px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.05)" }}>
      <div style={{ fontSize: "11px", color: "gray", marginBottom: "4px" }}>{label}</div>
      <div style={{ fontWeight: "bold", fontSize: sm ? "16px" : "18px", color }}>{value}</div>
    </div>
  );
}

function Badge({ label, value }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
      <span style={{ fontSize: "10px", color: "#8b949e", textTransform: "uppercase" }}>{label}</span>
      <span style={{ fontSize: "12px", fontWeight: "bold", backgroundColor: "rgba(255,255,255,0.1)", padding: "4px 12px", borderRadius: "12px", marginTop: "4px", color: "#fff" }}>
        {value}
      </span>
    </div>
  )
}

function ProgressBar({ label, value, max }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100)) || 0;
  const color = pct > 75 ? "var(--accent-green)" : pct > 40 ? "var(--accent-yellow)" : "var(--accent-red)";
  
  return (
    <div style={{ backgroundColor: "rgba(0,0,0,0.2)", padding: "12px", borderRadius: "6px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "#8b949e", marginBottom: "8px" }}>
        <strong>{label}</strong>
        <span style={{ color: "#fff", fontWeight: "bold" }}>{value}/{max}</span>
      </div>
      <div style={{ height: "8px", backgroundColor: "rgba(255,255,255,0.1)", borderRadius: "4px", overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${pct}%`, backgroundColor: color, transition: "width 0.3s ease" }} />
      </div>
    </div>
  )
}

function StrategyCard({ title, icon, data, children }) {
  if (!data) return null;
  const hasError = !!data.error;

  return (
    <div className="card" style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div className="card-header" style={{ display: "flex", alignItems: "center", gap: "8px", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span>{icon}</span>
          <span className="card-title">{title}</span>
        </div>
        {hasError ? <span style={{ color: "var(--accent-red)", fontSize: "12px", fontWeight: "bold" }}>Error</span> : <span style={{ color: "var(--accent-green)", fontSize: "12px", fontWeight: "bold" }}>Active</span>}
      </div>
      <div className="card-content" style={{ padding: "20px", flex: 1 }}>
        {hasError ? (
          <div style={{ color: "var(--accent-red)", fontSize: "14px", fontWeight: "bold" }}>⚠ {data.error}</div>
        ) : (
          children
        )}
      </div>
    </div>
  );
}
