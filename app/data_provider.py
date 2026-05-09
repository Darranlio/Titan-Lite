import yfinance as ticker_info
import yfinance as yf
import pandas as pd
import time
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_fixed
from datetime import datetime, timedelta
from config import settings

class DataProvider:
    """
    Titan-Lite V2 数据适配层 (美港股优先)
    基于 yfinance 和自定义爬虫获取行情与投行目标价
    """

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_history_price(symbol, start_date=None, end_date=None, interval="1d"):
        """
        获取个股历史行情 (yfinance)
        :param symbol: 股票代码 (如 'AAPL', '0700.HK')
        """
        try:
            # yfinance 获取数据
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval=interval)
            if df.empty: return pd.Series()
            
            # 标准化清洗
            series = df['Close']
            series.name = symbol
            return series
        except Exception as e:
            print(f"yfinance 获取行情失败 {symbol}: {e}")
            return pd.Series()

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_analyst_info(symbol):
        """
        获取投行目标价与评级 (Analyst Targets)
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 提取关键估值字段
            result = {
                'currentPrice': info.get('currentPrice'),
                'targetMeanPrice': info.get('targetMeanPrice'),
                'targetLowPrice': info.get('targetLowPrice'),
                'targetHighPrice': info.get('targetHighPrice'),
                'recommendationKey': info.get('recommendationKey'), # e.g., 'buy', 'strong_buy'
                'numberOfAnalystOpinions': info.get('numberOfAnalystOpinions')
            }
            
            # 计算潜在涨幅
            if result['currentPrice'] and result['targetMeanPrice']:
                result['upside'] = (result['targetMeanPrice'] - result['currentPrice']) / result['currentPrice']
            else:
                result['upside'] = 0
                
            return result
        except Exception as e:
            print(f"获取分析师数据失败 {symbol}: {e}")
            return {}

    @staticmethod
    def get_company_news(symbol, limit=5):
        """
        获取公司最新新闻
        """
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            return news[:limit]
        except:
            return []

    @staticmethod
    def get_market_trending(market="US"):
        """
        获取市场热点标的 (初步通过 yfinance 模拟，后期可接入新闻爬虫)
        """
        # 这里先占位，后续 Phase 2 会开发专门的 news_spider
        if market == "US":
            return ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMZN", "META"]
        else:
            return ["0700.HK", "9988.HK", "3690.HK", "1810.HK", "9888.HK"]

# 导出单例
data_provider = DataProvider()
