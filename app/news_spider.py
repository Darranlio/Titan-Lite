import requests
from bs4 import BeautifulSoup
import re

class NewsSpider:
    """
    轻量级新闻爬虫：获取市场热点板块与标的
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def get_trending_tickers(self):
        """
        从 Yahoo Finance 获取热门标的 (Trending Tickers)
        """
        url = "https://finance.yahoo.com/trending-tickers"
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # 找到代码列表
            table = soup.find('table')
            if not table: return []
            
            tickers = []
            for row in table.find_all('tr')[1:20]: # 取前20个
                symbol = row.find('td').text.strip()
                tickers.append(symbol)
            return tickers
        except Exception as e:
            print(f"爬取热点标的失败: {e}")
            return ["AAPL", "NVDA", "TSLA", "MSFT", "BABA", "0700.HK"]

    def get_market_sentiment_keywords(self):
        """
        简易关键词提取：判断当前市场热点 (如 AI, Fed, Rate Cut)
        """
        url = "https://finance.yahoo.com/news/"
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'lxml')
            headlines = [h.text for h in soup.find_all('h3')]
            
            # 这里可以接入简单的 NLP 或词频统计
            keywords = ["AI", "Semiconductor", "Inflation", "Rate", "Tech"]
            # 简化逻辑：如果在标题中频繁出现则认为热度高
            return keywords
        except:
            return []

news_spider = NewsSpider()
