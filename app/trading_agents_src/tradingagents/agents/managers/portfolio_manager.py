"""Portfolio Manager: synthesises the risk-analyst debate into the final decision.

Uses LangChain's ``with_structured_output`` so the LLM produces a typed
``PortfolioDecision`` directly, in a single call.  The result is rendered
back to markdown for storage in ``final_trade_decision`` so memory log,
CLI display, and saved reports continue to consume the same shape they do
today.  When a provider does not expose structured output, the agent falls
back gracefully to free-text generation.
"""

from __future__ import annotations

from tradingagents.agents.schemas import PortfolioDecision, render_pm_decision
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
)
from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)


def create_portfolio_manager(llm):
    structured_llm = bind_structured(llm, PortfolioDecision, "Portfolio Manager")

    def portfolio_manager_node(state) -> dict:
        instrument_context = build_instrument_context(state["company_of_interest"])

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        research_plan = state["investment_plan"]
        trader_plan = state["trader_investment_plan"]

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
