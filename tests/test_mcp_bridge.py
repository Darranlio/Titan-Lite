import asyncio
import sys
import os

# 将 app 目录加入路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from mcp_client import get_mcp_client

async def test_bridge():
    print("--- [Test] 正在启动 Titan-Alpha MCP 链路测试 ---")
    client = await get_mcp_client()
    
    # 测试工具 1: 获取行情
    print("\n[Action] 正在通过 MCP 请求 NVDA 行情数据...")
    price_json = await client.call_tool("get_stock_price", {"symbol": "NVDA", "days": 3})
    print(f"[Result] 行情数据: {price_json}")
    
    # 测试工具 2: 获取预测
    print("\n[Action] 正在通过 MCP 请求 NVDA 分析师预测...")
    forecast_json = await client.call_tool("get_analyst_forecast", {"symbol": "NVDA"})
    print(f"[Result] 预测数据: {forecast_json}")
    
    await client.disconnect()
    print("\n--- [Test] 链路测试完成 ---")

if __name__ == "__main__":
    asyncio.run(test_bridge())
