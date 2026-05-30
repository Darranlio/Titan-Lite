from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from strategy import run_job, run_single
from backtester import backtester
from portfolio_manager import portfolio_manager
from sys_logger import sys_logger
from data_provider import data_provider
from archive_manager import archive_manager
import os
import multiprocessing

# 强制使用 spawn 模式，避免 fork 导致的 asyncio/fd 继承问题
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass

# 全局存储正在运行的进程
running_processes = {}

def start_analysis_process(symbol):
    """在独立进程中运行研判任务"""
    try:
        run_single(symbol)
    except Exception as e:
        sys_logger.info(f"子进程异常退出: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_job, 'cron', hour=15, minute=5, id='daily_strategy_v2')
    scheduler.start()
    yield
    # 清理所有残余进程
    for p in running_processes.values():
        if p.is_alive(): p.terminate()
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

@app.post("/analyze/{symbol}")
def analyze_one(symbol: str):
    symbol = symbol.upper()
    # 如果已有同名任务在跑，先杀掉
    if symbol in running_processes and running_processes[symbol].is_alive():
        running_processes[symbol].terminate()
    
    # 立即清理旧日志，确保前端看到的是最新进度
    sys_logger.clear()
    
    p = multiprocessing.Process(target=start_analysis_process, args=(symbol,))
    p.start()
    running_processes[symbol] = p
    return {"status": "started", "symbol": symbol}

@app.post("/stop")
def stop_all():
    """停止所有正在运行的分析任务"""
    count = 0
    for sym, p in running_processes.items():
        if p.is_alive():
            p.terminate()
            count += 1
    sys_logger.clear()
    sys_logger.info("🛑 用户手动终止了所有正在运行的研判任务。")
    return {"status": "stopped", "count": count}

@app.get("/search")
async def search_ticker(q: str):
    # 搜索现在会非常快，因为 AI 任务在独立进程
    return await data_provider.search_ticker_async(q)

@app.get("/logs")
def get_logs():
    return sys_logger.get_latest()

@app.post("/logs/clear")
def clear_logs():
    sys_logger.clear()
    return {"status": "ok"}

# --- Archive Management Endpoints (Phase 4.5) ---

@app.get("/archive/list")
def list_archive():
    return archive_manager.get_all_reports()

@app.delete("/archive/{symbol}/{file_ts}")
def delete_report(symbol: str, file_ts: str):
    success, msg = archive_manager.delete_single_report(symbol, file_ts)
    return {"status": "success" if success else "failed", "msg": msg}

@app.delete("/archive/{symbol}")
def delete_symbol(symbol: str):
    success, msg = archive_manager.delete_full_archive(symbol)
    return {"status": "success" if success else "failed", "msg": msg}

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

# --- Pending Orders Endpoints (Phase 4) ---

@app.get("/portfolio/pending")
def get_pending():
    return portfolio_manager.get_pending_orders()

@app.delete("/portfolio/pending/{order_id}")
def clear_pending(order_id: int):
    success, msg = portfolio_manager.clear_pending_order(order_id)
    return {"status": "success" if success else "failed", "msg": msg}

@app.post("/portfolio/pending/execute/{order_id}")
def execute_pending(order_id: int):
    # Fetch the order first
    orders = portfolio_manager.get_pending_orders()
    order = next((o for o in orders if o['id'] == order_id), None)
    if not order:
        return {"status": "failed", "msg": "Order not found"}
    
    # Record as a real transaction
    success, msg = portfolio_manager.record_transaction(
        order['symbol'], order['side'], order['quantity'], order['price']
    )
    if success:
        # Clear it from pending
        portfolio_manager.clear_pending_order(order_id)
    return {"status": "success" if success else "failed", "msg": msg}

@app.get("/portfolio/diagnosis")
def get_diag():
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    macro_path = os.path.join(base_path, "docs", "projects", "titan-lite", "reports", "market_overview.md")
    macro_context = "暂无宏观背景数据"
    if os.path.exists(macro_path):
        with open(macro_path, "r", encoding="utf-8") as f:
            macro_context = f.read()
    return {"report": portfolio_manager.get_portfolio_diagnosis(macro_context)}
