import pandas as pd
from statsmodels.tsa.stattools import coint
from datetime import datetime, timedelta
import concurrent.futures
from data_provider import data_provider
from config import settings

class PairMiner:
    def __init__(self, stock_list):
        self.stock_list = stock_list
        self.max_pairs = 15

    def get_history(self, stock):
        """下载数据 (通过适配器)"""
        symbol = stock['symbol']
        start = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        end = datetime.now().strftime("%Y%m%d")
        # 直接调用适配器
        return data_provider.get_history_price(symbol, start, end)

    def mine(self):
        print(f">>> [2/5] 开始同行业CP挖掘...")
        
        # 1. 并发下载
        all_series = []
        meta_map = {s['symbol']: s for s in self.stock_list}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = executor.map(self.get_history, self.stock_list)
            for res in results:
                if res is not None and len(res) > 200:
                    all_series.append(res)
        
        if not all_series: return []
        price_df = pd.concat(all_series, axis=1).dropna()
        cols = price_df.columns
        valid_pairs = []

        # 2. 挖掘计算
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                code_a, code_b = cols[i], cols[j]
                
                # --- 核心：不同行业跳过 ---
                if meta_map[code_a]['sector'] != meta_map[code_b]['sector']: continue
                
                s1, s2 = price_df[code_a], price_df[code_b]
                
                # 相关性初筛
                if s1.corr(s2) < 0.85: continue
                
                # 协整性终筛
                score, pvalue, _ = coint(s1, s2)
                
                # 使用配置的阈值
                if pvalue < settings.PAIR_P_THRESHOLD:
                    valid_pairs.append({
                        'A': code_a, 'A_name': meta_map[code_a]['name'],
                        'B': code_b, 'B_name': meta_map[code_b]['name'],
                        'p_value': pvalue
                    })

        valid_pairs.sort(key=lambda x: x['p_value'])
        return valid_pairs[:self.max_pairs]