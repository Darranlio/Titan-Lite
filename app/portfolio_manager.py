import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from data_provider import data_provider

class PortfolioManager:
    """
    Titan-PM V8.9: 工业级多币种核算引擎 (含完整状态回滚)
    """
    def __init__(self):
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.db_dir = os.path.join(base_path, "app", "data", "portfolio")
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, "vault.db")
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT, side TEXT, quantity INTEGER, price REAL, total REAL, units_issued REAL, timestamp DATETIME
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS fund_meta (key TEXT PRIMARY KEY, value REAL)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS nav_history (date TEXT PRIMARY KEY, nav REAL, total_value_usd REAL)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS pending_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT, side TEXT, quantity INTEGER, price REAL, rationale TEXT, timestamp DATETIME
            )''')
            conn.commit()

    def add_pending_order(self, symbol, side, price, rationale=""):
        """添加待处理订单 (由 Agent 建议)"""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 默认建议买入 100 股或根据组合价值计算 (此处简化为 10 股作为占位)
        quantity = 10 
        try:
            with self._get_conn() as conn:
                conn.execute("INSERT INTO pending_orders (symbol, side, quantity, price, rationale, timestamp) VALUES (?,?,?,?,?,?)",
                             (symbol.upper(), side.upper(), quantity, price, rationale, ts))
                conn.commit()
            return True, "✅ 建议已加入预挂单队列"
        except Exception as e: return False, str(e)

    def get_pending_orders(self):
        """获取所有待处理建议"""
        try:
            with self._get_conn() as conn:
                return pd.read_sql_query("SELECT * FROM pending_orders ORDER BY timestamp DESC", conn).to_dict('records')
        except: return []

    def clear_pending_order(self, order_id):
        """清除或执行后删除建议"""
        try:
            with self._get_conn() as conn:
                conn.execute("DELETE FROM pending_orders WHERE id=?", (order_id,))
                conn.commit()
            return True, "建议已清除"
        except Exception as e: return False, str(e)

    def record_transaction(self, symbol, side, quantity, price, date=None):
        symbol = symbol.upper()
        total = quantity * price
        ts = date if date else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            status = self.calculate_nav()
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT SUM(units_issued) FROM transactions")
                total_units = cursor.fetchone()[0] or 0

            if side == 'SELL':
                all_stocks = status['us_equities'] + status['hk_equities']
                current_qty = next((s['quantity'] for s in all_stocks if s['symbol'] == symbol), 0)
                if current_qty < quantity: return False, f"持仓不足 (仅剩 {current_qty})"
            if side == 'BUY':
                currency = "HKD" if symbol.endswith(".HK") else "USD"
                cash_map = {c['symbol']: c['quantity'] for c in status['cash_positions']}
                if cash_map.get(currency, 0) < total: return False, f"{currency} 现金不足"

            rates = data_provider.get_exchange_rates()
            usd_equiv = total
            if symbol == 'HKD': usd_equiv = total / rates['HKD']
            elif symbol == 'CNY': usd_equiv = total / rates['CNY']
            elif symbol.endswith('.HK'): usd_equiv = total / rates['HKD']

            units_to_issue = 0
            if side in ['DEPOSIT', 'INITIAL']:
                units_to_issue = usd_equiv if total_units <= 0 else (usd_equiv / status['nav'])

            with self._get_conn() as conn:
                conn.execute("INSERT INTO transactions (symbol, side, quantity, price, total, units_issued, timestamp) VALUES (?,?,?,?,?,?,?)", 
                             (symbol, side, quantity, price, total, units_to_issue, ts))
                conn.commit()
            
            if side == 'INITIAL' and symbol not in ['USD', 'HKD', 'CNY']:
                self._backfill_nav(symbol, ts[:10], quantity, price)
            return True, "✅ 记录成功"
        except Exception as e: return False, str(e)

    def calculate_nav(self):
        """核心聚合逻辑 (含彻底回滚策略)"""
        try:
            with self._get_conn() as conn:
                df = pd.read_sql_query("SELECT * FROM transactions", conn)
                cursor = conn.cursor()
                cursor.execute("SELECT SUM(units_issued) FROM transactions")
                total_units = cursor.fetchone()[0] or 0

            # --- 彻底回滚：如果账本为空，清空历史数据，防止指标残留 ---
            if df.empty:
                with self._get_conn() as conn:
                    conn.execute("DELETE FROM nav_history")
                    conn.commit()
                return {"nav": 1.0, "total_value_usd": 0, "cash_positions": [{"symbol":"USD","quantity":0,"mkt_value_usd":0}], "us_equities": [], "hk_equities": []}
            
            rates = data_provider.get_exchange_rates()
            cash_ledger = {"USD": 0.0, "HKD": 0.0, "CNY": 0.0}
            stocks = {}

            for _, r in df.iterrows():
                side, sym, total, qty = r['side'], r['symbol'], r['total'], r['quantity']
                if sym in ['USD', 'HKD', 'CNY']:
                    if side == 'DEPOSIT': cash_ledger[sym] += total
                    elif side == 'WITHDRAW': cash_ledger[sym] -= total
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

            cash_pos = [{"symbol": k, "quantity": round(v, 2), "mkt_value_usd": round(v/rates[k], 2)} for k, v in cash_ledger.items()]
            total_cash_usd = sum(p['mkt_value_usd'] for p in cash_pos)

            total_stock_usd = 0.0
            us_equities, hk_equities = [], []
            for s, d in stocks.items():
                if d['qty'] <= 0: continue
                try:
                    hist = data_provider.get_history_price(s, start_date=(datetime.now()-timedelta(days=5)).strftime("%Y-%m-%d"))
                    curr = hist.iloc[-1] if not hist.empty else (d['total_cost']/d['qty'])
                except: curr = d['total_cost']/d['qty']
                
                mkt = curr * d['qty']
                mkt_usd = mkt / (rates['HKD'] if s.endswith('.HK') else 1.0)
                total_stock_usd += mkt_usd
                avg_cost = d['total_cost'] / d['qty']
                item = {"symbol": s, "quantity": d['qty'], "cost": round(avg_cost, 2), "current_price": round(curr, 2), "pnl": f"{(curr - avg_cost)/avg_cost:.2%}", "mkt_value": round(mkt, 2), "mkt_value_usd": round(mkt_usd, 2)}
                if s.endswith('.HK'): hk_equities.append(item)
                else: us_equities.append(item)

            total_val_usd = max(0, total_cash_usd + total_stock_usd)
            nav = total_val_usd / total_units if total_units > 0 else 1.0
            
            if total_units > 0:
                with self._get_conn() as conn:
                    conn.execute("INSERT OR REPLACE INTO nav_history VALUES (?, ?, ?)", (datetime.now().strftime("%Y-%m-%d"), nav, total_val_usd))

            return {
                "nav": round(nav, 4), "total_value_usd": round(total_val_usd, 2),
                "total_value_hkd": round(total_val_usd * rates['HKD'], 2),
                "total_value_cny": round(total_val_usd * rates['CNY'], 2),
                "cash_positions": [c for c in cash_pos if c['quantity'] != 0 or c['symbol'] == 'USD'],
                "us_equities": us_equities, "hk_equities": hk_equities
            }
        except Exception as e:
            return {"nav": 1.0, "total_value_usd": 0, "cash_positions": [{"symbol":"USD","quantity":0,"mkt_value_usd":0}], "us_equities": [], "hk_equities": []}

    def delete_transaction(self, tx_id):
        try:
            with self._get_conn() as conn: conn.execute("DELETE FROM transactions WHERE id=?", (tx_id,)); conn.commit()
            return True, "记录已撤销"
        except Exception as e: return False, str(e)

    def get_transaction_history(self):
        try:
            with self._get_conn() as conn: return pd.read_sql_query("SELECT * FROM transactions ORDER BY timestamp DESC", conn).to_dict('records')
        except: return []

    def get_nav_history(self):
        try:
            with self._get_conn() as conn:
                df = pd.read_sql_query("SELECT date, nav FROM nav_history ORDER BY date ASC", conn)
                if df.empty: return {"user": [], "benchmark": []}
                spy = data_provider.get_history_price("SPY", start_date=df['date'].iloc[0])
                spy_nav = (spy / spy.iloc[0]).tolist() if not spy.empty else [1.0]*len(df)
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

portfolio_manager = PortfolioManager()
