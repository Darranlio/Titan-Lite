import requests
from config import settings
from tenacity import retry, stop_after_attempt, wait_fixed

class FinnhubProvider:
    """
    Finnhub 适配器：获取机构级新闻与情绪
    """
    def __init__(self):
        self.api_key = settings.FINNHUB_API_KEY
        self.base_url = "https://finnhub.io/api/v1"

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_company_news(self, symbol, _from=None, _to=None):
        """获取公司专业新闻"""
        if not self.api_key: return []
        
        url = f"{self.base_url}/company-news"
        params = {
            "symbol": symbol,
            "token": self.api_key,
            "from": _from or "2024-01-01", # 默认参数
            "to": _to or "2026-12-31"
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            return resp.json()[:10] # 仅取前10条高质量新闻
        except:
            return []

    def get_insider_transactions(self, symbol):
        """获取高管/内幕交易记录"""
        url = f"{self.base_url}/stock/insider-transactions"
        params = {"symbol": symbol, "token": self.api_key}
        try:
            resp = requests.get(url, params=params, timeout=10)
            return resp.json().get('data', [])[:5]
        except:
            return []

finnhub_provider = FinnhubProvider()
