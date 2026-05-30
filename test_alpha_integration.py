import asyncio
import sys
import os

# 将 app 目录加入路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'app', 'trading_agents_src'))

from agent_bridge import agent_bridge

async def test_alpha_orchestrator():
    print("--- [Integration Test] Titan-Alpha Orchestrator (Research-then-Debate) ---")
    
    symbol = "NVDA"
    context = "Initial context: Market looks stable, AI demand remains high."
    
    # 运行深度分析
    # 这将触发：
    # 1. 各 Analysts 收集数据 (via MCP)
    # 2. FactAggregator 整合事实 (English)
    # 3. Bull/Bear Researcher 辩论 (English)
    # 4. Portfolio Manager 裁决 (Chinese)
    
    print(f"\n[Phase] Starting analysis for {symbol}...")
    decision = agent_bridge.analyze_ticker(symbol, context_extra=context)
    
    if decision:
        print("\n" + "="*50)
        print(">>> [FINAL DECISION] <<<")
        print(f"Action: {decision.get('action')}")
        print("-" * 20)
        print(f"Rationale:\n{decision.get('rationale')}")
        print("="*50)
        
        # 验证 Fact Sheet 是否存在
        # 注意：由于我们在 AgentBridge 中没有显式解出 fact_sheet，
        # 但它在 graph 的状态流中运行。我们可以通过日志观察。
    else:
        print("[Error] Analysis failed to produce a decision.")

if __name__ == "__main__":
    asyncio.run(test_alpha_orchestrator())
