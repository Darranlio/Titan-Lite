"""Portfolio Manager: synthesises the risk-analyst debate into the final decision.

Uses LangChain's ``with_structured_output`` so the LLM produces a typed
``PortfolioDecision`` directly, in a single call.  The result is rendered
back to markdown for storage in ``final_trade_decision`` so memory log,
CLI display, and saved reports continue to consume the same shape they do
today.  When a provider does not expose structured output, the agent falls
back gracefully to free-text generation.
"""

from __future__ import annotations

import pandas as pd

from tradingagents.agents.schemas import PortfolioDecision, render_pm_decision
from tradingagents.dataflows.stockstats_utils import load_ohlcv
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
)
from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)


def _build_structure_facts(symbol: str, trade_date: str) -> str:
    """Compute signal-free Wyckoff effort-vs-result facts from cached OHLCV.

    Returns objective facts + position context only (no buy/sell signal), so
    the Portfolio Manager can weigh market structure alongside the debate.
    """
    try:
        df = load_ohlcv(symbol, trade_date)
    except Exception:
        return "(量价结构数据不可用，跳过该维度)"

    if df.empty or len(df) < 30:
        return "(量价结构数据不足，跳过该维度)"

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    open_ = df["Open"]
    volume = df["Volume"]

    prev_close = close.shift(1)
    true_range = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    atr = true_range.rolling(14).mean()

    effort = volume / volume.rolling(20).mean()
    result = (close - open_) / atr

    bar_range = (high - low).replace(0, pd.NA)
    close_loc = (close - low) / bar_range
    ad_line = (volume * (2 * close - high - low) / bar_range).cumsum()

    n = 20
    price_chg = close.iloc[-1] / close.iloc[-n] - 1
    ad_net = ad_line.iloc[-1] - ad_line.iloc[-n]

    window = close.iloc[-252:]
    percentile = float((window <= close.iloc[-1]).mean())

    recent = df.iloc[-n:]
    recent_effort = effort.iloc[-n:]
    supply = int(((recent_effort > 1.5) & (recent["Close"] <= recent["Open"])).sum())
    absorb = int(((recent_effort > 1.5) & (recent["Close"] >= recent["Open"])).sum())

    if price_chg > 0 and ad_net < 0:
        divergence = "价升量能背离（警惕）"
    elif price_chg < 0 and ad_net > 0:
        divergence = "价跌资金承接（关注）"
    else:
        divergence = "量价基本一致"

    position = "高位" if percentile > 0.7 else "低位" if percentile < 0.3 else "中位"

    return (
        "## 量价结构事实 (Wyckoff Effort vs Result，客观事实非信号)\n"
        f"- 最近交易日: {str(df['Date'].iloc[-1])[:10]}\n"
        f"  相对成交量 effort={effort.iloc[-1]:.2f}x（对20日均量），"
        f"ATR归一化推进 result={result.iloc[-1]:+.2f}，"
        f"收盘位于当日区间 {close_loc.iloc[-1]:.0%} 分位\n"
        f"- 近{n}日: 价格 {price_chg:+.1%}，A/D资金流净额 {ad_net:+,.0f} → {divergence}\n"
        f"- 位置: 当前价处于近252日区间 {percentile:.0%} 分位（{position}）\n"
        f"- 近{n}日放量滞涨（供应压制）{supply}次，放量止跌（需求承接）{absorb}次"
    )


def create_portfolio_manager(llm):
    structured_llm = bind_structured(llm, PortfolioDecision, "Portfolio Manager")

    def portfolio_manager_node(state) -> dict:
        instrument_context = build_instrument_context(state["company_of_interest"])

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        research_plan = state["investment_plan"]
        trader_plan = state["trader_investment_plan"]

        structure_facts = _build_structure_facts(
            state["company_of_interest"], state.get("trade_date", "")
        )

        past_context = state.get("past_context", "")
        lessons_line = (
            f"- Lessons from prior decisions and outcomes:\n{past_context}\n"
            if past_context
            else ""
        )

        prompt = f"""As the Lead Portfolio Manager, synthesize the research and deliver a DECISIVE and CONSISTENT trading decision.

{instrument_context}

---

**Rating Scale** (strict adherence required):
- **Strong Buy**: Exceptional conviction; CURRENT price is at or below ideal entry.
- **Buy**: Solid conviction; favorable risk/reward at CURRENT price.
- **Overweight**: Constructive long-term view; hold current position and add on minor dips.
- **Hold**: Neutral view OR constructive view but **CURRENT price is too far above entry/support**.
- **Underweight**: Cautious view; reduce exposure/trim profits.
- **Sell**: High conviction bear case; exit immediately.
- **Strong Sell**: Extreme conviction; structural failure identified.

---

**CRITICAL LOGICAL CONSISTENCY RULE:**
If your reasoning suggests "waiting for a pullback", "waiting for a better entry", or "waiting for a lower price (e.g., $150)" before buying, you **MUST NOT** select "Buy" or "Strong Buy". In such cases, the only acceptable rating is **HOLD**. 

Your Rating MUST reflect the action to take at the **CURRENT MARKET PRICE**, not a hypothetical future price.

**Context:**
- Research Manager's plan: {research_plan}
- Trader's proposal: {trader_plan}
{lessons_line}
**Risk Analysts Debate History:**
{history}

{structure_facts}

---

Deliver your final decision in Chinese as requested, but ensure the logic is bulletproof and free of contradictions.{get_language_instruction()}"""

        final_trade_decision = invoke_structured_or_freetext(
            structured_llm,
            llm,
            prompt,
            render_pm_decision,
            "Portfolio Manager",
        )

        new_risk_debate_state = {
            "judge_decision": final_trade_decision,
            "history": risk_debate_state["history"],
            "aggressive_history": risk_debate_state["aggressive_history"],
            "conservative_history": risk_debate_state["conservative_history"],
            "neutral_history": risk_debate_state["neutral_history"],
            "latest_speaker": "Judge",
            "current_aggressive_response": risk_debate_state["current_aggressive_response"],
            "current_conservative_response": risk_debate_state["current_conservative_response"],
            "current_neutral_response": risk_debate_state["current_neutral_response"],
            "count": risk_debate_state["count"],
        }

        return {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": final_trade_decision,
        }

    return portfolio_manager_node
