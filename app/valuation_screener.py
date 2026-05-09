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
        
        # 2. 逐一审计估值 (切换至 FMP)
        for symbol in candidates:
            try:
                # 获取 FMP 专家预测
                estimates = fmp_provider.get_analyst_estimates(symbol)
                metrics = fmp_provider.get_key_metrics(symbol)
                
                # 获取当前价格 (yfinance 依然最快)
                current_price = data_provider.get_history_price(symbol).iloc[-1]
                
                # FMP 提供的平均目标价
                target_price = estimates.get('estimatedPriceAvg', 0)
                
                if target_price > 0:
                    upside = (target_price - current_price) / current_price
                    
                    if upside >= self.min_upside:
                        qualified.append({
                            'symbol': symbol,
                            'current_price': round(current_price, 2),
                            'target_price': round(target_price, 2),
                            'upside': upside,
                            'pe': metrics.get('peRatioTTM', 0),
                            'roe': metrics.get('roeTTM', 0),
                            'rating': "FMP Institutional"
                        })
                
                time.sleep(0.2)
            except Exception as e:
                print(f"审计 {symbol} 失败: {e}")
                
        qualified.sort(key=lambda x: x['upside'], reverse=True)
        return qualified[:5]

valuation_screener = ValuationScreenerV2_1()
