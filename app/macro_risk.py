import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_provider import data_provider
from config import settings

class MacroRisk:
    def check(self):
        try:
            # 调用适配器
            df = data_provider.get_index_daily("sh000300")
            
            # 取最近半年
            start_dt = datetime.now() - timedelta(days=180)
            df = df[df['date'] >= start_dt].sort_values('date')
            
            # 计算指标
            df['pct'] = df['close'].pct_change()
            vol = df['pct'].tail(20).std() * np.sqrt(252)
            recent_high = df['close'].tail(10).max()
            drawdown = (df['close'].iloc[-1] - recent_high) / recent_high
            
            msg = f"波动率:{vol:.1%}, 回撤:{drawdown:.1%}"
            
            # 使用配置阈值
            if vol > settings.MACRO_VOL_THRESHOLD: 
                return False, f"⛔ 恐慌熔断 ({msg})"
            if drawdown < -0.10: 
                return False, f"⛔ 崩盘熔断 ({msg})"
                
            return True, f"✅ 市场平稳 ({msg})"
        except:
            return True, "⚠️ 风控数据缺失"