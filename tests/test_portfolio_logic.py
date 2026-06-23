import pytest
import os
import sqlite3
import pandas as pd
from unittest.mock import MagicMock, patch
from app.portfolio_manager import PortfolioManager

@pytest.fixture
def mock_db(tmp_path):
    """创建一个临时的内存数据库用于测试"""
    db_path = tmp_path / "test_vault.db"
    with patch("app.portfolio_manager.os.makedirs"):
        pm = PortfolioManager()
        pm.db_path = str(db_path)
        pm._init_db()
        return pm

@pytest.fixture
def mock_data_provider():
    """Mock 数据提供者"""
    with patch("app.portfolio_manager.data_provider") as mock:
        # 默认汇率：HKD=7.8, CNY=7.2
        mock.get_exchange_rates.return_value = {"USD": 1.0, "HKD": 7.8, "CNY": 7.2}

        # 默认股价：AAPL=$150
        def side_effect_price(symbol, **kwargs):
            return pd.Series([150.0], index=[pd.Timestamp.now()])

        mock.get_history_price.side_effect = side_effect_price
        yield mock

def test_zero_base_initialization(mock_db, mock_data_provider):
    """
    测试：冷启动入金。
    逻辑：1.0 净值起步，份额发行。
    """
    mock_db.record_transaction("USD", "DEPOSIT", 20000, 1.0)
    status = mock_db.calculate_nav()

    assert status['nav'] == 1.0
    assert status['total_value_usd'] == 20000.0
    # 验证多币种现金明细
    usd_cash = next(c for c in status['cash_positions'] if c['symbol'] == 'USD')
    assert usd_cash['quantity'] == 20000.0

def test_deposit_form_values_update_cash_and_normalize_date(mock_db, mock_data_provider):
    """
    测试：基金页入金表单的 1 x 10000 USD 能正确入账。
    """
    success, msg = mock_db.record_transaction("USD", "DEPOSIT", 1, 10000, "06/04/2026")
    assert success, msg

    status = mock_db.calculate_nav()
    usd_cash = next(c for c in status['cash_positions'] if c['symbol'] == 'USD')
    assert status['nav'] == 1.0
    assert status['total_value_usd'] == 10000.0
    assert usd_cash['quantity'] == 10000.0

    history = mock_db.get_transaction_history()
    assert history[0]['timestamp'] == "2026-06-04"

def test_initial_cash_sync_counts_as_cash_position(mock_db, mock_data_provider):
    """
    测试：初始现金同步应进入现金余额，但不改变 1.0 起始净值。
    """
    success, msg = mock_db.record_transaction("USD", "INITIAL", 5000, 1.0)
    assert success, msg

    status = mock_db.calculate_nav()
    usd_cash = next(c for c in status['cash_positions'] if c['symbol'] == 'USD')
    assert status['nav'] == 1.0
    assert status['total_value_usd'] == 5000.0
    assert usd_cash['quantity'] == 5000.0

def test_initial_stock_pnl(mock_db, mock_data_provider):
    """
    测试：录入带历史收益的初始持仓。
    逻辑：100买的现价150，净值应为1.5。
    """
    # 录入 100 股 AAPL，成本 $100 (现价由 mock 提供为 $150)
    mock_db.record_transaction("AAPL", "INITIAL", 100, 100.0)
    status = mock_db.calculate_nav()

    # 初始份额 = 100 * 100 = 10000 份 (以成本入账发行)
    # 当前市值 = 100 * 150 = 15000 USD
    # NAV = 15000 / 10000 = 1.5
    assert status['nav'] == 1.5
    assert status['us_equities'][0]['pnl'] == "50.00%"

def test_capital_inflow_non_dilutive(mock_db, mock_data_provider):
    """
    测试：在中途追加本金，不应改变当前净值。
    """
    # 1. 初始入金 10000，NAV=1.0
    mock_db.record_transaction("USD", "DEPOSIT", 10000, 1.0)

    # 2. 模拟资产上涨，假设净值变为 1.2
    with patch("app.portfolio_manager.data_provider.get_history_price") as mock_price:
        # 强制将市价设为 120 (成本 100)
        mock_price.return_value = pd.Series([120.0])
        mock_db.record_transaction("AAPL", "INITIAL", 100, 100.0)

        # 此时总值 = 10000 (现金) + 12000 (股票) = 22000
        # 总份额 = 10000 (入金) + 10000 (初始持仓) = 20000
        # NAV = 22000 / 20000 = 1.1
        status = mock_db.calculate_nav()
        current_nav = status['nav']
        assert current_nav == 1.1

        # 3. 追加入金 11000 USD
        # 系统应按 1.1 净值折算份额：11000 / 1.1 = 10000 份
        mock_db.record_transaction("USD", "DEPOSIT", 11000, 1.0)

        new_status = mock_db.calculate_nav()
        # 净值必须保持 1.1
        assert new_status['nav'] == 1.1
        # 总市值 = 22000 + 11000 = 33000
        assert new_status['total_value_usd'] == 33000.0

def test_ledger_integrity_after_undo(mock_db, mock_data_provider):
    """
    测试：撤销买入流水后，资产状态完全恢复到买入前。
    """
    # 1. 存入 10000
    mock_db.record_transaction("USD", "DEPOSIT", 10000, 1.0)

    # 2. 买入 10 股 (成本 100, 总价 1000)
    mock_db.record_transaction("AAPL", "BUY", 10, 100.0)

    # 3. 获取 ID 并删除该笔买入
    with mock_db._get_conn() as conn:
        tx_id = conn.execute("SELECT id FROM transactions WHERE symbol='AAPL'").fetchone()[0]

    mock_db.delete_transaction(tx_id)

    # 4. 重算后应回到 10000 现金，0 持仓
    status = mock_db.calculate_nav()
    assert status['total_value_usd'] == 10000.0
    usd_cash = next(c for c in status['cash_positions'] if c['symbol'] == 'USD')
    assert usd_cash['quantity'] == 10000.0
    assert len(status['us_equities']) == 0

def test_sell_logic_realized_cash(mock_db, mock_data_provider):
    """
    测试：卖出股票后，市值正确转化为现金。
    """
    # 1. 初始持仓 1000 股，成本 100 (总值 10w)
    mock_db.record_transaction("NVDA", "INITIAL", 1000, 100.0)

    # 2. 卖出 1000 股，单价 1.0 (割肉卖出，回笼 1000)
    mock_db.record_transaction("NVDA", "SELL", 1000, 1.0)

    status = mock_db.calculate_nav()
    # 现金应增加 1000
    usd_cash = next(c for c in status['cash_positions'] if c['symbol'] == 'USD')
    assert usd_cash['quantity'] == 1000.0
    # 持仓应清空
    assert len(status['us_equities']) == 0
    # 总市值应等于现金 = 1000
    assert status['total_value_usd'] == 1000.0
