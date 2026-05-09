import pytest
from app.agent_bridge import AgentBridge

def test_analyze_ticker_structure(mocker):
    # Mock TradingAgentsGraph
    mock_graph = mocker.patch("app.agent_bridge.TradingAgentsGraph")
    mock_instance = mock_graph.return_value
    
    # 模拟 propagate 的返回值
    # 返回值 1: final_state (dict)
    # 返回值 2: rating (str)
    mock_final_state = {
        "final_trade_decision": "Test rationale",
        "market_report": "Market data",
        "sentiment_report": "Sentiment data",
        "news_report": "News data",
        "fundamentals_report": "Fundamentals data",
        "investment_debate_state": {"history": "Debate 1"},
        "risk_debate_state": {"history": "Debate 2"}
    }
    mock_rating = "BUY"
    mock_instance.propagate.return_value = (mock_final_state, mock_rating)
    
    bridge = AgentBridge()
    decision = bridge.analyze_ticker("AAPL")
    
    # 验证结构是否正确
    assert isinstance(decision, dict)
    assert decision["action"] == "BUY"
    assert "rationale" in decision
    assert decision["reports"]["market"] == "Market data"
    assert decision["debates"]["investment"]["history"] == "Debate 1"
    
    print("\n✅ AgentBridge 结构验证通过，未发现 TypeError")

if __name__ == "__main__":
    # 手动运行测试的简易方式
    pytest.main([__file__])
