import pandas as pd
from datetime import datetime, timedelta

# 引入所有模块
from config import settings
from data_provider import data_provider
from wecom import WeComBot
from macro_risk import MacroRisk
from news_analyzer import NewsAnalyzer
from chart_painter import ChartPainter
from content_manager import ContentManager
from screener import run_screener
from pair_miner import PairMiner
from ltcm_math import run_kalman

class TitanStrategy:
    def __init__(self):
        self.bot = WeComBot()
        self.risk = MacroRisk()
        self.news = NewsAnalyzer()
        self.painter = ChartPainter()
        self.content = ContentManager()

    def execute(self):
        print(">>> Titan-Lite v3.2 启动...")

        # 1. 宏观风控
        is_safe, risk_msg = self.risk.check()
        if not is_safe:
            self.bot.send_markdown(f"# ⛔ 系统熔断\n{risk_msg}", mode="private")
            return

        # 2. 漏斗 & 挖掘
        candidates = run_screener()
        if not candidates: return
        pairs = PairMiner(candidates).mine()
        if not pairs: return

        # 3. 策略循环
        start = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        end = datetime.now().strftime("%Y%m%d")

        for pair in pairs:
            try:
                # 调用适配器获取数据
                s1 = data_provider.get_history_price(pair['A'], start, end)
                s2 = data_provider.get_history_price(pair['B'], start, end)
                
                df = pd.concat([s1, s2], axis=1).dropna()
                df.columns = ['A', 'B']
                if len(df) < 100: continue

                # 数学计算
                beta, alpha = run_kalman(df['B'], df['A'])
                spread = df['A'] - (beta * df['B'] + alpha)
                z_score = (spread - spread.rolling(30).mean()) / spread.rolling(30).std()
                curr_z = z_score.iloc[-1]

                # 信号触发 (使用配置阈值)
                if abs(curr_z) > settings.TRADE_Z_THRESHOLD:
                    pair_name = f"{pair['A_name']} vs {pair['B_name']}"
                    action = "卖A买B" if curr_z > 0 else "买A卖B"
                    
                    # 舆情 & 绘图 & 文案
                    news_fact = self.news.analyze(pair_name, pair['A'], pair['B'])
                    img_priv = self.painter.draw(pair_name, df, z_score, "private")
                    img_pub = self.painter.draw(pair_name, df, z_score, "public")
                    
                    mid_priv = self.bot.upload_image(img_priv)
                    mid_pub = self.bot.upload_image(img_pub)
                    
                    txt_priv = self.content.private_report(pair_name, curr_z, action, news_fact)
                    txt_pub = self.content.public_article(pair_name, curr_z, news_fact)
                    
                    # 推送
                    self.bot.send_markdown(txt_priv, "private")
                    self.bot.send_image(mid_priv, "private")
                    
                    self.bot.send_markdown(txt_pub, "public")
                    self.bot.send_image(mid_pub, "public")
                    
                    print(f"推送完成: {pair_name}")

            except Exception as e:
                print(f"处理失败: {e}")

def run_job():
    TitanStrategy().execute()