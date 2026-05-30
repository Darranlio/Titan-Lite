import sys
import os
import json
import pandas as pd
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# 初始化 FastMCP 服务端
mcp = FastMCP("Titan Financial Data Server")

# 模拟之前的 data_provider 逻辑，但将其封装为 MCP Tool
@mcp.tool()
def get_stock_price(symbol: str, days: int = 5, start_date: str = None, end_date: str = None) -> str:
    """
    获取指定股票的历史收盘价数据。
    :param symbol: 股票代码 (如 AAPL, 0700.HK)
    :param days: 获取过去几天的行情 (若未提供 start_date)
    :param start_date: 开始日期 (YYYY-MM-DD)
    :param end_date: 结束日期 (YYYY-MM-DD)
    """
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        if start_date:
            hist = ticker.history(start=start_date, end=end_date or datetime.now().strftime('%Y-%m-%d'))
        else:
            hist = ticker.history(period=f"{days}d")
            
        if hist.empty:
            return json.dumps({"error": f"No data found for {symbol}"})
        
        # 转化为精简的 JSON 格式
        data = hist['Close'].to_dict()
        # 将 timestamp 转化为字符串
        data = {k.strftime('%Y-%m-%d'): round(v, 2) for k, v in data.items()}
        return json.dumps({"symbol": symbol, "prices": data})
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def search_symbols(query: str) -> str:
    """
    根据关键词搜索股票代码和公司名称。
    """
    print(f">>> [MCP Tool] Searching symbols for: {query}")
    try:
        import yfinance as yf
        # yfinance 的 search 功能可以根据关键词返回候选列表
        results = yf.Search(query, max_results=5).quotes
        simplified = []
        for r in results:
            simplified.append({
                "symbol": r.get("symbol"),
                "name": r.get("longname") or r.get("shortname"),
                "exch": r.get("exchange")
            })
        return json.dumps(simplified)
    except Exception as e:
        return json.dumps([])

@mcp.tool()
def get_analyst_forecast(symbol: str) -> str:
    """
    获取分析师对个股的目标价和建议。
    """
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info
        result = {
            "currentPrice": info.get("currentPrice") or info.get("previousClose") or 0,
            "targetMeanPrice": info.get("targetMeanPrice") or 0,
            "recommendationKey": info.get("recommendationKey") or "hold",
            "peRatioTTM": info.get("trailingPE") or 0,
            "roeTTM": info.get("returnOnEquity") or 0,
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown")
        }
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_company_news(symbol: str, limit: int = 5) -> str:
    """获取公司最新新闻"""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        news = ticker.news
        return json.dumps(news[:limit])
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_financial_highlights(symbol: str) -> str:
    """获取财务报表核心亮点"""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info
        result = {
            "rev_growth": info.get('revenueGrowth'),
            "net_margin": info.get('profitMargins'),
            "fcf": info.get('freeCashflow'),
            "ebitda_margin": info.get('ebitdaMargins'),
            "debt_to_equity": info.get('debtToEquity')
        }
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_company_details(symbol: str) -> str:
    """获取公司简介"""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info
        result = {
            "summary_en": info.get('longBusinessSummary', 'No summary available.'),
            "full_name": info.get('longName', symbol),
            "website": info.get('website', '#'),
            "employees": info.get('fullTimeEmployees', 'N/A')
        }
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_market_benchmarks() -> str:
    """获取全球核心指数表现"""
    indices = {
        "S&P 500": "SPY",
        "Nasdaq 100": "QQQ",
        "Dow Jones": "DIA",
        "Hang Seng": "^HSI"
    }
    results = {}
    import yfinance as yf
    for name, symbol in indices.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if not hist.empty:
                change = (hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]
                results[name] = f"{change:.2%}"
        except:
            results[name] = "Data N/A"
    return json.dumps(results)

@mcp.tool()
def get_exchange_rates() -> str:
    """获取实时汇率 (USDHKD, USDCNY)"""
    rates = {"USD": 1.0, "HKD": 7.8, "CNY": 7.2}
    import yfinance as yf
    try:
        pairs = ["USDHKD=X", "USDCNY=X"]
        for pair in pairs:
            ticker = yf.Ticker(pair)
            hist = ticker.history(period="1d")
            if not hist.empty:
                currency = pair[3:6]
                rates[currency] = round(hist['Close'].iloc[-1], 4)
        return json.dumps(rates)
    except:
        return json.dumps(rates)

if __name__ == "__main__":
    # 使用 stdio 传输运行服务端
    mcp.run()
