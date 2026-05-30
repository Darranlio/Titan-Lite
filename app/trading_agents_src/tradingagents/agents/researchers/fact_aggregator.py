from typing import Any, Dict
from langchain_core.messages import HumanMessage
from tradingagents.agents.utils.agent_states import AgentState

def create_fact_aggregator(llm: Any):
    """
    Creates a Fact Aggregator node that synthesizes reports from all analysts
    into a single structured fact sheet.
    """
    
    def fact_aggregator_node(state: AgentState) -> Dict[str, Any]:
        symbol = state.get("company_of_interest", "the company")
        
        # Collect reports
        market = state.get("market_report", "No market data available.")
        social = state.get("sentiment_report", "No social media sentiment available.")
        news = state.get("news_report", "No recent news available.")
        fundamentals = state.get("fundamentals_report", "No fundamental data available.")
        
        prompt = f"""
[Role] You are the Lead Investment Auditor following the "Thesis-First" Research Framework.
[Objective] Synthesize multi-source raw research into a structured "Investment Fact Sheet" for {symbol}.

### [Source Inputs]
- Market Performance: {market}
- Sentiment & Social: {social}
- News & Events: {news}
- Fundamentals & Financials: {fundamentals}

### [Synthesis Protocol]
1. **Driver Decomposition**: Identify the 3-5 core drivers of value (e.g., Revenue growth, Margin expansion, Regulatory tailwinds).
2. **Consensus vs. Asymmetry**: Distinguish between "Priced-in Consensus" (what everyone knows) and "Potential Asymmetry" (what the market might be missing).
3. **Data Hierarchy & Conflict Resolution**: 
   - Weightage: SEC Filings > Official Press Releases > Sell-side Research > Social Media.
   - Flag any "Data Discrepancies" in bold.
4. **Killing Conditions**: For each primary bullish factor, define a specific "Falsifiability Criterion" (e.g., "Logic fails if OPM drops below X%").

### [Output Requirements]
- **Zero Fabrication**: If data is missing, mark as [MISSING]. Do not hallucinate.
- **Tone**: Analytical, objective, and cold. Use professional investment nomenclature.
- **Structure**: Markdown with clear headers for [Drivers], [Key Metrics], [Catalysts], and [Risks].

This Fact Sheet will be the *Sole Source of Truth* for the subsequent Bull/Bear Debate.
"""
        
        # Use LLM to aggregate
        response = llm.invoke([HumanMessage(content=prompt)])
        
        return {
            "fact_sheet": response.content,
            "sender": "Fact Aggregator"
        }
        
    return fact_aggregator_node
