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
    将数据抓取逻辑解耦到 MCP Server 中
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
            sys_logger.info(f"   [DataProvider] 正在连接 MCP Client...")
            client = await get_mcp_client()
            sys_logger.info(f"   [DataProvider] 正在通过 MCP 调用 get_stock_price ({symbol})...")
            params = {"symbol": symbol}
            if start_date:
                params["start_date"] = start_date
                params["end_date"] = end_date
            else:
                params["days"] = days
            res = await client.call_tool("get_stock_price", params)
            sys_logger.info(f"   [DataProvider] MCP 调用完成")
            return json.loads(res) if res else {}
        
        try:
            data = self._run_sync(_fetch())
            if not data or "error" in data: 
                sys_logger.info(f"   [DataProvider] 数据为空或含错: {data.get('error') if data else 'Empty'}")
                return pd.Series()
            
            series = pd.Series(data['prices'])
            series.name = symbol
            series.index = pd.to_datetime(series.index)
            return series
        except Exception as e:
            sys_logger.info(f"   [DataProvider] MCP 获取行情异常: {e}")
            return pd.Series()

    def get_analyst_info(self, symbol):
        """通过 MCP 获取分析师预测与基本面"""
        async def _fetch():
            sys_logger.info(f"   [DataProvider] 正在通过 MCP 调用 get_analyst_forecast ({symbol})...")
            client = await get_mcp_client()
            res = await client.call_tool("get_analyst_forecast", {"symbol": symbol})
            return json.loads(res) if res else {}
        
        try:
            result = self._run_sync(_fetch())
            return result
        except Exception as e:
            sys_logger.info(f"   [DataProvider] MCP 获取分析师数据异常: {e}")
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
        """获取公司详情 (含 LLM 翻译)"""
        async def _fetch():
            client = await get_mcp_client()
            res = await client.call_tool("get_company_details", {"symbol": symbol})
            return json.loads(res) if res else {}
        
        try:
            data = self._run_sync(_fetch())
            if not data or "error" in data: return {"summary": "获取失败", "full_name": symbol}
            
            summary_en = data.get('summary_en', '')
            summary_cn = summary_en
            
            # 翻译逻辑保留在 DataProvider 层 (作为 Orchestrator 的一部分)
            if summary_en and summary_en != 'No summary available.':
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
                    prompt = f"请将以下这段股票业务简介翻译为专业的金融中文。要求：准确、精炼、符合中文表达习惯。\n\n原文：\n{summary_en}"
                    resp = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}], temperature=0.1)
                    summary_cn = resp.choices[0].message.content.strip()
                except Exception as e:
                    print(f"翻译简介失败: {e}")
            
            return {
                "summary": summary_cn,
                "full_name": data.get('full_name', symbol),
                "website": data.get('website', '#'),
                "employees": data.get('employees', 'N/A')
            }
        except: return {"summary": "获取失败", "full_name": symbol}

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

    async def search_ticker_async(self, query):
        """通过 MCP 模糊搜索代码 (异步版)"""
        try:
            client = await get_mcp_client()
            res = await client.call_tool("search_symbols", {"query": query})
            return json.loads(res) if res else []
        except Exception as e:
            sys_logger.info(f"   [DataProvider] 异步搜索异常: {e}")
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
