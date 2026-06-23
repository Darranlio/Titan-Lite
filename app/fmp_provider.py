import requests
from config import settings
from tenacity import retry, stop_after_attempt, wait_fixed

class FMPProvider:
    """
    Financial Modeling Prep (FMP) 适配器：深度基本面与精准估值
    """
    def __init__(self):
        self.api_key = settings.FMP_API_KEY
        self.base_url = "https://financialmodelingprep.com/stable"

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_analyst_estimates(self, symbol):
        """获取华尔街分析师共识预期"""
        if not self.api_key: return {}
        
        url = f"{self.base_url}/analyst-estimates"
        params = {"symbol": symbol, "apikey": self.api_key}
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code != 200:
                print(f"FMP API 响应异常: HTTP {resp.status_code}")
                return {}
            # 增加对空内容的检查
            if not resp.text.strip():
                return {}
            data = resp.json()
            if isinstance(data, dict) and "Error Message" in data:
                print(f"FMP API 错误: {data['Error Message']}")
                return {}
            return data[0] if data and isinstance(data, list) else {}
        except Exception as e:
            print(f"FMP 请求异常 ({symbol}): {e}")
            return {}

    def get_key_metrics(self, symbol):
        """获取核心财务指标 (PE, ROE等)"""
        if not self.api_key: return {}
        url = f"{self.base_url}/key-metrics-ttm"
        params = {"symbol": symbol, "apikey": self.api_key}
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code != 200 or not resp.text.strip():
                return {}
            data = resp.json()
            if isinstance(data, dict) and "Error Message" in data:
                print(f"FMP API 错误 (Metrics): {data['Error Message']}")
                return {}
            return data[0] if data and isinstance(data, list) else {}
        except:
            return {}

fmp_provider = FMPProvider()
