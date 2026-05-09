from valuation_screener import valuation_screener
from data_provider import data_provider

def test():
    print("--- 步骤 1: 运行估值筛选器 (Screener) ---")
    results = valuation_screener.run()
    
    if not results:
        print("未发现符合条件的标的。可能是 API 限制或市场波动。")
        return

    for item in results:
        print(f"找到潜力股: {item['symbol']}")
        print(f"  现价: {item['current_price']}, 目标价: {item['target_price']}, 预期涨幅: {item['upside']:.2%}")
        
    print("\n--- 步骤 2: 模拟数据获取 (News) ---")
    news = data_provider.get_company_news(results[0]['symbol'], limit=2)
    print(f"[{results[0]['symbol']}] 最新新闻数量: {len(news)}")

if __name__ == "__main__":
    test()
