

def create_bull_researcher(llm):
    def bull_node(state) -> dict:
        symbol = state.get("company_of_interest", "the company")
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bull_history = investment_debate_state.get("bull_history", "")

        current_response = investment_debate_state.get("current_response", "")
        fact_sheet = state.get("fact_sheet", "No fact sheet available.")

        prompt = f"""
[Role] You are a highly-analytical Bull Researcher. Your goal is to build a rigorous, data-driven investment thesis for {symbol} based *exclusively* on the provided Fact Sheet.

[Task]
1. **Thesis Construction**: Identify the most powerful value drivers from the Fact Sheet.
2. **Growth & Competitive Edge**: Emphasize scalability, moat, and positive financial trajectories.
3. **Refutation**: If a Bear argument exists, use specific quantitative data from the Fact Sheet to debunk their risks or show why the rewards outweigh them.
4. **Logical Sparring**: Directly address the Bear Analyst's points. Do not just list facts; engage in a dynamic logical debate.

[Constraints]
- **Sole Source of Truth**: Use ONLY the provided "Investment Fact Sheet". Never introduce external information or hallucinations.
- **Language**: Use professional English financial terminology.
- **Tone**: Persuasive but strictly evidence-based.

### [Investment Fact Sheet]
{fact_sheet}

### [Debate History]
{history}

### [Current Bear Argument]
{current_response}

Please deliver your argument:
"""

        response = llm.invoke(prompt)

        argument = f"Bull Analyst: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bull_history": bull_history + "\n" + argument,
            "bear_history": investment_debate_state.get("bear_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bull_node
