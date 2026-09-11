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
    
    # --- Analysis Mode (V2.2) ---
    # Options: 'debate' (multi-agent graph), 'solo' (single prompt expert), 'quant' (pure quantitative)
    ANALYSIS_MODE = os.environ.get('ANALYSIS_MODE', 'solo')

    
    # --- Professional Data Sources (V2.1) ---
    FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY', '')
    FMP_API_KEY = os.environ.get('FMP_API_KEY', '')
    
    # --- Strategy V2 ---
    SCREENER_MIN_UPSIDE = float(os.environ.get('SCREENER_MIN_UPSIDE', 0.10))
    TRADE_Z_THRESHOLD = float(os.environ.get('TRADE_Z_THRESHOLD', 1.5))
    MACRO_VOL_THRESHOLD = float(os.environ.get('MACRO_VOL_THRESHOLD', 0.35))

    # --- Screener Quality Gates (P0) ---
    SCREENER_MAX_UPSIDE = float(os.environ.get('SCREENER_MAX_UPSIDE', 0.80))          # 涨幅合理性上限，>80% 视为脏数据
    SCREENER_MIN_MARKET_CAP_US = float(os.environ.get('SCREENER_MIN_MARKET_CAP_US', 1e9))          # $1B
    SCREENER_MIN_MARKET_CAP_ASHARE = float(os.environ.get('SCREENER_MIN_MARKET_CAP_ASHARE', 100e8))  # 100亿 CNY
    SCREENER_MIN_MARKET_CAP_HK = float(os.environ.get('SCREENER_MIN_MARKET_CAP_HK', 100e8))          # 100亿 HKD
    SCREENER_MIN_PRICE_US = float(os.environ.get('SCREENER_MIN_PRICE_US', 5.0))       # 剔除仙股
    SCREENER_MIN_ANALYST_COUNT = int(os.environ.get('SCREENER_MIN_ANALYST_COUNT', 3)) # 分析师覆盖下限
    SCREENER_MIN_ROE = float(os.environ.get('SCREENER_MIN_ROE', 0.05))
    SCREENER_ASHARE_TOP_N = int(os.environ.get('SCREENER_ASHARE_TOP_N', 200))         # 按成交额截断
    SCREENER_HK_TOP_N = int(os.environ.get('SCREENER_HK_TOP_N', 100))
    SCREENER_US_ACTIVE_TOP_N = int(os.environ.get('SCREENER_US_ACTIVE_TOP_N', 30))
    
    # --- Data Source ---
    DATA_RETRY_ATTEMPTS = int(os.environ.get('DATA_RETRY_ATTEMPTS', 3))
    DATA_RETRY_WAIT = int(os.environ.get('DATA_RETRY_WAIT', 2))
    DATA_REQUEST_SLEEP = float(os.environ.get('DATA_REQUEST_SLEEP', 0.5))

    # --- Test & Auth Mode ---
    # Set to True to allow seeing verification codes in the UI (for friend testing)
    IS_TEST_MODE = os.environ.get('IS_TEST_MODE', 'True').lower() == 'true'

# 单例模式导出
settings = Config()