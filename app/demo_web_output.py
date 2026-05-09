from strategy import TitanStrategyV2
from unittest.mock import MagicMock
import os

def demo_full_pipeline():
    print(">>> 模拟 V2 全流程执行 (含 Mock Agent)...")
    
    # 1. 实例化策略
    strat = TitanStrategyV2()
    
    # 2. Mock Agent Bridge 避免调用真实 LLM (因为没有 API Key)
    import agent_bridge
    agent_bridge.agent_bridge.analyze_ticker = MagicMock(return_value={
        "action": "BUY",
        "quantity": "5%",
        "rationale": "该标的基本面强劲，投行预期涨幅空间大。虽然短期有宏观波动，但多智能体辩论认为其估值修复逻辑未改变。AI 分析显示近期新闻多为中性偏好。",
        "debate_summary": "Bull Researcher: 认为该股 AI 业务增长超预期；Bear Researcher: 担忧监管压力。最终 PM 认为收益风险比极佳。"
    })

    # 3. 拦截 WeCom 推送 (避免产生干扰)
    strat.bot.send_markdown = MagicMock()
    strat.push_to_wecom = MagicMock()

    # 4. 执行 (由于是 Mock，这里会快速完成扫描并生成网页报告)
    # 我们只对第一个标的进行模拟生成
    candidates = [
        {'symbol': '0700.HK', 'current_price': 471.4, 'target_price': 724.4, 'upside': 0.53, 'analysts': 45, 'rating': 'buy'},
        {'symbol': 'NVDA', 'current_price': 135.5, 'target_price': 185.0, 'upside': 0.36, 'analysts': 60, 'rating': 'strong_buy'}
    ]
    
    for item in candidates:
        symbol = item['symbol']
        decision = agent_bridge.agent_bridge.analyze_ticker(symbol)
        strat.save_to_web(symbol, item, decision)
        print(f"已生成网页研报: docs/projects/titan-lite/reports/{symbol}.md")

if __name__ == "__main__":
    demo_full_pipeline()
