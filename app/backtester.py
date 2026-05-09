import pandas as pd
import numpy as np
from data_provider import data_provider
from datetime import datetime, timedelta

class Backtester:
    """
    轻量级回测引擎
    """
    def __init__(self, initial_capital=100000):
        self.capital = initial_capital
        self.holdings = {}

    def run_simple_backtest(self, symbol, days=252):
        """
        对单个标的进行简单的买入持有回测
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        series = data_provider.get_history_price(symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        if series.empty: return None
        
        df = pd.DataFrame(series)
        df.columns = ['Close']
        df['Returns'] = df['Close'].pct_change()
        df['Cumulative_Returns'] = (1 + df['Returns']).cumprod()
        
        total_return = df['Cumulative_Returns'].iloc[-1] - 1
        sharpe = (df['Returns'].mean() / df['Returns'].std()) * np.sqrt(252) if df['Returns'].std() != 0 else 0
        
        return {
            'symbol': symbol,
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': (df['Cumulative_Returns'] / df['Cumulative_Returns'].cummax() - 1).min()
        }

    def forecast_price(self, symbol, horizon=30):
        """
        简易预测功能 (基于移动平均与趋势)
        """
        series = data_provider.get_history_price(symbol)
        if len(series) < 60: return "数据不足"
        
        # 简单线性外推或移动平均
        ma20 = series.rolling(20).mean().iloc[-1]
        ma60 = series.rolling(60).mean().iloc[-1]
        
        trend = "看涨" if ma20 > ma60 else "看跌"
        target_est = series.iloc[-1] * (1 + (ma20/ma60 - 1))
        
        return {
            'symbol': symbol,
            'current': series.iloc[-1],
            'trend': trend,
            'forecast_target': target_est,
            'horizon_days': horizon
        }

backtester = Backtester()
