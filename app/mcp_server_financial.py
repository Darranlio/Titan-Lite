import sys
import os
import json
import pandas as pd
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Ensure the app directory is in the path for importing strategies
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 初始化 FastMCP 服务端
mcp = FastMCP("Titan Financial Data Server")

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
        "Hang Seng": "^HSI",
        "CSI 300": "000300.SS"
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

@mcp.tool()
def get_ashare_specifics(symbol: str) -> str:
    """
    获取 A 股特有的高增量数据 (通过 AkShare)。
    :param symbol: A 股 6 位数字代码 (如 600519)
    """
    try:
        import akshare as ak
        # 获取实时行情快照
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == symbol]
        if row.empty:
            return json.dumps({"error": f"Symbol {symbol} not found in A-Share market"})
        
        row_dict = row.iloc[0].to_dict()
        result = {
            "name": row_dict.get('名称'),
            "pe_ttm": row_dict.get('市盈率-动态'),
            "pb": row_dict.get('市净率'),
            "turnover_rate": f"{row_dict.get('换手率')}%",
            "total_mv": f"{row_dict.get('总市值')/1e8:.2f}亿",
            "volume_ratio": row_dict.get('量比'),
            "main_inflow": f"{row_dict.get('主力净流入')/1e4:.2f}万"
        }
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_sector_status() -> str:
    """
    获取全球主要行业板块表现 (CN + US)。
    """
    results = {"CN": {}, "US": {}}
    
    # 临时禁用代理，确保直连 AkShare A股数据源
    env_backup = {k: os.environ.get(k) for k in ["http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"]}
    for k in env_backup:
        os.environ[k] = ""
        
    try:
        import akshare as ak
        # 1. A股行业表现 (取当日涨幅前 5)
        df_cn = ak.stock_board_industry_name_em()
        if df_cn is not None and not df_cn.empty:
            df_cn = df_cn.sort_values(by="涨跌幅", ascending=False).head(5)
            for _, row in df_cn.iterrows():
                results["CN"][row['板块名称']] = f"{row['涨跌幅']}%"
    except Exception as e:
        results["CN_error"] = str(e)
    finally:
        # 恢复代理设置，防止破坏美股/大模型 API 请求的科学上网代理
        for k, v in env_backup.items():
            if v is not None:
                os.environ[k] = v
            else:
                if k in os.environ: del os.environ[k]
                
    try:
        # 2. 美股行业表现 (通过核心行业 ETF 代理)
        sector_etfs = {
            "科技(XLK)": "XLK", "金融(XLF)": "XLF", "医疗(XLV)": "XLV", 
            "能源(XLE)": "XLE", "消费(XLY)": "XLY", "半导体(SOXX)": "SOXX"
        }
        import yfinance as yf
        for name, symbol in sector_etfs.items():
            t = yf.Ticker(symbol)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                change = (hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]
                results["US"][name] = f"{change:.2%}"
    except Exception as e:
        results["US_error"] = str(e)
        
    return json.dumps(results)

@mcp.tool()
def run_hurst_and_ou_analysis(prices: list[float]) -> str:
    """
    计算价格序列的均值回归特征，包含赫斯特指数（Hurst Exponent）和 Ornstein-Uhlenbeck (O-U) 过程的半衰期。
    :param prices: 价格收盘价数组 (时间正序，最旧在最前，最新在最后)
    """
    try:
        from strategies.mean_reversion import calculate_hurst_exponent, estimate_half_life
        if len(prices) < 10:
            return json.dumps({"error": "Insufficient data points, at least 10 required."})
        
        hurst = calculate_hurst_exponent(prices)
        half_life = estimate_half_life(prices)
        
        regime = "mean_reversion" if hurst < 0.45 else "momentum" if hurst > 0.55 else "random_walk"
        
        return json.dumps({
            "hurst": round(hurst, 4),
            "half_life_days": round(half_life, 2) if half_life else None,
            "regime": regime,
            "interpretation": f"Hurst 指数为 {hurst:.4f}，表现为 {regime} 特征。"
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def run_pairs_trading_analysis(prices_a: list[float], prices_b: list[float], symbol_a: str = "A", symbol_b: str = "B") -> str:
    """
    计算两只股票之间的协整关系和配对交易特征（配对分析）。
    :param prices_a: 股票 A 的价格历史收盘价数组 (时间正序)
    :param prices_b: 股票 B 的价格历史收盘价数组 (时间正序)
    :param symbol_a: 股票 A 的代码
    :param symbol_b: 股票 B 的代码
    """
    try:
        from strategies.statistical_arbitrage import analyze_pairs_trading
        if len(prices_a) != len(prices_b):
            min_len = min(len(prices_a), len(prices_b))
            prices_a = prices_a[-min_len:]
            prices_b = prices_b[-min_len:]
        
        if len(prices_a) < 30:
            return json.dumps({"error": "Insufficient data, at least 30 data points required."})
        
        # 转换为倒序 (最新在前) 以供策略层调用
        rev_a = list(reversed(prices_a))
        rev_b = list(reversed(prices_b))
        
        res = analyze_pairs_trading(rev_a, rev_b)
        
        return json.dumps({
            "symbol_a": symbol_a,
            "symbol_b": symbol_b,
            "signal": res.signal,
            "spread_z_score": round(res.spread_z_score, 4),
            "cointegration_score": round(res.cointegration_score, 4),
            "half_life": res.half_life if res.half_life != float('inf') else None,
            "hedge_ratio": round(res.hedge_ratio, 4),
            "details": res.details
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_momentum_metrics(prices: list[float]) -> str:
    """
    计算股票的历史动量指标，包括相对强弱、趋势强度和趋势加速度。
    :param prices: 价格历史收盘价数组 (时间正序，最旧在前，最新在最后)
    """
    try:
        from strategies.momentum import analyze_momentum
        if len(prices) < 30:
            return json.dumps({"error": "Insufficient data, at least 30 data points required."})
            
        prices_list = list(reversed(prices))
        res = analyze_momentum(prices_list)
        
        return json.dumps({
            "signal_strength": round(res.signal_strength, 4),
            "trend_strength": round(res.trend_strength, 4),
            "trend_acceleration": round(res.acceleration, 4),
            "optimal_lookback": res.optimal_lookback,
            "details": res.details
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def run_composite_quant_decision(
    symbol: str, 
    prices: list[float], 
    target_price: float = 0.0, 
    peer_prices: list[float] = None
) -> str:
    """
    运行综合量化决策计算（复合研判），输出包括期望超额收益（Edge）、凯利仓位配资在内的完整量化报告。
    :param symbol: 股票代码
    :param prices: 股票价格数组 (时间正序，最旧在最前，最新在最后)
    :param target_price: 分析师目标价，默认 0.0 则使用当前价格作为估值基底
    :param peer_prices: 同行业对比股票价格数组 (用于统计套利配对)
    """
    try:
        from strategies.analysis import (
            run_signal_analysis,
            run_risk_analysis,
            run_execution_analysis,
            run_stat_arb_analysis,
            synthesize_decision
        )
        
        if len(prices) < 30:
            return json.dumps({"error": "Insufficient prices data, at least 30 data points required."})
            
        prices_list = list(reversed(prices))
        current_price = prices[-1]
        intrinsic_estimates = [target_price] if target_price > 0 else [current_price]
        
        sig_res = run_signal_analysis(symbol, prices_list)
        risk_res = run_risk_analysis(symbol, prices_list)
        exec_res = run_execution_analysis(symbol, trade_value=1_000_000, market_cap=10_000_000_000, avg_daily_volume=5_000_000)
        
        peer_list = list(reversed(peer_prices)) if peer_prices else None
        arb_res = run_stat_arb_analysis(symbol, prices_list, intrinsic_estimates=intrinsic_estimates, peer_prices=peer_list)
        
        dec = synthesize_decision(
            symbol,
            signal_analysis=sig_res,
            risk_analysis=risk_res,
            execution_analysis=exec_res,
            stat_arb_analysis=arb_res
        )
        
        return json.dumps({
            "symbol": symbol,
            "signal": dec.signal.value,
            "confidence": round(dec.confidence, 2),
            "expected_edge_bps": round(dec.statistical_edge, 4),
            "recommended_position_pct": round(dec.position_sizing.recommended_size_pct, 4),
            "kelly_fraction": round(dec.position_sizing.kelly_fraction, 4),
            "market_regime": sig_res.get('pattern_recognition', {}).get('regime', 'sideways'),
            "realized_volatility": round(risk_res.get('volatility', {}).get('realized_volatility', 0), 4),
            "max_drawdown": round(risk_res.get('drawdown', {}).get('max_drawdown', 0), 4),
            "key_factors": dec.key_factors,
            "risks": dec.risks,
            "reasoning": dec.reasoning
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

# === A-Share Data Source Endpoints (Supplemented from a_stock_data) ===

@mcp.tool()
def get_ashare_valuation_details(symbol: str) -> str:
    """
    获取 A 股全面的机构预测与估值指标 (包括 Forward PE、PEG 及 PE 消化年数)。
    :param symbol: 6位 A 股股票代码 (如 600519)
    """
    try:
        import a_stock_data
        # Clean symbol to 6-digit
        code = "".join(filter(str.isdigit, symbol))
        res = a_stock_data.full_valuation(code)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_ashare_concept_sectors(symbol: str) -> str:
    """
    获取 A 股个股所属的概念板块、行业板块及地域板块归属。
    :param symbol: 6位 A 股股票代码
    """
    try:
        import a_stock_data
        code = "".join(filter(str.isdigit, symbol))
        res = a_stock_data.eastmoney_concept_blocks(code)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_ashare_fund_flow_intraday(symbol: str) -> str:
    """
    获取 A 股个股当日盘中分钟级的主力/大单/中单/小单资金净流入。
    :param symbol: 6位 A 股股票代码
    """
    try:
        import a_stock_data
        code = "".join(filter(str.isdigit, symbol))
        res = a_stock_data.eastmoney_fund_flow_minute(code)
        return json.dumps(res[:100], ensure_ascii=False) # Limit size for token efficiency
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_ashare_fund_flow_history(symbol: str) -> str:
    """
    获取 A 股个股过去 120 天日级的主力/超大单/大单/中单/小单净流入历史。
    :param symbol: 6位 A 股股票代码
    """
    try:
        import a_stock_data
        code = "".join(filter(str.isdigit, symbol))
        res = a_stock_data.stock_fund_flow_120d(code)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_ashare_dragon_tiger_board(symbol: str, trade_date: str) -> str:
    """
    获取 A 股个股历史龙虎榜上榜明细，包含买卖席位 Top5 及机构动向。
    :param symbol: 6位 A 股股票代码
    :param trade_date: 交易日期 (YYYY-MM-DD)
    """
    try:
        import a_stock_data
        code = "".join(filter(str.isdigit, symbol))
        res = a_stock_data.dragon_tiger_board(code, trade_date)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_ashare_lockup_expiry(symbol: str, trade_date: str, forward_days: int = 90) -> str:
    """
    获取 A 股限售股解禁日历预警（包含历史解禁和未来待解禁）。
    :param symbol: 6位 A 股股票代码
    :param trade_date: 基准交易日期 (YYYY-MM-DD)
    :param forward_days: 向后预测天数，默认 90 天
    """
    try:
        import a_stock_data
        code = "".join(filter(str.isdigit, symbol))
        res = a_stock_data.lockup_expiry(code, trade_date, forward_days)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_ashare_shareholder_changes(symbol: str) -> str:
    """
    获取 A 股个股历季股东户数环比变化，判断筹码集中度。
    :param symbol: 6位 A 股股票代码
    """
    try:
        import a_stock_data
        code = "".join(filter(str.isdigit, symbol))
        res = a_stock_data.holder_num_change(code)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_ashare_margin_trading(symbol: str) -> str:
    """
    获取 A 股个股融资融券余额及变动明细 (两融余额)。
    :param symbol: 6位 A 股股票代码
    """
    try:
        import a_stock_data
        code = "".join(filter(str.isdigit, symbol))
        res = a_stock_data.margin_trading(code)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_ashare_block_trades(symbol: str) -> str:
    """
    获取 A 股个股大宗交易明细，含成交溢价率和买卖营业部。
    :param symbol: 6位 A 股股票代码
    """
    try:
        import a_stock_data
        code = "".join(filter(str.isdigit, symbol))
        res = a_stock_data.block_trade(code)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_ashare_announcements(symbol: str, page_size: int = 15) -> str:
    """
    检索巨潮资讯中关于该 A 股公司的全量公告与官方申报材料。
    :param symbol: 6位 A 股股票代码
    :param page_size: 拉取公告条数
    """
    try:
        import a_stock_data
        code = "".join(filter(str.isdigit, symbol))
        res = a_stock_data.cninfo_announcements(code, page_size)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_ashare_analyst_reports(symbol: str, max_pages: int = 3) -> str:
    """
    拉取东财该 A 股的个股分析师研报列表与三年期 EPS 预测数据。
    :param symbol: 6位 A 股股票代码
    """
    try:
        import a_stock_data
        code = "".join(filter(str.isdigit, symbol))
        res = a_stock_data.eastmoney_reports(code, max_pages)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    mcp.run()
