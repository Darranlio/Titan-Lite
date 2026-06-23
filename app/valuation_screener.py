from data_provider import data_provider
from news_spider import news_spider
from fmp_provider import fmp_provider
from config import settings
from sys_logger import sys_logger
import time
import asyncio

class ValuationScreenerV2_1:
    """
    估值筛选器 V2.1：使用 FMP 机构级数据 + AkShare A股支持 (Async 版)
    """
    def __init__(self):
        # 降低门槛至 5%（原为 10%），让更多稳健白马股/热门股进入深研池
        self.min_upside = 0.05 

    async def run(self, market='Global'):
        sys_logger.info(f">>> [Screener] 启动 {market} 市场价值洼地扫描...", stage="Discovery", task_type="batch")
        
        # 1. 构建不同市场的候选集
        universe = []
        if market == 'A-Share' or market == 'Global':
            universe += self._get_ashare_universe()
        if market == 'HK' or market == 'Global':
            universe += self._get_hk_universe()
        if market == 'US' or market == 'Global':
            universe += self._get_us_universe()
            
        universe = list(set(universe))
        sys_logger.info(f"  [Screener] 初始搜索空间：{len(universe)} 只标的", stage="Discovery", task_type="batch")
        
        qualified = []
        
        async def audit_symbol_async(symbol):
            try:
                # 针对 A股进行代码转换
                fetch_symbol = symbol
                if symbol.isdigit() and len(symbol) == 6:
                    if symbol.startswith(('60', '68')): fetch_symbol = f"{symbol}.SS"
                    elif symbol.startswith(('00', '30')): fetch_symbol = f"{symbol}.SZ"
                    elif symbol.startswith('4', '8', '9'): fetch_symbol = f"{symbol}.BJ"

                # 优先调取机构数据 (FMP 仍然是同步请求，暂时保留)
                from concurrent.futures import ThreadPoolExecutor
                loop = asyncio.get_event_loop()
                
                # FMP 请求
                estimates = await loop.run_in_executor(None, fmp_provider.get_analyst_estimates, fetch_symbol)
                metrics = await loop.run_in_executor(None, fmp_provider.get_key_metrics, fetch_symbol)
                
                # 获取实时价格 (使用异步 MCP)
                # 修改 data_provider 增加异步接口或直接调用 MCP
                from mcp_client import get_mcp_client
                import json
                client = await get_mcp_client()
                
                # 获取价格
                price_res = await client.call_tool("get_stock_price", {"symbol": fetch_symbol, "days": 5})
                price_data = json.loads(price_res) if price_res else {}
                if not price_data or "prices" not in price_data:
                    return None
                
                prices = list(price_data['prices'].values())
                current_price = prices[-1] if prices else 0
                if current_price <= 0: return None
                
                target_price = estimates.get('estimatedPriceAvg', 0)
                
                # 获取分析师预测 (使用异步 MCP)
                forecast_res = await client.call_tool("get_analyst_forecast", {"symbol": fetch_symbol})
                y_info = json.loads(forecast_res) if forecast_res else {}
                
                if target_price <= 0:
                    target_price = y_info.get('targetMeanPrice', 0)
                
                pe = metrics.get('peRatioTTM', 0)
                if not pe: pe = y_info.get('peRatioTTM', 0)
                
                roe = metrics.get('roeTTM', 0)
                if not roe: roe = y_info.get('roeTTM', 0)
                
                sector = y_info.get('sector', 'Unknown')
                industry = y_info.get('industry', 'Unknown')
                source = "FMP Institutional" if estimates.get('estimatedPriceAvg') else "yfinance Analytics"

                if target_price > 0:
                    upside = (target_price - current_price) / current_price
                    if upside >= self.min_upside:
                        return {
                            'symbol': symbol,
                            'current_price': round(current_price, 2),
                            'target_price': round(target_price, 2),
                            'upside': upside,
                            'pe': pe or 0,
                            'roe': roe or 0,
                            'sector': sector,
                            'industry': industry,
                            'rating': source
                        }
            except Exception:
                pass
            return None

        # 异步并发执行
        tasks = [audit_symbol_async(s) for s in universe]
        # 控制并发数，防止触发 API 限制
        chunk_size = 10
        for i in range(0, len(tasks), chunk_size):
            batch = tasks[i:i+chunk_size]
            results = await asyncio.gather(*batch)
            for res in results:
                if res:
                    sys_logger.info(f"  [Screener] 发现潜力标的: {res['symbol']} (预期 +{res['upside']:.1%})", stage="Discovery", task_type="batch")
                    qualified.append(res)
            
            p = 10 + int((min(i + chunk_size, len(universe)) / len(universe)) * 15)
            sys_logger.info(f"  [Screener] 已完成 {min(i + chunk_size, len(universe))}/{len(universe)} 只标的的探测...", stage="Discovery", progress=p, task_type="batch")
            # 稍微停顿，避免过快
            await asyncio.sleep(0.2)
                
        qualified.sort(key=lambda x: x['upside'], reverse=True)
        sys_logger.info(f">>> [Screener] 扫描结束，共发现 {len(qualified)} 只符合准入条件的标的。", stage="Discovery", task_type="batch")
        return qualified

    def _get_us_universe(self):
        """美股动态搜索：结合 Trending + Most Active"""
        print("  [Screener] 正在动态探测美股热点与活跃标的...")
        trending = news_spider.get_trending_tickers()
        active = news_spider.get_us_most_active()
        
        # 基础蓝筹股兜底
        blue_chips = ["NVDA", "AAPL", "TSLA", "MSFT", "GOOGL", "META", "AMZN", "AMD", "NFLX", "AVGO"]
        
        combined = list(set(trending + active + blue_chips))
        return combined # 移除硬编码限制，返回全量标的

    def _get_ashare_universe(self):
        """利用 AkShare 获取 A股全市场高成交额标的 (不仅限于沪深300)"""
        print("  [Screener] 正在通过 AkShare 探测 A股高热度标的...")
        import os

        # 临时彻底禁用代理，确保直连国内数据源
        env_backup = {k: os.environ.get(k) for k in ["http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"]}
        for k in env_backup:
            os.environ[k] = ""

        try:
            import akshare as ak
            # 获取全市场 A股实时行情
            df = ak.stock_zh_a_spot_em()

            if df is not None and not df.empty:
                # 选取所有高成交额的标的，不强制截断前 60
                df = df.sort_values(by="成交额", ascending=False)
                return df['代码'].tolist()
            return ["600519", "000858", "601318", "601888", "002594", "300750"] # 扩充兜底
        except Exception as e:
            print(f"  [Screener] AkShare A股探测失败: {e}")
            # 当网络连接东方财富失败时，使用预设的 A 股核心蓝筹池作为兜底
            return [
                "600519", "000858", "601318", "601888", "002594", "300750",
                "600036", "000333", "601166", "600030", "600900", "002415",
                "000002", "600276", "601012", "000568", "600887", "601816",
                "300059", "002304", "000001", "603259"
            ]
        finally:
            # 恢复代理设置
            for k, v in env_backup.items():
                if v is not None:
                    os.environ[k] = v
                else:
                    if k in os.environ: del os.environ[k]

    def _get_hk_universe(self):
        """利用 AkShare 获取港股核心资产 (恒生科技 + 高成交额标的)"""
        print("  [Screener] 正在通过 AkShare 提取港股核心资产...")
        import os

        # 临时彻底禁用代理
        env_backup = {k: os.environ.get(k) for k in ["http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"]}
        for k in env_backup:
            os.environ[k] = ""

        try:
            import akshare as ak
            # 获取港股主板行情
            df = ak.stock_hk_spot_em()
            if df is not None and not df.empty:
                # 不再截断前 30 只
                df = df.sort_values(by="成交额", ascending=False)
                # AkShare 港股代码通常是 5 位，yf 需要 4 位加 .HK
                return [f"{s[-4:]}.HK" if len(s) >= 4 else f"{s}.HK" for s in df['代码'].tolist()]
            return ["0700.HK", "9988.HK", "3690.HK", "1211.HK", "9888.HK", "1810.HK"]
        except Exception as e:
            print(f"  [Screener] AkShare 港股提取失败: {e}")
            return ["0700.HK", "9988.HK", "3690.HK", "1211.HK", "9888.HK", "1810.HK"]
        finally:
            # 恢复代理设置
            for k, v in env_backup.items():
                if v is not None:
                    os.environ[k] = v
                else:
                    if k in os.environ: del os.environ[k]
valuation_screener = ValuationScreenerV2_1()
