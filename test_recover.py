import re

with open("api/routes/analysis.py", "r") as f:
    text = f.read()

better_func = """def _build_story_sections(
    structure: dict,
    fib: dict,
    liquidity: dict,
    rs: dict,
    current_price: float,
) -> dict:
    \"\"\"Build structured 5-section stock story with detail.\"\"\"
    trend = structure.get("trend", "Unknown")
    sma = structure.get("sma50", 0)

    # 1. Structure
    if trend == "Bullish":
        structure_text = f"The stock is currently demonstrating a robust upward trajectory, firmly sustained above the 50-day SMA of ₹{round(sma, 1) if sma else 0}. This reflects consistent buyer demand and higher-low market structure formations, marking clear institutional support and positive investor sentiment."
    elif trend == "Bearish":
        structure_text = f"The stock is locked in a prolonged downtrend, facing heavy resistance and trading below the 50-day SMA of ₹{round(sma, 1) if sma else 0}. Sellers maintain firm control, steadily compressing higher-highs and suppressing any meaningful rebounds in this bearish cycle."
    else:
        structure_text = f"The stock is currently trading in a sideways, range-bound consolidation phase. Without a clear directional bias relative to the 50-day SMA of ₹{round(sma, 1) if sma else 0}, the asset is searching for a catalyst to break equilibrium."

    # 2. Fibonacci
    fib_zone = fib.get("zone", "unknown")
    fib_high = fib.get("high", 0)
    fib_low = fib.get("low", 0)
    
    if fib_zone == "golden_pocket":
        fib_text = f"Price action has gracefully retraced into the Golden Pocket zone (between ₹{round(fib.get('levels',{}).get('0.618',0),1)} and ₹{round(fib.get('levels',{}).get('0.5',0),1)}). This specific area often acts as a massive psychological bounce point for smart money, setting up a very high-probability continuation of the overall primary trend."
    elif fib_zone == "failed_retracement":
        fib_text = "Price broke decisively below the critical 0.786 Fibonacci level, indicating a failed retracement. This technical failure signifies that the opposing side has overwhelmed the trend, risking severe structural breakdown if buyers do not step in immediately."
    else:
        fib_text = f"Price is meandering within the {fib_zone.replace('_', ' ')} zone, mapped from a swing high of ₹{round(fib_high,1)} down to a swing low of ₹{round(fib_low,1)}. While not at a critical turning point, its reaction here will dictate the immediate micro-trend direction."

    # 3. Liquidity
    if liquidity.get("detected"):
        liq_text = f"A prominent {liquidity.get('type','Liquidity sweep')} was detected at the ₹{liquidity.get('level',0)} level. This behavior highly suggests institutional 'stop hunting'—taking out retail traders' stop-losses. This often immediately precedes a sharp, violent mean-reversion move in the opposite direction."
    else:
        liq_text = "Currently, no major liquidity sweeps or stop-hunts are detected on the chart. Price action remains highly organic and clean, reacting dynamically to standard structural supply and demand zones without unusual manipulation."

    # 4. Relative Strength
    rs_ratio = rs.get("rs_ratio", 0)
    if rs.get("outperforming"):
        rs_text = f"Displaying exceptional relative strength, the asset is outperforming the broader NIFTY index by a margin of {rs_ratio}%. Such massive outperformance typically indicates deep underlying institutional accumulation, meaning the stock will likely hold up much better during market corrections."
    elif rs.get("underperforming"):
        rs_text = f"The asset is severely lagging behind the NIFTY index, underperforming by {rs_ratio}%. This weakness suggests a lack of capital inflow and a possible internal fundamental weakness, making it dangerous to hold long positions compared to broader market alternatives."
    else:
        rs_text = f"The stock's performance is tracking completely inline with the broader NIFTY (RS Ratio: {rs_ratio}%). It is essentially acting as a beta-tracker, rising and falling mechanically with general market tides without any specific idiosyncratic alpha."

    # 5. Conclusion
    bias = "BULLISH" if trend == "Bullish" else "BEARISH" if trend == "Bearish" else "NEUTRAL"
    conclusion = f"Overall Technical Verdict is solidly {bias}. Factoring in its structural alignment, current Fibonacci positioning, recent liquidity grabs, and momentum relative to the broader index, traders should focus closely on the defined high-probability scenarios outlined directly below."

    return {
        "structure": structure_text,
        "fibonacci": fib_text,
        "liquidity": liq_text,
        "relative_strength": rs_text,
        "conclusion": conclusion
    }"""

# Use regex to replace the function
pattern = r"def _build_story_sections\(.*?\)\s*->\s*dict:.*?(?=\n\s*# Scenarios|\n\s*def|\Z)"

new_text = re.sub(pattern, better_func + "\n\n", text, flags=re.DOTALL | re.MULTILINE)

with open("api/routes/analysis.py", "w") as f:
    f.write(new_text)