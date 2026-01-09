import os
import sys

class Config:
    """
    配置加载器
    从环境变量中读取配置，如果缺失则报错或使用默认值
    """
    try:
        # --- WeCom ---
        WECOM_CORP_ID = os.environ['WECOM_CORP_ID']
        WECOM_CORP_SECRET = os.environ['WECOM_CORP_SECRET']
        WECOM_AGENTS = {
            "private": os.environ['WECOM_AGENT_ID_PRIVATE'],
            "public": os.environ['WECOM_AGENT_ID_PUBLIC']
        }
        
        # --- LLM ---
        LLM_API_KEY = os.environ['LLM_API_KEY']
        LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.deepseek.com')
        
        # --- Strategy ---
        SCREENER_TOP_N = int(os.environ.get('SCREENER_TOP_N', 3))
        PAIR_P_THRESHOLD = float(os.environ.get('PAIR_P_VALUE_THRESHOLD', 0.05))
        TRADE_Z_THRESHOLD = float(os.environ.get('TRADE_Z_THRESHOLD', 1.5))
        MACRO_VOL_THRESHOLD = float(os.environ.get('MACRO_VOL_THRESHOLD', 0.35))
        
        # --- Data Source ---
        DATA_RETRY_ATTEMPTS = int(os.environ.get('DATA_RETRY_ATTEMPTS', 3))
        DATA_RETRY_WAIT = int(os.environ.get('DATA_RETRY_WAIT', 2))
        DATA_REQUEST_SLEEP = float(os.environ.get('DATA_REQUEST_SLEEP', 0.5))
        
    except KeyError as e:
        print(f"❌ 启动失败: 缺少环境变量配置 {e}")
        print("请检查 .env 文件")
        sys.exit(1)

# 单例模式导出
settings = Config()