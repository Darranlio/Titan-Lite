import os
import sqlite3
import pandas as pd
from datetime import datetime
from data_provider import data_provider

class PortfolioManager:
    """
    Titan-PM V2: 基于 SQLite 的工业级基金管理系统
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
            # 1. 交易流水表
            cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                side TEXT,
                quantity INTEGER,
                price REAL,
                total REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            # 2. 持仓表
            cursor.execute('''CREATE TABLE IF NOT EXISTS positions (
                symbol TEXT PRIMARY KEY,
                quantity INTEGER,
                average_cost REAL
            )''')
            # 3. 基金元数据 (现金、份额)
            cursor.execute('''CREATE TABLE IF NOT EXISTS fund_meta (
                key TEXT PRIMARY KEY,
                value REAL
            )''')
            # 4. 净值历史
            cursor.execute('''CREATE TABLE IF NOT EXISTS nav_history (
                date TEXT PRIMARY KEY,
                nav REAL,
                total_value REAL
            )''')
            # 5. 结构化研报库
            cursor.execute('''CREATE TABLE IF NOT EXISTS research_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                date TEXT,
                rating TEXT,
                price REAL,
                upside REAL,
                pe REAL,
                fact_score REAL,
                content_md TEXT,
                raw_data_json TEXT,
                UNIQUE(symbol, date)
            )''')
            
            # 初始化本金 (100万)
            cursor.execute("INSERT OR IGNORE INTO fund_meta VALUES ('cash', 1000000.0)")
            cursor.execute("INSERT OR IGNORE INTO fund_meta VALUES ('total_units', 1000000.0)")
            conn.commit()

    def record_transaction(self, symbol, side, quantity, price):
        symbol = symbol.upper()
        total_amount = quantity * price
        
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM fund_meta WHERE key='cash'")
                current_cash = cursor.fetchone()[0]

                if side == 'BUY':
                    if current_cash < total_amount:
                        return False, "现金不足"
                    cursor.execute("UPDATE fund_meta SET value = value - ? WHERE key='cash'", (total_amount,))
                    cursor.execute("SELECT quantity, average_cost FROM positions WHERE symbol=?", (symbol,))
                    row = cursor.fetchone()
                    if row:
                        old_qty, old_cost = row
                        new_qty = old_qty + quantity
                        new_cost = (old_qty * old_cost + total_amount) / new_qty
                        cursor.execute("UPDATE positions SET quantity=?, average_cost=? WHERE symbol=?", (new_qty, new_cost, symbol))
                    else:
                        cursor.execute("INSERT INTO positions VALUES (?, ?, ?)", (symbol, quantity, price))
                elif side == 'SELL':
                    cursor.execute("SELECT quantity FROM positions WHERE symbol=?", (symbol,))
                    row = cursor.fetchone()
                    if not row or row[0] < quantity:
                        return False, "持仓不足"
                    cursor.execute("UPDATE fund_meta SET value = value + ? WHERE key='cash'", (total_amount,))
                    new_qty = row[0] - quantity
                    if new_qty == 0:
                        cursor.execute("DELETE FROM positions WHERE symbol=?", (symbol,))
                    else:
                        cursor.execute("UPDATE positions SET quantity=? WHERE symbol=?", (new_qty, symbol))
                cursor.execute("INSERT INTO transactions (symbol, side, quantity, price, total) VALUES (?,?,?,?,?)", (symbol, side, quantity, price, total_amount))
                conn.commit()
            return True, "交易记录已持久化至数据库"
        except Exception as e: return False, f"数据库错误: {e}"

    def calculate_nav(self):
        """计算最新净值"""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM fund_meta WHERE key='cash'")
                cash = cursor.fetchone()[0]
                cursor.execute("SELECT value FROM fund_meta WHERE key='total_units'")
                total_units = cursor.fetchone()[0]
                cursor.execute("SELECT symbol, quantity, average_cost FROM positions")
                positions = cursor.fetchall()
            total_market_value = cash
            pos_details = []
            for symbol, qty, cost in positions:
                price_series = data_provider.get_history_price(symbol)
                current_price = price_series.iloc[-1] if not price_series.empty else cost
                mkt_val = current_price * qty
                total_market_value += mkt_val
                pnl = (current_price - cost) / cost
                pos_details.append({"symbol": symbol, "quantity": qty, "cost": round(cost, 2), "current_price": round(current_price, 2), "mkt_value": round(mkt_val, 2), "pnl": f"{pnl:.2%}"})
            nav = total_market_value / total_units
            date_str = datetime.now().strftime("%Y-%m-%d")
            with self._get_conn() as conn:
                conn.execute("INSERT OR REPLACE INTO nav_history VALUES (?, ?, ?)", (date_str, nav, total_market_value))
            return {"nav": round(nav, 4), "total_value": round(total_market_value, 2), "cash": round(cash, 2), "positions": pos_details, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        except Exception as e: return None

    def get_nav_history(self):
        """获取净值历史数据用于画图"""
        try:
            with self._get_conn() as conn:
                df = pd.read_sql_query("SELECT date, nav FROM nav_history ORDER BY date ASC", conn)
                return df.to_dict('records')
        except: return []

    def calculate_risk_metrics(self):
        """
        计算专业风险指标：夏普比率、最大回撤
        """
        try:
            with self._get_conn() as conn:
                df = pd.read_sql_query("SELECT nav FROM nav_history ORDER BY date ASC", conn)
            
            if len(df) < 2: return {"sharpe": 0, "max_drawdown": "0.00%", "volatility": "0.00%"}
            
            # 计算日收益率
            df['returns'] = df['nav'].pct_change().fillna(0)
            
            # 1. 最大回撤
            rolling_max = df['nav'].cummax()
            drawdown = (df['nav'] - rolling_max) / rolling_max
            max_drawdown = drawdown.min()
            
            # 2. 年化波动率 (假设 252 交易日)
            vol = df['returns'].std() * (252 ** 0.5)
            
            # 3. 夏普比率 (假设无风险利率 2%)
            sharpe = (df['returns'].mean() * 252 - 0.02) / vol if vol > 0 else 0
            
            return {
                "sharpe": round(sharpe, 2),
                "max_drawdown": f"{max_drawdown:.2%}",
                "volatility": f"{vol:.2%}",
                "total_return": f"{(df['nav'].iloc[-1] - 1):.2%}"
            }
        except:
            return {"sharpe": "-", "max_drawdown": "-", "volatility": "-"}

    def save_report_to_db(self, symbol, date, item, decision, verify_data, content_md):
        """将研报数据结构化持久化"""
        import json
        try:
            with self._get_conn() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO research_reports 
                    (symbol, date, rating, price, upside, pe, fact_score, content_md, raw_data_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (symbol, date, decision.get('action'), item['current_price'], item['upside'], item.get('pe', 0), 0.5, content_md, json.dumps(decision)))
            return True
        except Exception as e:
            print(f"研报存数据库失败: {e}")
            return False

    def get_portfolio_diagnosis(self, macro_context):
        status = self.calculate_nav()
        if not status: return "数据核算异常"
        from openai import OpenAI
        from config import settings
        prompt = f"你是一位顶级基金评级专家。请对以下个人基金组合进行【资产配置诊断】。\n[持仓快照]{status}\n[市场背景]{macro_context}"
        try:
            client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
            resp = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}])
            return resp.choices[0].message.content
        except: return "诊断生成失败。"

portfolio_manager = PortfolioManager()
