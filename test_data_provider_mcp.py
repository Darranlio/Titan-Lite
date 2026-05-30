import sys
import os
import pandas as pd

# 将 app 目录加入路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from data_provider import data_provider

def test_data_provider():
    print("--- [Test] 正在验证 DataProvider (MCP 驱动版) ---")
    
    symbol = "NVDA"
    
    # 1. 测试历史价格
    print(f"\n[Action] 正在获取 {symbol} 历史价格...")
    prices = data_provider.get_history_price(symbol, days=5)
    print(f"[Result] 价格数据类型: {type(prices)}")
    print(f"[Result] 价格数据内容:\n{prices}")
    
    if prices.empty:
        print("[Error] 无法获取价格数据")
    
    # 2. 测试分析师信息
    print(f"\n[Action] 正在获取 {symbol} 分析师信息...")
    info = data_provider.get_analyst_info(symbol)
    print(f"[Result] 分析师信息: {info}")
    
    # 3. 测试汇率
    print("\n[Action] 正在获取实时汇率...")
    rates = data_provider.get_exchange_rates()
    print(f"[Result] 汇率: {rates}")

    # 4. 测试市场基准
    print("\n[Action] 正在获取市场基准...")
    benchmarks = data_provider.get_market_benchmarks()
    print(f"[Result] 市场基准: {benchmarks}")

    print("\n--- [Test] DataProvider 验证完成 ---")

if __name__ == "__main__":
    test_data_provider()
