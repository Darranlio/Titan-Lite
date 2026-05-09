import requests
from config import settings
from tenacity import retry, stop_after_attempt, wait_fixed

class FMPProvider:
    """
    Financial Modeling Prep (FMP) 适配器：深度基本面与精准估值
    """
    def __init__(self):
        self.api_key = settings.FMP_API_KEY
        self.base_url = "https://financialmodelingprep.com/api/v3"

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_analyst_estimates(self, symbol):
        """获取华尔街分析师共识预期"""
        if not self.api_key: return {}
        
        url = f"{self.base_url}/analyst-estimates/{symbol}"
        params = {"apikey": self.api_key}
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            return data[0] if data else {}
        except:
            return {}

    def get_key_metrics(self, symbol):
        """获取核心财务指标 (PE, ROE等)"""
        url = f"{self.base_url}/key-metrics-ttm/{symbol}"
        params = {"apikey": self.api_key}
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            return data[0] if data else {}
        except:
            return {}

fmp_provider = FMPProvider()
