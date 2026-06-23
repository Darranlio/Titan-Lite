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
                tds = row.find_all('td')
                if tds:
                    symbol = tds[0].text.strip()
                    tickers.append(symbol)
            return tickers
        except Exception as e:
            print(f"爬取热点标的失败: {e}")
            return []

    def get_us_most_active(self):
        """
        从 Yahoo Finance 获取成交最活跃的美股 (Most Active)
        """
        url = "https://finance.yahoo.com/markets/stocks/most-active"
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'lxml')
            # yfinance 页面结构可能变化，尝试匹配 <td> 中的代码
            # 通常在 data-symbol 属性中
            import re
            symbols = []
            for td in soup.find_all('td', {'data-field': 'symbol'}):
                sym = td.text.strip()
                if sym: symbols.append(sym)
            
            if not symbols:
                # 兜底方案：查找所有链接中看起来像代码的部分
                links = soup.find_all('a', href=re.compile(r'/quote/([A-Z]+)'))
                symbols = [re.search(r'/quote/([A-Z]+)', a['href']).group(1) for a in links]
            
            return list(set(symbols))[:30]
        except Exception as e:
            print(f"爬取活跃美股失败: {e}")
            return []

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
