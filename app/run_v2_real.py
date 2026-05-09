from strategy import TitanStrategyV2
import os
from dotenv import load_dotenv

def run_real_test():
    # 确保加载了环境变量
    load_dotenv()
    
    print(">>> [V2 Real Test] 启动真实 Gemini AI 研判测试...")
    
    # 实例化策略
    strat = TitanStrategyV2()
    
    # 执行
    # 注意：这会调用真实 Gemini API，产生少量 Token 消耗
    # 它会自动扫描热点标的并选择前几个进行深度研判
    strat.execute()
    
    print("\n>>> 测试完成！请检查 docs/projects/titan-lite/reports/ 查看生成的研报。")

if __name__ == "__main__":
    run_real_test()
