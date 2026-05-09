import pytest
import pandas as pd
from app.valuation_screener import ValuationScreenerV2_1

def test_screener_logic(mocker):
    # Mock news_spider, fmp_provider, data_provider
    mocker.patch("app.valuation_screener.news_spider.get_trending_tickers", return_value=["AAPL"])
    mock_fmp = mocker.patch("app.valuation_screener.fmp_provider")
    mock_dp = mocker.patch("app.valuation_screener.data_provider")
    
    # Setup data: 
    # Use side_effect to give AAPL a higher upside
    def mock_history(symbol):
        return pd.Series([100])
    
    def mock_estimates(symbol):
        if symbol == "AAPL":
            return {"estimatedPriceAvg": 200} # 100% upside
        return {"estimatedPriceAvg": 110}     # 10% upside
        
    mock_dp.get_history_price.side_effect = mock_history
    mock_fmp.get_analyst_estimates.side_effect = mock_estimates
    mock_fmp.get_key_metrics.return_value = {"peRatioTTM": 20, "roeTTM": 0.15}
    
    vs = ValuationScreenerV2_1()
    vs.min_upside = 0.10
    results = vs.run()
    
    # Check if AAPL is in the results (others might be there due to hardcoded backbone)
    symbols = [r['symbol'] for r in results]
    assert "AAPL" in symbols
    
    aapl_res = next(r for r in results if r['symbol'] == "AAPL")
    assert aapl_res['upside'] == 1.0
    assert aapl_res['pe'] == 20
