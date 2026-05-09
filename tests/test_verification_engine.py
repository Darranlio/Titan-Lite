import pytest
import pandas as pd
import numpy as np
from app.verification_engine import VerificationEngine

def test_check_divergence(mocker):
    # Mock yfinance Ticker.history for OBV calculation
    mock_ticker = mocker.patch("yfinance.Ticker")
    mock_instance = mock_ticker.return_value
    
    # Case: Price UP, OBV DOWN (Negative Divergence)
    # Day 0: 10, Vol 1000, OBV 0
    # Day 1: 15 (UP), Vol 10, OBV 10
    # Day 2: 14 (DOWN), Vol 1000, OBV -990
    # Day 3: 13 (DOWN), Vol 1000, OBV -1990
    # Day 4: 16 (UP), Vol 10, OBV -1980
    # Result: Price 10 -> 16 (UP), OBV 0 -> -1980 (DOWN)
    df = pd.DataFrame({
        "Close": [10, 15, 14, 13, 16],
        "Volume": [1000, 10, 1000, 1000, 10]
    }, index=pd.date_range("2024-01-01", periods=5))
    mock_instance.history.return_value = df
    
    ve = VerificationEngine()
    res = ve.check_divergence("AAPL")
    assert "警告" in res
    assert "量价背离" in res

def test_get_insider_signal(mocker):
    # Mock finnhub_provider
    mock_fp = mocker.patch("app.verification_engine.finnhub_provider")
    mock_fp.get_insider_transactions.return_value = [
        {"transactionText": "Sale of 1000 shares"},
        {"transactionText": "Sale of 500 shares"}
    ]
    
    ve = VerificationEngine()
    res = ve.get_insider_signal("AAPL")
    assert "🚨 预警" in res
    assert "2 次减持" in res

def test_verify_news(mocker):
    # Mock OpenAI client
    mock_openai = mocker.patch("app.verification_engine.OpenAI")
    mock_client = mock_openai.return_value
    mock_client.chat.completions.create.return_value.choices[0].message.content = "新闻看起来非常可靠。"
    
    ve = VerificationEngine()
    content, score = ve.verify_news("AAPL", [{"headline": "Test"}])
    assert score == 0.8
    assert "可靠" in content
