

def create_bear_researcher(llm):
    def bear_node(state) -> dict:
        symbol = state.get("company_of_interest", "the company")
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bear_history = investment_debate_state.get("bear_history", "")

        current_response = investment_debate_state.get("current_response", "")
        fact_sheet = state.get("fact_sheet", "No fact sheet available.")

        prompt = f"""
[Role] You are a skeptical, highly-analytical Bear Researcher. Your goal is to identify critical risks and build a data-driven case against investing in {symbol} based *exclusively* on the provided Fact Sheet.

[Task]
1. **Risk Identification**: Highlight financial instability, overvaluation, market saturation, or competitive threats.
2. **Weakness Analysis**: Emphasize declining innovation, regulatory hurdles, or macroeconomic vulnerabilities.
3. **Refutation**: Use specific quantitative data from the Fact Sheet to expose flaws or over-optimistic assumptions in the Bull argument.
4. **Logical Sparring**: Directly attack the Bull Analyst's logical foundations. Do not just list facts; engage in a dynamic logical debate.

[Constraints]
- **Sole Source of Truth**: Use ONLY the provided "Investment Fact Sheet". Never introduce external information or hallucinations.
- **Language**: Use professional English financial terminology.
- **Tone**: Skeptical, analytical, and cold.

### [Investment Fact Sheet]
{fact_sheet}

### [Debate History]
{history}

### [Current Bull Argument]
{current_response}

Please deliver your argument:
"""

        response = llm.invoke(prompt)

        argument = f"Bear Analyst: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bear_history": bear_history + "\n" + argument,
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bear_node
