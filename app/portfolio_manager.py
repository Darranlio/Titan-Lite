import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from data_provider import data_provider
from typing import Optional
from sys_logger import sys_logger
from utils import sanitize_json_data

class PortfolioManager:
    """
    Titan-PM V8.10: 工业级多币种核算引擎 (含自动迁移与详细诊断)
    """
    def __init__(self, storage_root: Optional[str] = None):
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
        if storage_root:
            self.db_dir = os.path.join(base_path, storage_root, "data", "portfolio")
        else:
            self.db_dir = os.path.join(base_path, "app", "data", "portfolio")
            
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, "vault.db")
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """初始化数据库并执行自动迁移"""
        with self._get_conn() as conn:
            # 1. 创建基础表
            conn.execute('''CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT, side TEXT, quantity REAL, price REAL, total REAL, units_issued REAL, timestamp DATETIME
            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS fund_meta (key TEXT PRIMARY KEY, value REAL)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS nav_history (date TEXT PRIMARY KEY, nav REAL, total_value_usd REAL)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS pending_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT, side TEXT, quantity REAL, price REAL, rationale TEXT, timestamp DATETIME
            )''')
            
            # 2. 自动迁移：检查缺失列
            cursor = conn.execute("PRAGMA table_info(transactions)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'units_issued' not in columns:
                sys_logger.info("Migrating database: Adding units_issued to transactions")
                conn.execute("ALTER TABLE transactions ADD COLUMN units_issued REAL DEFAULT 0")
            
            # 确保 quantity 是 REAL (虽然 SQLite 动态类型，但为了明确性)
            conn.commit()

    def record_transaction(self, symbol, side, quantity, price, date=None):
        """记录交易流水"""
        symbol = (symbol or "").strip().upper()
        if not symbol: return False, "标的代码不能为空"
        
        total = quantity * price
        ts = date if date else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if ts and '/' in ts:
            try:
                ts = datetime.strptime(ts, "%m/%d/%Y").strftime("%Y-%m-%d")
            except:
                pass
        
        try:
            status = self.calculate_nav()
            
            # 获取当前总份额
            with self._get_conn() as conn:
                row = conn.execute("SELECT SUM(units_issued) as total_units FROM transactions").fetchone()
                total_units = row['total_units'] if row and row['total_units'] else 0

            # 业务校验
            if side == 'SELL':
                all_stocks = status.get('us_equities', []) + status.get('hk_equities', []) + status.get('cn_equities', [])
                current_qty = next((s['quantity'] for s in all_stocks if s['symbol'] == symbol), 0)
                if current_qty < quantity: return False, f"持仓不足 (仅剩 {current_qty})"
                
            if side == 'BUY':
                if symbol.endswith(".HK"):
                    currency = "HKD"
                elif symbol.endswith(".SS") or symbol.endswith(".SZ") or symbol.endswith(".BJ") or (symbol.isdigit() and len(symbol) == 6):
                    currency = "CNY"
                else:
                    currency = "USD"
                cash_map = {c['symbol']: c['quantity'] for c in status.get('cash_positions', [])}
                if cash_map.get(currency, 0) < total: 
                    return False, f"{currency} 现金不足 (需 {total}, 剩余 {cash_map.get(currency, 0)})"

            if side == 'WITHDRAW':
                currency = symbol
                if currency not in ['USD', 'HKD', 'CNY']:
                    return False, f"提现币种必须为 USD, HKD 或 CNY"
                cash_map = {c['symbol']: c['quantity'] for c in status.get('cash_positions', [])}
                if cash_map.get(currency, 0) < total: 
                    return False, f"{currency} 现金不足 (需 {total}, 剩余 {cash_map.get(currency, 0)})"

            # 换算为 USD
            rates = data_provider.get_exchange_rates()
            usd_equiv = total
            if symbol == 'HKD': usd_equiv = total / rates.get('HKD', 7.8)
            elif symbol == 'CNY': usd_equiv = total / rates.get('CNY', 7.2)
            elif symbol.endswith('.HK'): usd_equiv = total / rates.get('HKD', 7.8)
            elif symbol.endswith('.SS') or symbol.endswith('.SZ') or symbol.endswith('.BJ'): usd_equiv = total / rates.get('CNY', 7.2)

            # 计算新增/扣减份额
            units_to_issue = 0
            if side in ['DEPOSIT', 'INITIAL']:
                nav = status.get('nav', 1.0)
                if nav <= 0: nav = 1.0 # 防御性逻辑
                units_to_issue = usd_equiv if total_units <= 0 else (usd_equiv / nav)
            elif side == 'WITHDRAW':
                nav = status.get('nav', 1.0)
                if nav <= 0: nav = 1.0
                units_to_issue = - (usd_equiv / nav)

            # 写入数据库
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT INTO transactions (symbol, side, quantity, price, total, units_issued, timestamp) VALUES (?,?,?,?,?,?,?)", 
                    (symbol, side, quantity, price, total, units_to_issue, ts)
                )
                conn.commit()
            
            # 如果是初始同步，尝试追溯净值历史
            if side == 'INITIAL' and symbol not in ['USD', 'HKD', 'CNY']:
                self._backfill_nav(symbol, ts[:10], quantity, price)
                
            return True, "✅ 记录成功"
        except Exception as e:
            sys_logger.error(f"Transaction record failed: {str(e)}")
            return False, f"数据库写入失败: {str(e)}"

    def calculate_nav(self):
        """全量资产核算"""
        try:
            with self._get_conn() as conn:
                df = pd.read_sql_query("SELECT * FROM transactions", conn)
                row = conn.execute("SELECT SUM(units_issued) as total_units FROM transactions").fetchone()
                total_units = row['total_units'] if row and row['total_units'] else 0

            if df.empty:
                return {"nav": 1.0, "total_value_usd": 0, "cash_positions": [{"symbol":"USD","quantity":0,"mkt_value_usd":0}], "us_equities": [], "hk_equities": []}
            
            rates = data_provider.get_exchange_rates()
            cash_ledger = {"USD": 0.0, "HKD": 0.0, "CNY": 0.0}
            stocks = {}

            for _, r in df.iterrows():
                side, sym, total, qty = r['side'], r['symbol'], r['total'], r['quantity']
                if sym in ['USD', 'HKD', 'CNY']:
                    if side in ['DEPOSIT', 'INITIAL']: cash_ledger[sym] += total
                    elif side == 'WITHDRAW': cash_ledger[sym] -= total
                    elif side == 'BUY': cash_ledger[sym] -= total # 如果用现金买股票
                    elif side == 'SELL': cash_ledger[sym] += total # 卖股票回笼现金
                else:
                    if sym not in stocks: stocks[sym] = {"qty": 0, "total_cost": 0.0}
                    currency = "HKD" if sym.endswith(".HK") else "USD"
                    if side in ['BUY', 'INITIAL']:
                        stocks[sym]['qty'] += qty
                        stocks[sym]['total_cost'] += total
                        if side == 'BUY': cash_ledger[currency] -= total
                    elif side == 'SELL':
                        if stocks[sym]['qty'] > 0:
                            avg_cost = stocks[sym]['total_cost'] / stocks[sym]['qty']
                            stocks[sym]['qty'] -= qty
                            stocks[sym]['total_cost'] -= qty * avg_cost
                        cash_ledger[currency] += total

            cash_pos = [{"symbol": k, "quantity": round(v, 2), "mkt_value_usd": round(v/rates.get(k, 1.0), 2)} for k, v in cash_ledger.items()]
            total_cash_usd = sum(p['mkt_value_usd'] for p in cash_pos)

            total_stock_usd = 0.0
            us_equities, hk_equities, cn_equities = [], [], []
            for s, d in stocks.items():
                if d['qty'] <= 0: continue
                try:
                    hist = data_provider.get_history_price(s, start_date=(datetime.now()-timedelta(days=5)).strftime("%Y-%m-%d"))
                    curr = hist.iloc[-1] if not hist.empty else (d['total_cost']/d['qty'])
                except: curr = d['total_cost']/d['qty']
                
                mkt = curr * d['qty']
                if s.endswith('.HK'):
                    mkt_usd = mkt / rates.get('HKD', 7.8)
                elif s.endswith('.SS') or s.endswith('.SZ') or s.endswith('.BJ'):
                    mkt_usd = mkt / rates.get('CNY', 7.2)
                else:
                    mkt_usd = mkt
                total_stock_usd += mkt_usd
                avg_cost = d['total_cost'] / d['qty']
                item = {
                    "symbol": s, "quantity": round(d['qty'], 4), 
                    "cost": round(avg_cost, 4), "current_price": round(curr, 4), 
                    "pnl": f"{(curr - avg_cost)/avg_cost:.2%}" if avg_cost != 0 else "0.00%", 
                    "mkt_value": round(mkt, 2), "mkt_value_usd": round(mkt_usd, 2)
                }
                if s.endswith('.HK'): hk_equities.append(item)
                elif s.endswith('.SS') or s.endswith('.SZ') or s.endswith('.BJ'): cn_equities.append(item)
                else: us_equities.append(item)

            total_val_usd = max(0, total_cash_usd + total_stock_usd)
            nav = total_val_usd / total_units if total_units > 0 else 1.0
            
            # 记录净值曲线
            if total_units > 0:
                with self._get_conn() as conn:
                    conn.execute("INSERT OR REPLACE INTO nav_history VALUES (?, ?, ?)", (datetime.now().strftime("%Y-%m-%d"), nav, total_val_usd))

            return sanitize_json_data({
                "nav": round(nav, 4), "total_value_usd": round(total_val_usd, 2),
                "total_value_hkd": round(total_val_usd * rates.get('HKD', 7.8), 2),
                "total_value_cny": round(total_val_usd * rates.get('CNY', 7.2), 2),
                "cash_positions": [c for c in cash_pos if c['quantity'] != 0 or c['symbol'] == 'USD'],
                "us_equities": us_equities, "hk_equities": hk_equities, "cn_equities": cn_equities
            })
        except Exception as e:
            sys_logger.error(f"NAV calculation failed: {str(e)}")
            return {"nav": 1.0, "total_value_usd": 0, "cash_positions": [{"symbol":"USD","quantity":0,"mkt_value_usd":0}], "us_equities": [], "hk_equities": [], "cn_equities": []}

    def delete_transaction(self, tx_id):
        try:
            with self._get_conn() as conn: conn.execute("DELETE FROM transactions WHERE id=?", (tx_id,)); conn.commit()
            return True, "记录已撤销"
        except Exception as e: return False, str(e)

    def get_transaction_history(self):
        try:
            with self._get_conn() as conn:
                df = pd.read_sql_query("SELECT * FROM transactions ORDER BY timestamp DESC", conn)
                return df.where(pd.notnull(df), None).to_dict('records')
        except: 
            return []

    def get_nav_history(self):
        try:
            with self._get_conn() as conn:
                df = pd.read_sql_query("SELECT date, nav FROM nav_history ORDER BY date ASC", conn)
                if df.empty: return {"user": [], "benchmark": []}
                spy = data_provider.get_history_price("SPY", start_date=df['date'].iloc[0])
                
                # Sanitize SPY data
                spy_nav = []
                if not spy.empty:
                    base_spy = spy.iloc[0]
                    spy_nav = (spy / base_spy).fillna(1.0).tolist() # Use 1.0 as fallback for NaN in benchmark
                else:
                    spy_nav = [1.0] * len(df)
                    
                return {"user": df.to_dict('records'), "benchmark": spy_nav}
        except: return {"user": [], "benchmark": []}

    def calculate_risk_metrics(self):
        status = self.calculate_nav()
        t_ret = f"{(status['nav'] - 1):.2%}" if status['nav'] > 0 else "0.00%"
        try:
            with self._get_conn() as conn:
                df = pd.read_sql_query("SELECT nav FROM nav_history ORDER BY date ASC", conn)
            if len(df) < 2: return {"sharpe": "-", "max_drawdown": "-", "volatility": "-", "total_return": t_ret}
            df['returns'] = df['nav'].pct_change().fillna(0)
            mdd = ((df['nav'] - df['nav'].cummax()) / df['nav'].cummax()).min()
            vol = df['returns'].std() * (252 ** 0.5) if len(df) > 2 else 0
            sharpe = (df['returns'].mean() * 252 - 0.02) / vol if vol > 0 else 0
            return {"sharpe": round(sharpe, 2) if vol > 0 else "-", "max_drawdown": f"{mdd:.2%}", "volatility": f"{vol:.2%}", "total_return": t_ret}
        except: return {"sharpe": "-", "max_drawdown": "-", "volatility": "-", "total_return": t_ret}

    def _backfill_nav(self, symbol, start_date, quantity, cost):
        try:
            history = data_provider.get_history_price(symbol, start_date=start_date)
            if history.empty: return
            with self._get_conn() as conn:
                for date, price in history.items():
                    conn.execute("INSERT OR IGNORE INTO nav_history VALUES (?, ?, ?)", (date.strftime("%Y-%m-%d"), 1.0 * (price / history.iloc[0]), price * quantity))
                conn.commit()
        except: pass

    def get_portfolio_diagnosis(self, macro_context):
        status = self.calculate_nav()
        from openai import OpenAI
        from config import settings
        prompt = f"分析组合资产现状：{status}。宏观：{macro_context}。给出调仓建议。"
        try:
            client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
            resp = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}])
            return resp.choices[0].message.content
        except: return "诊断暂不可用。"

    def get_pending_orders(self):
        """获取所有待处理建议"""
        try:
            with self._get_conn() as conn:
                df = pd.read_sql_query("SELECT * FROM pending_orders ORDER BY timestamp DESC", conn)
                return sanitize_json_data(df.where(pd.notnull(df), None).to_dict('records'))
        except: return []

    def add_pending_order(self, symbol, side, price, quantity=0, rationale=""):
        """添加待处理的交易建议 (来自智能体研判)"""
        now = datetime.now()
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT INTO pending_orders (symbol, side, quantity, price, rationale, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                    (symbol, side, quantity, price, rationale, now)
                )
        except Exception as e:
            sys_logger.info(f"Failed to add pending order: {str(e)}")

    def clear_pending_order(self, order_id):
        """清除或执行后删除建议"""
        try:
            with self._get_conn() as conn:
                conn.execute("DELETE FROM pending_orders WHERE id=?", (order_id,))
                conn.commit()
            return True, "建议已清除"
        except Exception as e: return False, str(e)

# 默认导出单例
portfolio_manager = PortfolioManager()
