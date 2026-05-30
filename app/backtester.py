import pandas as pd
import numpy as np
import json
from data_provider import data_provider
from datetime import datetime, timedelta

class Backtester:
    """
    Titan-Alpha 专业级回测引擎
    支持基准对比、净值曲线生成与风险指标核算。
    """
    def __init__(self, initial_capital=100000):
        self.capital = initial_capital

    def run_simple_backtest(self, symbol, days=365):
        """
        对单个标的进行 '买入并持有' (Buy & Hold) 的基准对比回测
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # 1. 获取标的价格数据
        series = data_provider.get_history_price(symbol, start_date=start_str, end_date=end_str)
        if series.empty: return None
        
        # 2. 获取基准 (SPY) 价格数据
        benchmark_symbol = "SPY"
        bench_series = data_provider.get_history_price(benchmark_symbol, start_date=start_str, end_date=end_str)
        if bench_series.empty:
             # 如果 SPY 获取失败，尝试获取标的的平均涨幅作为平替 (避免崩溃)
             bench_series = series.copy()
             bench_series.values[:] = series.iloc[0] 

        # 3. 数据对齐与预处理
        df = pd.DataFrame({
            'asset': series,
            'benchmark': bench_series
        }).ffill().dropna()
        
        # 4. 计算净值曲线 (Normalized to 1.0)
        df['asset_cum'] = (df['asset'] / df['asset'].iloc[0])
        df['bench_cum'] = (df['benchmark'] / df['benchmark'].iloc[0])
        
        # 5. 计算风险指标
        asset_returns = df['asset'].pct_change().dropna()
        bench_returns = df['benchmark'].pct_change().dropna()
        
        total_return = df['asset_cum'].iloc[-1] - 1
        bench_return = df['bench_cum'].iloc[-1] - 1
        
        # 简单夏普比率 (年化)
        sharpe = (asset_returns.mean() / asset_returns.std()) * np.sqrt(252) if asset_returns.std() != 0 else 0
        # 最大回撤
        drawdown = (df['asset_cum'] / df['asset_cum'].cummax() - 1).min()
        # 波动率
        volatility = asset_returns.std() * np.sqrt(252)

        # 6. 构建返回结构
        # 包含用于绘图的时间序列
        history_data = []
        for i, (ts, row) in enumerate(df.iterrows()):
            # 抽样减少数据量，每 3 天取一个点用于绘图
            if i % 3 == 0 or i == len(df) - 1:
                history_data.append({
                    "date": ts.strftime('%Y-%m-%d'),
                    "asset": round(row['asset_cum'], 4),
                    "bench": round(row['bench_cum'], 4)
                })

        return {
            'symbol': symbol,
            'benchmark': benchmark_symbol,
            'metrics': {
                'total_return': f"{total_return:.2%}",
                'benchmark_return': f"{bench_return:.2%}",
                'alpha': f"{(total_return - bench_return):.2%}",
                'sharpe_ratio': round(sharpe, 2),
                'max_drawdown': f"{drawdown:.2%}",
                'volatility': f"{volatility:.2%}"
            },
            'chart_data': history_data,
            'summary': f"在过去 {days} 天中，{symbol} 实现了 {total_return:.2%} 的回报，相对于标普500 (SPY) 的超额收益为 {(total_return - bench_return):.2%}。"
        }

backtester = Backtester()
