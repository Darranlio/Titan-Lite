import asyncio
import pandas as pd
from data_provider import data_provider
from news_spider import news_spider
from fmp_provider import fmp_provider
from config import settings
from sys_logger import sys_logger


# ============================================================
# 纯函数层（无网络 I/O，可单测）
# ============================================================

def _ashare_upside(peg, max_upside=None):
    """
    A股预期涨幅由 PEG 推导：upside = clamp(1/peg - 1, 0, max_upside)。
    PEG < 1 才有正空间；PEG 无效（None / 非正 / inf）返回 0。
    """
    if max_upside is None:
        max_upside = settings.SCREENER_MAX_UPSIDE
    if peg is None or peg == float("inf") or peg <= 0:
        return 0.0
    upside = (1.0 / peg) - 1.0
    if upside <= 0:
        return 0.0
    return min(upside, max_upside)


def _compute_quality_score(candidate, max_upside=None, min_roe=None):
    """
    多维质量评分（0-100）：预期涨幅 50 + 分析师覆盖 20 + ROE 20 + 市值档 10。
    仅用于排序，不参与准入判定。
    """
    if max_upside is None:
        max_upside = settings.SCREENER_MAX_UPSIDE
    if min_roe is None:
        min_roe = settings.SCREENER_MIN_ROE

    upside = candidate.get('upside', 0) or 0
    analyst_count = candidate.get('analyst_count', 0) or 0
    roe = candidate.get('roe', 0) or 0
    mcap = candidate.get('market_cap', 0) or 0

    # 预期涨幅：0 → 0 分，满幅 → 50 分
    upside_score = min(upside / max_upside, 1.0) * 50

    # 分析师覆盖：0 → 0 分，20 家及以上 → 20 分
    analyst_score = min(analyst_count, 20) / 20.0 * 20

    # ROE：低于下限 → 0 分，下限+20pct 及以上 → 20 分
    roe_score = min(max(roe - min_roe, 0) / 0.20, 1.0) * 20

    # 市值档：越大越稳（千亿/五百亿/百亿/以下）
    if mcap >= 1e11:
        mcap_score = 10
    elif mcap >= 5e10:
        mcap_score = 7
    elif mcap >= 1e10:
        mcap_score = 4
    else:
        mcap_score = 2

    return round(upside_score + analyst_score + roe_score + mcap_score, 1)


def _passes_quality_gates(candidate, market):
    """
    质量闸门：涨幅区间、市值下限、股价下限(US)、分析师覆盖、ROE。
    任一不满足即剔除。
    """
    upside = candidate.get('upside', 0) or 0
    if upside < settings.SCREENER_MIN_UPSIDE:
        return False
    if upside > settings.SCREENER_MAX_UPSIDE:
        return False

    mcap = candidate.get('market_cap', 0) or 0
    if market == 'US':
        if mcap < settings.SCREENER_MIN_MARKET_CAP_US:
            return False
        if (candidate.get('current_price', 0) or 0) < settings.SCREENER_MIN_PRICE_US:
            return False
    elif market == 'A-Share':
        if mcap < settings.SCREENER_MIN_MARKET_CAP_ASHARE:
            return False
    elif market == 'HK':
        if mcap < settings.SCREENER_MIN_MARKET_CAP_HK:
            return False

    if (candidate.get('analyst_count', 0) or 0) < settings.SCREENER_MIN_ANALYST_COUNT:
        return False

    if (candidate.get('roe', 0) or 0) < settings.SCREENER_MIN_ROE:
        return False

    return True


# ============================================================
# 估值筛选器 V2.2：分市场数据源 + 质量闸门 + 多维评分
# ============================================================

class ValuationScreenerV2_1:
    """
    估值筛选器 V2.2：
    - US：FMP `/price-target-consensus` 目标价 + key-metrics，yfinance 兜底
    - A股：同花顺一致预期 full_valuation（Forward PE / PEG / 覆盖数），PEG 推导 upside
    - HK：yfinance 分析师目标价
    全部候选经过统一质量闸门与多维评分。
    """
    def __init__(self):
        self.min_upside = settings.SCREENER_MIN_UPSIDE

    async def run(self, market='Global'):
        sys_logger.info(f">>> [Screener] 启动 {market} 市场价值洼地扫描...", stage="Discovery", task_type="batch")

        universe = []
        if market in ('A-Share', 'Global'):
            universe += self._get_ashare_universe()
        if market in ('HK', 'Global'):
            universe += self._get_hk_universe()
        if market in ('US', 'Global'):
            universe += self._get_us_universe()

        # 按 symbol 去重，保留首次出现的市场归属
        seen = set()
        deduped = []
        for item in universe:
            sym = item.get('symbol')
            if sym and sym not in seen:
                seen.add(sym)
                deduped.append(item)
        universe = deduped

        sys_logger.info(f"  [Screener] 初始搜索空间：{len(universe)} 只标的", stage="Discovery", task_type="batch")
        if not universe:
            return []

        loop = asyncio.get_running_loop()
        qualified = []

        def audit(item):
            return self._audit(item)

        # 同步数据源（FMP/requests/akshare）放到线程池，避免阻塞事件循环
        from concurrent.futures import ThreadPoolExecutor
        max_workers = 10
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [loop.run_in_executor(executor, audit, item) for item in universe]
            done = 0
            total = len(universe)
            for fut in asyncio.as_completed(futures):
                try:
                    res = await fut
                except Exception:
                    res = None
                done += 1
                if res:
                    qualified.append(res)
                    sys_logger.info(
                        f"  [Screener] 发现潜力标的: {res['symbol']} "
                        f"(预期 +{res['upside']:.1%}, 质量分 {res.get('quality_score', 0)})",
                        stage="Discovery", task_type="batch"
                    )
                if done % 10 == 0 or done == total:
                    p = 10 + int((done / total) * 15)
                    sys_logger.info(f"  [Screener] 已完成 {done}/{total} 只标的的探测...", stage="Discovery", progress=p, task_type="batch")

        qualified.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        sys_logger.info(f">>> [Screener] 扫描结束，共发现 {len(qualified)} 只符合质量闸门的标的。", stage="Discovery", task_type="batch")
        return qualified

    # ---------------- 审计分发 ----------------

    def _audit(self, item):
        """对单只标的执行分市场审计，返回通过质量闸门的候选 dict 或 None。"""
        symbol = item.get('symbol')
        market = item.get('market')
        try:
            if market == 'A-Share':
                cand = self._audit_ashare(symbol)
            elif market == 'HK':
                cand = self._audit_hk(symbol)
            else:
                cand = self._audit_us(symbol)
        except Exception:
            cand = None

        if not cand:
            return None
        if not _passes_quality_gates(cand, market):
            return None

        cand['quality_score'] = _compute_quality_score(cand)
        return cand

    def _audit_us(self, symbol):
        """美股：FMP 目标价共识 + 关键指标优先，yfinance 兜底。"""
        pt = fmp_provider.get_price_target(symbol) or {}
        fmp_target = pt.get('targetConsensus', 0) or 0

        metrics = fmp_provider.get_key_metrics(symbol) or {}

        y_info = data_provider.get_analyst_info(symbol) or {}
        current_price = y_info.get('currentPrice', 0) or 0
        if current_price <= 0:
            prices = data_provider.get_history_price(symbol, days=5)
            if not prices.empty:
                current_price = prices.iloc[-1]
        if current_price <= 0:
            return None

        target_price = fmp_target or y_info.get('targetMeanPrice', 0) or 0
        if target_price <= 0:
            return None

        # PE：yfinance trailingPE 优先；FMP 无直接 PE 字段，用 earningsYieldTTM 推导
        pe = y_info.get('peRatioTTM', 0) or 0
        if not pe:
            ey = metrics.get('earningsYieldTTM', 0) or 0
            pe = (1.0 / ey) if ey > 0 else 0
        # ROE：FMP returnOnEquityTTM 优先，yfinance 兜底
        roe = metrics.get('returnOnEquityTTM', 0) or y_info.get('roeTTM', 0) or 0
        sector = y_info.get('sector', 'Unknown')
        industry = y_info.get('industry', 'Unknown')
        market_cap = y_info.get('marketCap', 0) or metrics.get('marketCap', 0) or 0
        analyst_count = y_info.get('numberOfAnalystOpinions', 0) or 0
        rating = "FMP 目标价共识" if fmp_target > 0 else "yfinance 分析师"

        upside = (target_price - current_price) / current_price
        return {
            'symbol': symbol,
            'market': 'US',
            'current_price': round(current_price, 2),
            'target_price': round(target_price, 2),
            'upside': upside,
            'pe': pe or 0,
            'roe': roe or 0,
            'sector': sector,
            'industry': industry,
            'rating': rating,
            'market_cap': market_cap or 0,
            'analyst_count': analyst_count or 0,
        }

    def _audit_ashare(self, symbol):
        """A股：同花顺一致预期 full_valuation，PEG 推导 upside。"""
        val = data_provider.get_ashare_valuation(symbol) or {}
        if not val or "error" in val:
            return None

        price = val.get('price', 0) or 0
        if price <= 0:
            return None

        upside = _ashare_upside(val.get('peg'))
        if upside <= 0:
            return None

        pe = val.get('pe_ttm', 0) or val.get('pe_fwd', 0) or 0
        pb = val.get('pb', 0) or 0
        roe = (pb / pe) if (pe and pe > 0) else 0

        mcap_yi = val.get('mcap_yi', 0) or 0  # 单位：亿
        market_cap = mcap_yi * 1e8  # 换算为元

        target_price = price * (1 + upside)
        return {
            'symbol': symbol,
            'market': 'A-Share',
            'current_price': round(price, 2),
            'target_price': round(target_price, 2),
            'upside': upside,
            'pe': round(pe, 2) if pe else 0,
            'roe': roe,
            'sector': 'A股',
            'industry': val.get('name', symbol),
            'rating': '同花顺一致预期 (PEG 推导)',
            'market_cap': market_cap,
            'analyst_count': val.get('analyst_count', 0) or 0,
        }

    def _audit_hk(self, symbol):
        """港股：yfinance 分析师目标价。"""
        y_info = data_provider.get_analyst_info(symbol) or {}
        current_price = y_info.get('currentPrice', 0) or 0
        if current_price <= 0:
            prices = data_provider.get_history_price(symbol, days=5)
            if not prices.empty:
                current_price = prices.iloc[-1]
        if current_price <= 0:
            return None

        target_price = y_info.get('targetMeanPrice', 0) or 0
        if target_price <= 0:
            return None

        pe = y_info.get('peRatioTTM', 0) or 0
        roe = y_info.get('roeTTM', 0) or 0
        sector = y_info.get('sector', 'Unknown')
        industry = y_info.get('industry', 'Unknown')
        market_cap = y_info.get('marketCap', 0) or 0
        analyst_count = y_info.get('numberOfAnalystOpinions', 0) or 0

        upside = (target_price - current_price) / current_price
        return {
            'symbol': symbol,
            'market': 'HK',
            'current_price': round(current_price, 2),
            'target_price': round(target_price, 2),
            'upside': upside,
            'pe': pe or 0,
            'roe': roe or 0,
            'sector': sector,
            'industry': industry,
            'rating': 'yfinance 分析师',
            'market_cap': market_cap or 0,
            'analyst_count': analyst_count or 0,
        }

    # ---------------- 候选宇宙构建 ----------------

    def _get_us_universe(self):
        """美股动态搜索：Most Active + 蓝筹兜底（去掉 Trending 妖股源）。"""
        print("  [Screener] 正在探测美股活跃标的 (Most Active)...")
        active = news_spider.get_us_most_active() or []
        blue_chips = ["NVDA", "AAPL", "TSLA", "MSFT", "GOOGL", "META", "AMZN", "AMD", "NFLX", "AVGO"]
        symbols = list(dict.fromkeys(active[:settings.SCREENER_US_ACTIVE_TOP_N] + blue_chips))
        return [{"symbol": s, "market": "US"} for s in symbols if s]

    def _get_ashare_universe(self):
        """A股全市场高成交额标的：截断 Top N 并预筛市值。"""
        print("  [Screener] 正在通过 AkShare 探测 A股高成交额标的...")
        import os

        env_backup = {k: os.environ.get(k) for k in ["http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"]}
        for k in env_backup:
            os.environ[k] = ""

        fallback = ["600519", "000858", "601318", "601888", "002594", "300750",
                    "600036", "000333", "601166", "600030", "600900", "002415",
                    "000002", "600276", "601012", "000568", "600887", "601816",
                    "300059", "002304", "000001", "603259"]
        try:
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                df = df.sort_values(by="成交额", ascending=False)
                if "总市值" in df.columns:
                    df["总市值"] = pd.to_numeric(df["总市值"], errors="coerce")
                    df = df[df["总市值"] >= settings.SCREENER_MIN_MARKET_CAP_ASHARE]
                df = df.head(settings.SCREENER_ASHARE_TOP_N)
                return [{"symbol": c, "market": "A-Share"} for c in df['代码'].tolist()]
            return [{"symbol": s, "market": "A-Share"} for s in fallback]
        except Exception as e:
            print(f"  [Screener] AkShare A股探测失败: {e}")
            return [{"symbol": s, "market": "A-Share"} for s in fallback]
        finally:
            for k, v in env_backup.items():
                if v is not None:
                    os.environ[k] = v
                else:
                    if k in os.environ:
                        del os.environ[k]

    def _get_hk_universe(self):
        """港股核心资产：按成交额截断 Top N。"""
        print("  [Screener] 正在通过 AkShare 提取港股核心资产...")
        import os

        env_backup = {k: os.environ.get(k) for k in ["http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"]}
        for k in env_backup:
            os.environ[k] = ""

        fallback = ["0700.HK", "9988.HK", "3690.HK", "1211.HK", "9888.HK", "1810.HK"]
        try:
            import akshare as ak
            df = ak.stock_hk_spot_em()
            if df is not None and not df.empty:
                df = df.sort_values(by="成交额", ascending=False).head(settings.SCREENER_HK_TOP_N)
                return [{"symbol": f"{s[-4:]}.HK" if len(s) >= 4 else f"{s}.HK", "market": "HK"} for s in df['代码'].tolist()]
            return [{"symbol": s, "market": "HK"} for s in fallback]
        except Exception as e:
            print(f"  [Screener] AkShare 港股提取失败: {e}")
            return [{"symbol": s, "market": "HK"} for s in fallback]
        finally:
            for k, v in env_backup.items():
                if v is not None:
                    os.environ[k] = v
                else:
                    if k in os.environ:
                        del os.environ[k]


valuation_screener = ValuationScreenerV2_1()
