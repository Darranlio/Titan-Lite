import asyncio
import json
import pandas as pd
import nest_asyncio
from mcp_client import get_mcp_client
from config import settings
from sys_logger import sys_logger

# 允许在已运行的事件循环中嵌套运行 (兼容 FastAPI)
nest_asyncio.apply()

class DataProvider:
    """
    Titan-Lite V2 数据适配层 (MCP 驱动版)
    将数据抓取逻辑解耦到 MCP Server 中。
    严格作为 Reader，不包含业务逻辑或 LLM 调用。
    """

    def _run_sync(self, coro):
        """同步运行异步任务的辅助函数"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return asyncio.get_event_loop().run_until_complete(coro)

    def get_history_price(self, symbol, start_date=None, end_date=None, days=30, **kwargs):
        """通过 MCP 获取历史行情"""
        async def _fetch():
            client = await get_mcp_client()
            params = {"symbol": symbol}
            if start_date:
                params["start_date"] = start_date
                params["end_date"] = end_date
            else:
                params["days"] = days
            res = await client.call_tool("get_stock_price", params)
            return json.loads(res) if res else {}
        
        try:
            data = self._run_sync(_fetch())
            if not data or "error" in data: 
                return pd.Series()
            
            series = pd.Series(data['prices'])
            series.name = symbol
            series.index = pd.to_datetime(series.index)
            return series
        except Exception:
            return pd.Series()

    def get_analyst_info(self, symbol):
        """通过 MCP 获取分析师预测与基本面"""
        async def _fetch():
            client = await get_mcp_client()
            res = await client.call_tool("get_analyst_forecast", {"symbol": symbol})
            return json.loads(res) if res else {}
        
        try:
            return self._run_sync(_fetch())
        except:
            return {}

    def get_company_news(self, symbol, limit=5):
        """通过 MCP 获取公司新闻"""
        async def _fetch():
            client = await get_mcp_client()
            res = await client.call_tool("get_company_news", {"symbol": symbol, "limit": limit})
            return json.loads(res) if res else []
        
        try:
            return self._run_sync(_fetch())
        except: return []

    def get_financial_highlights(self, symbol):
        """通过 MCP 获取财务亮点"""
        async def _fetch():
            client = await get_mcp_client()
            res = await client.call_tool("get_financial_highlights", {"symbol": symbol})
            return json.loads(res) if res else {}
        
        try:
            return self._run_sync(_fetch())
        except: return {}

    def get_company_details(self, symbol):
        """获取公司原始详情 (不再包含 LLM 翻译)"""
        async def _fetch():
            client = await get_mcp_client()
            res = await client.call_tool("get_company_details", {"symbol": symbol})
            return json.loads(res) if res else {}
        
        try:
            data = self._run_sync(_fetch())
            if not data or "error" in data: 
                return {"summary_en": "获取失败", "full_name": symbol}
            return data
        except: 
            return {"summary_en": "获取失败", "full_name": symbol}

    def get_ashare_specifics(self, symbol):
        """通过 MCP 获取 A股专用指标"""
        async def _fetch():
            # 剥离后缀，A股 MCP Tool 接收 6 位数字
            clean_symbol = symbol.split('.')[0]
            client = await get_mcp_client()
            res = await client.call_tool("get_ashare_specifics", {"symbol": clean_symbol})
            return json.loads(res) if res else {}
        
        try:
            return self._run_sync(_fetch())
        except: return {}

    def get_market_benchmarks(self):
        """通过 MCP 获取市场基准"""
        async def _fetch():
            client = await get_mcp_client()
            res = await client.call_tool("get_market_benchmarks")
            return json.loads(res) if res else {}
        
        try:
            return self._run_sync(_fetch())
        except: return {}

    def get_exchange_rates(self):
        """通过 MCP 获取汇率"""
        async def _fetch():
            client = await get_mcp_client()
            res = await client.call_tool("get_exchange_rates")
            return json.loads(res) if res else {"USD": 1.0, "HKD": 7.8, "CNY": 7.2}
        
        try:
            return self._run_sync(_fetch())
        except: return {"USD": 1.0, "HKD": 7.8, "CNY": 7.2}

    def get_sector_status(self):
        """通过 MCP 获取全球主要行业板块表现 (CN + US)"""
        async def _fetch():
            client = await get_mcp_client()
            res = await client.call_tool("get_sector_status")
            return json.loads(res) if res else {"CN": {}, "US": {}}
        
        try:
            return self._run_sync(_fetch())
        except: return {"CN": {}, "US": {}}


    async def search_ticker_async(self, query):
        """通过 MCP 模糊搜索代码 (异步版)"""
        try:
            client = await get_mcp_client()
            res = await client.call_tool("search_symbols", {"query": query})
            return json.loads(res) if res else []
        except Exception:
            return []

    def search_ticker(self, query):
        """通过 MCP 模糊搜索代码"""
        async def _fetch():
            client = await get_mcp_client()
            res = await client.call_tool("search_symbols", {"query": query})
            return json.loads(res) if res else []
        
        try:
            return self._run_sync(_fetch())
        except: return []

# 导出单例
data_provider = DataProvider()
