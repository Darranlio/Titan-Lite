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
        print(">>> [V2.1] 启动机构级价值洼地扫描 (FMP Powered)...")
        
        # 1. 发现候选集
        trending = news_spider.get_trending_tickers()
        backbone = ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "0700.HK", "9988.HK"]
        candidates = list(set(trending + backbone))
        
        qualified = []
        
        # 2. 逐一审计估值
        for symbol in candidates:
            try:
                # 尝试获取 FMP 专家预测
                estimates = fmp_provider.get_analyst_estimates(symbol)
                metrics = fmp_provider.get_key_metrics(symbol)
                
                # 获取当前价格 (yfinance 依然最快)
                price_series = data_provider.get_history_price(symbol)
                if price_series.empty:
                    print(f"  [Screener] 跳过 {symbol}: 无法获取价格数据")
                    continue
                current_price = price_series.iloc[-1]
                
                # 数据源融合：FMP 优先，yfinance 兜底
                target_price = estimates.get('estimatedPriceAvg', 0)
                pe = metrics.get('peRatioTTM', 0)
                roe = metrics.get('roeTTM', 0)
                sector = "Unknown"
                industry = "Unknown"
                source = "FMP Institutional"

                # 兜底逻辑：如果 FMP 数据为空，切换到 yfinance
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
                    print(f"  [Screener] {symbol}: {sector} | {industry} | 涨幅 {upside:.2%}")
                    
                    if upside >= self.min_upside:
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
                
                time.sleep(0.1)
            except Exception as e:
                print(f"审计 {symbol} 失败: {e}")
                
        qualified.sort(key=lambda x: x['upside'], reverse=True)
        return qualified[:5]

valuation_screener = ValuationScreenerV2_1()
