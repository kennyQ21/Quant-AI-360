"use client";
import { useState, useEffect, useRef } from "react";

const NIFTY50 = [
  "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS",
  "SBIN.NS","KOTAKBANK.NS","BHARTIARTL.NS","LT.NS","HINDUNILVR.NS",
  "ITC.NS","AXISBANK.NS","TATAMOTORS.NS","WIPRO.NS","BAJFINANCE.NS",
  "SUNPHARMA.NS","MARUTI.NS","NTPC.NS","ONGC.NS","POWERGRID.NS",
  "HCLTECH.NS","DRREDDY.NS","TATASTEEL.NS","BAJAJFINSV.NS","TITAN.NS",
  "ASIANPAINT.NS","TECHM.NS","ADANIENT.NS","DIVISLAB.NS","CIPLA.NS",
  "JSWSTEEL.NS","COALINDIA.NS","HINDALCO.NS","SBILIFE.NS","ULTRACEMCO.NS",
  "BRITANNIA.NS","GRASIM.NS","M&M.NS","APOLLOHOSP.NS","INDUSINDBK.NS",
  "HDFCLIFE.NS","BAJAJ-AUTO.NS","EICHERMOT.NS","HEROMOTOCO.NS","NESTLEIND.NS",
  "TATACONSUM.NS","LT.NS","ADANIPORTS.NS",
];

export default function StockSearch({ onSelect }) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [show, setShow] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }
    const q = query.toUpperCase();
    const matches = NIFTY50.filter(s => s.includes(q)).slice(0, 8);
    setSuggestions(matches);
    setShow(true);
  }, [query]);

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setShow(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function select(symbol) {
    setQuery(symbol);
    setShow(false);
    onSelect(symbol);
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && query.trim()) {
      const sym = query.trim().toUpperCase();
      const formatted = sym.endsWith(".NS") ? sym : sym + ".NS";
      select(formatted);
    }
  }

  return (
    <div ref={ref} style={{ position: "relative", width: "100%" }}>
      <input
        id="stock-search"
        value={query}
        onChange={e => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Search symbol (e.g. RELIANCE, TCS)"
        style={{
          width: "100%",
          background: "rgba(255,255,255,0.06)",
          border: "1px solid var(--border-color)",
          borderRadius: "var(--radius-sm)",
          color: "var(--text-primary)",
          padding: "10px 14px",
          fontSize: "14px",
          outline: "none",
        }}
      />
      {show && suggestions.length > 0 && (
        <div style={{
          position: "absolute", top: "100%", left: 0, right: 0,
          background: "var(--bg-secondary)", border: "1px solid var(--border-color)",
          borderRadius: "var(--radius-sm)", zIndex: 100, maxHeight: "260px", overflowY: "auto",
        }}>
          {suggestions.map(s => (
            <div
              key={s}
              onClick={() => select(s)}
              style={{
                padding: "10px 14px", cursor: "pointer", fontSize: "13px",
                color: "var(--text-secondary)", transition: "background 0.15s",
              }}
              onMouseEnter={e => e.target.style.background = "rgba(255,255,255,0.08)"}
              onMouseLeave={e => e.target.style.background = "transparent"}
            >
              {s}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
