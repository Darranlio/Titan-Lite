import pandas as pd
import numpy as np
from finnhub_provider import finnhub_provider
from data_provider import data_provider
from openai import OpenAI
from config import settings

class VerificationEngine:
    """
    鉴伪引擎：多源比对 + 量价背离验证
    """
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL
        )

    def verify_news(self, symbol, news_list):
        """
        AI 交叉比对新闻真伪
        """
        if not news_list: return "无新闻可验证", 0.5
        
        from skills.engine import skill_engine
        prompt = skill_engine.render_skill("verification_fact_checker", {"symbol": symbol, "news_list": news_list[:5]})
        try:
            resp = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}]
            )
            content = resp.choices[0].message.content
            # 简单提取评分逻辑（实际生产中可用 Regex）
            score = 0.8 if "可靠" in content else 0.4
            return content, score
        except:
            return "AI 鉴伪暂时不可用", 0.5

    def check_divergence(self, symbol):
        """
        量价背离验证：Sentiment vs. Price Action
        """
        # 获取 K 线数据 (yfinance)
        real_today = pd.Timestamp.now()
        end = real_today
        start = end - pd.Timedelta(days=30)
        
        # 为了计算 OBV，我们需要 Close 和 Volume
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))
        
        if len(df) < 5: return "数据不足，无法验证背离"
        
        # 1. 计算 OBV (On-Balance Volume)
        df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
        
        # 2. 判断背离
        recent_price_trend = df['Close'].iloc[-1] > df['Close'].iloc[-5]
        recent_obv_trend = df['OBV'].iloc[-1] > df['OBV'].iloc[-5]
        
        if recent_price_trend and not recent_obv_trend:
            return "⚠️ 警告：价格上涨但 OBV 下降，存在量价背离，疑似缩量诱多。"
        elif not recent_price_trend and recent_obv_trend:
            return "ℹ️ 提示：价格下跌但 OBV 上升，主力可能在暗中吸筹。"
        
        return "✅ 价格与量能同步，暂无背离迹象。"

    def get_insider_signal(self, symbol):
        """
        内幕交易验证
        """
        transactions = finnhub_provider.get_insider_transactions(symbol)
        if not transactions: return "近期无高管交易记录"
        
        buy_count = sum(1 for t in transactions if 'Buy' in str(t.get('transactionText', '')))
        sell_count = sum(1 for t in transactions if 'Sale' in str(t.get('transactionText', '')))
        
        if sell_count > buy_count:
            return f"🚨 预警：近期高管出现 {sell_count} 次减持行为。"
        elif buy_count > 0:
            return f"💎 亮点：近期高管出现 {buy_count} 次增持，信心较强。"
        
        return "近期高管交易平稳。"

verification_engine = VerificationEngine()
