import sys
import os
sys.path.append(os.path.dirname(__file__))

from strategy import TitanStrategyV2
from unittest.mock import MagicMock, patch

def run_lite_test():
    print("🚀 启动 Titan-Lite 快速自测模式 (Mocking Data Providers)...")
    
    # 模拟 data_provider 而不是直接模拟 valuation_screener.run，因为它是单例对象
    with patch('valuation_screener.valuation_screener.run') as mock_run:
         
        # 模拟 2 只股票
        mock_run.return_value = [
            {'symbol': 'AAPL', 'current_price': 150, 'target_price': 180, 'upside': 0.2, 'pe': 25, 'roe': 0.3, 'sector': 'Technology'},
            {'symbol': 'TSLA', 'current_price': 200, 'target_price': 250, 'upside': 0.25, 'pe': 50, 'roe': 0.15, 'sector': 'Consumer Cyclical'}
        ]
        
        # 实例化并运行
        strategy = TitanStrategyV2()
        
        # 模拟深度研判，避免真实 API 调用
        with patch.object(strategy, '_process_deep_analysis', side_effect=lambda x: {"symbol": x['symbol'], "action": "BUY", "logic": "Mocked Logic", "sector": x['sector']}), \
             patch.object(strategy, '_generate_market_panorama', return_value="Mocked Macro Report"), \
             patch.object(strategy, '_trigger_final_build', return_value=None):
            strategy.execute()
            
    print("✅ 快速自测完成！")

if __name__ == "__main__":
    run_lite_test()
