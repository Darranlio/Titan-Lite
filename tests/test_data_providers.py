import pytest
import pandas as pd
from app.data_provider import DataProvider
from app.finnhub_provider import FinnhubProvider
from app.fmp_provider import FMPProvider

def test_data_provider_history(mocker):
    # Mock yfinance Ticker.history
    mock_ticker = mocker.patch("yfinance.Ticker")
    mock_instance = mock_ticker.return_value
    mock_instance.history.return_value = pd.DataFrame({"Close": [100, 101]}, index=pd.to_datetime(["2024-01-01", "2024-01-02"]))
    
    dp = DataProvider()
    res = dp.get_history_price("AAPL")
    assert not res.empty
    assert res.iloc[0] == 100
    assert res.name == "AAPL"

def test_finnhub_provider_news(mocker):
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.json.return_value = [{"headline": "Test News"}]
    
    fp = FinnhubProvider()
    fp.api_key = "test"
    res = fp.get_company_news("AAPL")
    assert len(res) == 1
    assert res[0]["headline"] == "Test News"

def test_fmp_provider_estimates(mocker):
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.json.return_value = [{"estimatedPriceAvg": 150}]
    
    fmp = FMPProvider()
    fmp.api_key = "test"
    res = fmp.get_analyst_estimates("AAPL")
    assert res["estimatedPriceAvg"] == 150
