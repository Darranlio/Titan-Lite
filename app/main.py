from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from strategy import run_job, run_single
from backtester import backtester

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    # 每天 15:05 执行
    scheduler.add_job(run_job, 'cron', hour=15, minute=5, id='daily_strategy_v2')
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

# 允许跨域请求 (为了让 GitHub Pages 上的按钮能调到你的服务器)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 生产环境建议替换为你的具体 Pages 域名
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root(): return {"status": "ok", "version": "v2.1-institutional"}

@app.post("/run")
def manual_batch():
    run_job()
    return {"msg": "batch strategy triggered"}

@app.post("/analyze/{symbol}")
def analyze_one(symbol: str):
    success = run_single(symbol)
    return {"status": "success" if success else "failed", "symbol": symbol}

@app.get("/backtest/{symbol}")
def run_backtest(symbol: str):
    result = backtester.run_simple_backtest(symbol)
    return result if result else {"error": "symbol not found"}

@app.get("/forecast/{symbol}")
def run_forecast(symbol: str):
    result = backtester.forecast_price(symbol)
    return result

# --- 个人基金管理 (Portfolio Management) ---
from portfolio_manager import portfolio_manager

@app.post("/portfolio/trade")
def record_trade(symbol: str, side: str, quantity: int, price: float):
    """记录买卖记录"""
    success, msg = portfolio_manager.record_transaction(symbol, side, quantity, price)
    return {"status": "success" if success else "failed", "msg": msg}

@app.get("/portfolio/status")
def get_portfolio_status():
    """获取资产净值与持仓"""
    return portfolio_manager.calculate_nav()

@app.get("/portfolio/analysis")
def get_portfolio_analysis():
    """获取基金专业风险指标与历史曲线"""
    metrics = portfolio_manager.calculate_risk_metrics()
    history = portfolio_manager.get_nav_history()
    return {
        "metrics": metrics,
        "history": history
    }

@app.get("/portfolio/diagnosis")
def get_diagnosis():
    """AI 组合诊断"""
    import os
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    macro_path = os.path.join(base_path, "docs", "projects", "titan-lite", "reports", "market_overview.md")
    
    macro_context = "暂无宏观背景数据"
    if os.path.exists(macro_path):
        with open(macro_path, "r", encoding="utf-8") as f:
            macro_context = f.read()
            
    report = portfolio_manager.get_portfolio_diagnosis(macro_context)
    return {"report": report}
