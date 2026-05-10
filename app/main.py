from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from strategy import run_job, run_single
from backtester import backtester
from portfolio_manager import portfolio_manager
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_job, 'cron', hour=15, minute=5, id='daily_strategy_v2')
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root(): return {"status": "ok", "version": "v7.0-stable"}

@app.post("/run")
def trigger_batch():
    run_job()
    return {"msg": "batch strategy triggered"}

@app.post("/analyze/{symbol}")
def analyze_one(symbol: str):
    success = run_single(symbol)
    return {"status": "success" if success else "failed", "symbol": symbol}

# --- Portfolio Endpoints (V7.0) ---

@app.post("/portfolio/trade")
def record_trade(symbol: str, side: str, quantity: int, price: float, date: str = None):
    success, msg = portfolio_manager.record_transaction(symbol, side, quantity, price, date)
    return {"status": "success" if success else "failed", "msg": msg}

@app.get("/portfolio/status")
def get_status():
    return portfolio_manager.calculate_nav()

@app.get("/portfolio/history")
def get_history():
    return portfolio_manager.get_transaction_history()

@app.delete("/portfolio/trade/{tx_id}")
def delete_trade(tx_id: int):
    success, msg = portfolio_manager.delete_transaction(tx_id)
    return {"status": "success" if success else "failed", "msg": msg}

@app.get("/portfolio/analysis")
def get_analysis():
    metrics = portfolio_manager.calculate_risk_metrics()
    history = portfolio_manager.get_nav_history()
    return {"metrics": metrics, "history": history}

@app.get("/portfolio/diagnosis")
def get_diag():
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    macro_path = os.path.join(base_path, "docs", "projects", "titan-lite", "reports", "market_overview.md")
    macro_context = "暂无宏观背景数据"
    if os.path.exists(macro_path):
        with open(macro_path, "r", encoding="utf-8") as f:
            macro_context = f.read()
    return {"report": portfolio_manager.get_portfolio_diagnosis(macro_context)}
