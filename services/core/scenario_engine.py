"""Scenario Engine — generates Bull/Bear/Base scenarios"""
from typing import Dict, Any, List

def generate_scenarios(
    symbol: str,
    current_price: float,
    trend: str,
    fib_levels: Dict,
    momentum_label: str,
    regime: str,
) -> List[Dict[str, Any]]:

    scenarios = []

    # Bull Scenario
    if fib_levels:
        target_1 = fib_levels.get("0.0", current_price * 1.05)
        target_2 = current_price * 1.10
    else:
        target_1 = current_price * 1.05
        target_2 = current_price * 1.12

    bull_prob = 60 if trend == "Bullish" else 40 if trend == "Sideways" else 25
    if momentum_label == "Strong":
        bull_prob = min(bull_prob + 10, 80)
    if regime == "Bullish":
        bull_prob = min(bull_prob + 5, 85)

    scenarios.append({
        "type": "Bull",
        "probability": bull_prob,
        "target_1": round(target_1, 2),
        "target_2": round(target_2, 2),
        "stop_loss": round(current_price * 0.94, 2),
        "description": (
            f"BULLISH CONTINUATION STRATEGY: The primary objective is to capitalize on upward momentum. "
            f"If price successfully breaks and holds above the initial target of ₹{round(target_1, 1)}, it triggers further buying pressure. "
            f"Given the current momentum is {momentum_label} and the broader market regime is {regime}, this strategy relies on sustained institutional accumulation. "
            f"Secondary targets scale up to ₹{round(target_2, 1)}, offering an excellent risk-to-reward ratio. "
            f"Invalidation occurs if price sharply drops below the critical support at ₹{round(current_price * 0.94, 2)}. Traders should look for significant volume expansion "
            f"as the primary confirmation signal to avoid fake breakouts."
        ),
        "trigger": f"Close above ₹{round(current_price * 1.02, 1)} on volume.",
    })

    # Bear Scenario
    bear_prob = 100 - bull_prob - 15
    bear_target = fib_levels.get("1.0", current_price * 0.90) if fib_levels else current_price * 0.90
    
    scenarios.append({
        "type": "Bear",
        "probability": bear_prob,
        "target_1": round(bear_target, 2),
        "target_2": round(current_price * 0.85, 2),
        "stop_loss": round(current_price * 1.04, 2),
        "description": (
            f"BEARISH BREAKDOWN STRATEGY: This scenario outlines the potential for downside acceleration if key support structures fail. "
            f"When price loses its footing and drops below core demand zones targeting ₹{round(bear_target, 1)}, it typically triggers stop-losses from trapped long positions. "
            f"The secondary deeper target sits at ₹{round(current_price * 0.85, 2)}. "
            f"Short sellers or hedge operators should monitor for consecutive lower highs dynamically pushing the price down. "
            f"The thesis is invalidated if there is a sudden sharp recovery above ₹{round(current_price * 1.04, 2)} (a 'V-shape' bounce). "
            f"A successful breakdown requires high sell volume and broad market weakness."
        ),
        "trigger": f"Close below ₹{round(current_price * 0.98, 1)} on volume.",
    })

    # Base Scenario
    scenarios.append({
        "type": "Base",
        "probability": 15,
        "target_1": round(current_price * 1.02, 2),
        "target_2": round(current_price * 0.98, 2),
        "stop_loss": None,
        "description": (
            f"RANGE-BOUND/ACCUMULATION STRATEGY: In this neutral profile, the market enters a state of equilibrium, characterized by tightening volatility. "
            f"Price action is projected to oscillate between structural resistance at ₹{round(current_price * 1.02, 2)} and support at ₹{round(current_price * 0.98, 2)}. "
            f"During this phase, institutional players are typically accumulating or distributing quietly. "
            f"The optimal approach here is mean-reversion: buying the lower boundary and selling the upper boundary. "
            f"Avoid aggressive directional bets until a clear breakout/breakdown is established. Options sellers might capitalize on theta decay as the underlying stock drifts sideways."
        ),
        "trigger": "No directional catalyst in the next 5-10 sessions.",
    })

    return scenarios
