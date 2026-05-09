import os
import sys
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class Config:
    """
    配置加载器 V2
    """
    # --- WeCom ---
    WECOM_CORP_ID = os.environ.get('WECOM_CORP_ID', '')
    WECOM_CORP_SECRET = os.environ.get('WECOM_CORP_SECRET', '')
    WECOM_AGENTS = {
        "private": os.environ.get('WECOM_AGENT_ID_PRIVATE', ''),
        "public": os.environ.get('WECOM_AGENT_ID_PUBLIC', '')
    }
    
    # --- LLM ---
    LLM_API_KEY = os.environ.get('LLM_API_KEY', '')
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.deepseek.com')
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
    LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'deepseek') # 'deepseek', 'openai' or 'google'
    
    # --- Professional Data Sources (V2.1) ---
    FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY', '')
    FMP_API_KEY = os.environ.get('FMP_API_KEY', '')
    
    # --- Strategy V2 ---
    SCREENER_MIN_UPSIDE = float(os.environ.get('SCREENER_MIN_UPSIDE', 0.10))
    TRADE_Z_THRESHOLD = float(os.environ.get('TRADE_Z_THRESHOLD', 1.5))
    MACRO_VOL_THRESHOLD = float(os.environ.get('MACRO_VOL_THRESHOLD', 0.35))
    
    # --- Data Source ---
    DATA_RETRY_ATTEMPTS = int(os.environ.get('DATA_RETRY_ATTEMPTS', 3))
    DATA_RETRY_WAIT = int(os.environ.get('DATA_RETRY_WAIT', 2))
    DATA_REQUEST_SLEEP = float(os.environ.get('DATA_REQUEST_SLEEP', 0.5))

# 单例模式导出
settings = Config()