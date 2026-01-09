from data_provider import data_provider
from config import settings
import time
import random

def run_screener():
    print(">>> [1/5] 启动全市场扫描 (Smart Screener)...")
    
    # 1. 获取所有行业
    try:
        all_sectors = data_provider.get_sector_list()
    except:
        # 保底逻辑
        all_sectors = ["酿酒行业", "电池", "半导体", "银行"]
        
    all_candidates = []
    
    # 2. 遍历行业 (演示模式取前10个，生产环境请去掉切片)
    # for sector in all_sectors:
    for sector in all_sectors[:10]: 
        try:
            # 调用适配器获取数据
            df = data_provider.get_sector_stocks(sector)
            
            # --- 财务过滤 ---
            # 剔除亏损(PE<0), 剔除泡沫(PE>100), 剔除僵尸(换手<0.3)
            df = df[(df['pe'] > 0) & (df['pe'] < 100) & (df['turnover'] > 0.3)]
            
            # --- 龙头法则 ---
            # 按市值排序，取配置的前 N 名
            leaders = df.sort_values(by='market_cap', ascending=False).head(settings.SCREENER_TOP_N)
            leaders['sector'] = sector # 打上行业标签
            
            all_candidates.extend(leaders[['symbol', 'name', 'sector', 'market_cap']].to_dict(orient='records'))
            
            # 随机休眠
            time.sleep(random.uniform(0.1, 0.3))
            
        except Exception as e:
            print(f"扫描板块 {sector} 失败: {e}")
            continue
            
    # 去重
    unique = {s['symbol']: s for s in all_candidates}
    final_list = list(unique.values())
    
    print(f"筛选完成，共入选 {len(final_list)} 只龙头。")
    return final_list