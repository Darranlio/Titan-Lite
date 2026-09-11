import asyncio
import pytest

import app.valuation_screener as vs_mod
from app.valuation_screener import (
    ValuationScreenerV2_1,
    _ashare_upside,
    _compute_quality_score,
    _passes_quality_gates,
)


# ------------------------------------------------------------
# 纯函数单测（无网络）
# ------------------------------------------------------------

@pytest.mark.parametrize("peg,max_upside,expected", [
    (0.5, None, 0.8),        # 1/0.5 - 1 = 1.0 -> clamp 0.8
    (0.4, None, 0.8),        # 1.5 -> clamp 0.8
    (0.8, None, 0.25),       # 0.25
    (1.0, None, 0.0),        # 平价，无空间
    (2.0, None, 0.0),        # 高估，无空间
    (None, None, 0.0),       # 无 PEG
    (0.0, None, 0.0),        # 非法 PEG
    (0.6, 0.5, 0.5),         # 自定义上限
])
def test_ashare_upside(peg, max_upside, expected):
    assert abs(_ashare_upside(peg, max_upside) - expected) < 1e-9


def test_compute_quality_score_ranks_good_above_bad():
    good = {'upside': 0.4, 'analyst_count': 20, 'roe': 0.25, 'market_cap': 1e11}
    bad = {'upside': 0.0, 'analyst_count': 0, 'roe': 0.0, 'market_cap': 1e8}
    assert _compute_quality_score(good) > _compute_quality_score(bad)
    assert 0 <= _compute_quality_score(good) <= 100


@pytest.mark.parametrize("candidate,market,expected", [
    # 通过
    ({'upside': 0.15, 'market_cap': 5e9, 'current_price': 50.0, 'analyst_count': 5, 'roe': 0.12}, 'US', True),
    ({'upside': 0.30, 'market_cap': 150e8, 'current_price': 20.0, 'analyst_count': 4, 'roe': 0.10}, 'A-Share', True),
    ({'upside': 0.12, 'market_cap': 120e8, 'current_price': 30.0, 'analyst_count': 3, 'roe': 0.08}, 'HK', True),
    # 股价过低 (US 仙股)
    ({'upside': 0.15, 'market_cap': 5e9, 'current_price': 2.0, 'analyst_count': 5, 'roe': 0.12}, 'US', False),
    # 市值不达标 (US)
    ({'upside': 0.15, 'market_cap': 1e8, 'current_price': 50.0, 'analyst_count': 5, 'roe': 0.12}, 'US', False),
    # 市值不达标 (A股)
    ({'upside': 0.30, 'market_cap': 50e8, 'current_price': 20.0, 'analyst_count': 4, 'roe': 0.10}, 'A-Share', False),
    # 涨幅超上限 (脏数据)
    ({'upside': 1.5, 'market_cap': 5e9, 'current_price': 50.0, 'analyst_count': 5, 'roe': 0.12}, 'US', False),
    # 涨幅低于下限
    ({'upside': 0.02, 'market_cap': 5e9, 'current_price': 50.0, 'analyst_count': 5, 'roe': 0.12}, 'US', False),
    # 分析师覆盖不足
    ({'upside': 0.15, 'market_cap': 5e9, 'current_price': 50.0, 'analyst_count': 1, 'roe': 0.12}, 'US', False),
    # ROE 不足
    ({'upside': 0.15, 'market_cap': 5e9, 'current_price': 50.0, 'analyst_count': 5, 'roe': 0.01}, 'US', False),
])
def test_passes_quality_gates(candidate, market, expected):
    assert _passes_quality_gates(candidate, market) is expected


# ------------------------------------------------------------
# run() 集成测试：mock 数据源，走完整 审计 → 闸门 → 评分 流程
# ------------------------------------------------------------

def test_run_us_filters_and_scores(monkeypatch):
    vs = ValuationScreenerV2_1()

    # 固定候选宇宙，避免真实爬虫
    monkeypatch.setattr(vs, '_get_us_universe', lambda: [{"symbol": "AAPL", "market": "US"}])
    monkeypatch.setattr(vs, '_get_ashare_universe', lambda: [])
    monkeypatch.setattr(vs, '_get_hk_universe', lambda: [])

    # mock 数据源
    monkeypatch.setattr(vs_mod.fmp_provider, 'get_price_target',
                        lambda symbol: {"targetConsensus": 150.0})
    monkeypatch.setattr(vs_mod.fmp_provider, 'get_key_metrics',
                        lambda symbol: {"returnOnEquityTTM": 0.15, "marketCap": 3e12})
    monkeypatch.setattr(vs_mod.data_provider, 'get_analyst_info',
                        lambda symbol: {"currentPrice": 100.0, "marketCap": 3e12,
                                        "sector": "Technology", "industry": "Consumer Electronics",
                                        "peRatioTTM": 20.0, "roeTTM": 0.15, "numberOfAnalystOpinions": 20})

    results = asyncio.run(vs.run(market='US'))

    assert len(results) == 1
    r = results[0]
    assert r['symbol'] == "AAPL"
    assert r['current_price'] == 100.0
    assert r['target_price'] == 150.0
    assert abs(r['upside'] - 0.5) < 1e-9
    assert r['pe'] == 20.0
    assert r['roe'] == 0.15
    assert r['analyst_count'] == 20
    assert r['rating'] == "FMP 目标价共识"
    assert 'quality_score' in r


def test_run_excludes_garbage(monkeypatch):
    vs = ValuationScreenerV2_1()

    monkeypatch.setattr(vs, '_get_us_universe', lambda: [{"symbol": "SURG", "market": "US"}])
    monkeypatch.setattr(vs, '_get_ashare_universe', lambda: [])
    monkeypatch.setattr(vs, '_get_hk_universe', lambda: [])

    # 妖股：目标价暴涨 17 倍 -> upside 远高于上限，应被质量闸门剔除
    # （其余指标故意给正常值，确保唯一不通过的闸门是涨幅上限）
    monkeypatch.setattr(vs_mod.fmp_provider, 'get_price_target',
                        lambda symbol: {"targetConsensus": 1800.0})
    monkeypatch.setattr(vs_mod.fmp_provider, 'get_key_metrics',
                        lambda symbol: {"returnOnEquityTTM": 0.15, "marketCap": 1e10})
    monkeypatch.setattr(vs_mod.data_provider, 'get_analyst_info',
                        lambda symbol: {"currentPrice": 100.0, "marketCap": 1e10,
                                        "peRatioTTM": 20.0, "roeTTM": 0.15, "numberOfAnalystOpinions": 10})

    results = asyncio.run(vs.run(market='US'))
    assert results == []


def test_run_dedups_by_symbol(monkeypatch):
    vs = ValuationScreenerV2_1()

    # 同一 symbol 出现在两个市场宇宙，应只审计一次
    monkeypatch.setattr(vs, '_get_us_universe', lambda: [{"symbol": "AAPL", "market": "US"}])
    monkeypatch.setattr(vs, '_get_ashare_universe', lambda: [{"symbol": "AAPL", "market": "A-Share"}])
    monkeypatch.setattr(vs, '_get_hk_universe', lambda: [])

    calls = []
    def fake_audit(item):
        calls.append(item)
        return None
    monkeypatch.setattr(vs, '_audit', fake_audit)
    monkeypatch.setattr(vs_mod.sys_logger, 'info', lambda *a, **k: None)

    asyncio.run(vs.run(market='Global'))
    assert len(calls) == 1
