from data_provider import data_provider
from news_spider import news_spider
from fmp_provider import fmp_provider
from config import settings
import time

class ValuationScreenerV2_1:
    """
    估值筛选器 V2.1：使用 FMP 机构级数据
    """
    def __init__(self):
        self.min_upside = 0.10 

    def run(self):
        print(">>> [V2.1] 启动全市场价值洼地扫描 (地毯式审计)...")
        
        # 1. 构建全宇宙候选集 (Universe Expansion)
        # a. 核心骨干
        backbone = ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NFLX", "AVGO", "ORCL", "CRM", "AMD", "INTC"]
        # b. 热门标的
        trending = news_spider.get_trending_tickers()
        # c. 板块代表 (覆盖半导体、SaaS、中概、金融、AI)
        sector_leaders = [
            "ASML", "TSM", "ARM", "MU", # 半导体
            "NOW", "SNOW", "PLTR", "WDAY", # SaaS/AI
            "BABA", "PDD", "JD", "0700.HK", "9988.HK", "3690.HK", # 中概
            "COIN", "MSTR", "MARA", # 加密/高波动
            "JPM", "GS", "V", "MA" # 金融科技
        ]
        
        # 合并去重，构建约 50-80 只标的的深度池
        universe = list(set(trending + backbone + sector_leaders))
        print(f"  [Screener] 初始搜索空间已扩展至 {len(universe)} 只标的")
        
        qualified = []
        
        # 2. 逐一审计估值
        for symbol in universe:
            try:
                # 优先调取机构数据
                estimates = fmp_provider.get_analyst_estimates(symbol)
                metrics = fmp_provider.get_key_metrics(symbol)
                
                # 获取实时价格
                price_series = data_provider.get_history_price(symbol, days=5)
                if price_series.empty: continue
                current_price = price_series.iloc[-1]
                
                target_price = estimates.get('estimatedPriceAvg', 0)
                pe = metrics.get('peRatioTTM', 0)
                roe = metrics.get('roeTTM', 0)
                sector = "Unknown"
                industry = "Unknown"
                source = "FMP Institutional"

                if target_price <= 0:
                    y_info = data_provider.get_analyst_info(symbol)
                    target_price = y_info.get('targetMeanPrice', 0)
                    pe = y_info.get('peRatioTTM', 0)
                    roe = y_info.get('roeTTM', 0)
                    sector = y_info.get('sector', 'Unknown')
                    industry = y_info.get('industry', 'Unknown')
                    source = "yfinance Analytics"

                if target_price > 0:
                    upside = (target_price - current_price) / current_price
                    # 只要预期涨幅超过阈值，全部入选，不再只取前5
                    if upside >= self.min_upside:
                        print(f"  [Screener] 发现潜力标的: {symbol} (预期 +{upside:.1%})")
                        qualified.append({
                            'symbol': symbol,
                            'current_price': round(current_price, 2),
                            'target_price': round(target_price, 2),
                            'upside': upside,
                            'pe': pe or 0,
                            'roe': roe or 0,
                            'sector': sector,
                            'industry': industry,
                            'rating': source
                        })
                
                time.sleep(0.05) # 稍微提速
            except Exception as e:
                print(f"审计 {symbol} 失败: {e}")
                
        # 按涨幅排序
        qualified.sort(key=lambda x: x['upside'], reverse=True)
        print(f">>> [Screener] 扫描结束，共发现 {len(qualified)} 只符合准入条件的标的。")
        return qualified

valuation_screener = ValuationScreenerV2_1()
