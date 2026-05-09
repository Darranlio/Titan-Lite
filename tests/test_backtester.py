import pytest
import pandas as pd
from app.backtester import Backtester

def test_backtest_math(mocker):
    # Mock data_provider
    mock_dp = mocker.patch("app.backtester.data_provider")
    # Simulate a 10% gain over 5 days
    prices = [100, 102, 105, 108, 110]
    mock_dp.get_history_price.return_value = pd.Series(prices)
    
    bt = Backtester()
    res = bt.run_simple_backtest("AAPL", days=5)
    
    assert res['symbol'] == "AAPL"
    # Total return = 110/100 - 1 = 0.1
    assert pytest.approx(res['total_return'], 0.01) == 0.1
    assert 'sharpe_ratio' in res
    assert 'max_drawdown' in res

def test_forecast_logic(mocker):
    mock_dp = mocker.patch("app.backtester.data_provider")
    # Upward trend
    prices = list(range(100, 200)) # 100 days of data
    mock_dp.get_history_price.return_value = pd.Series(prices)
    
    bt = Backtester()
    res = bt.forecast_price("AAPL")
    
    assert res['trend'] == "看涨"
    assert res['forecast_target'] > 199
