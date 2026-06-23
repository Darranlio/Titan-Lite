import warnings
# 抑制 LangChain/LangGraph 与 Matplotlib 的冗余告警
warnings.filterwarnings("ignore", message=".*allowed_objects.*")
warnings.filterwarnings("ignore", message=".*findfont.*")

from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from strategy import run_job, run_single
from backtester import backtester
from portfolio_manager import portfolio_manager
from sys_logger import sys_logger, SystemLogger
from data_provider import data_provider
from archive_manager import archive_manager
from user_manager import user_manager
from orchestrator.context import UserContext
from orchestrator.engine import TitanWorkflowEngine
from orchestrator.workflows import TICKER_DEEP_RESEARCH_WORKFLOW
from utils import sanitize_json_data
import os
import multiprocessing
import time
import asyncio

# --- Authentication Helpers ---
# Set auto_error=False to allow optional authentication for log polling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        return None
    payload = user_manager.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

# --- Lifespan and Global State ---
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass

running_processes = {}

def start_analysis_process(symbol, user_context_dict, mode="solo"):
    """在独立进程中运行研判任务 (Identity Aware + Workflow Engine)"""
    try:
        user_ctx = UserContext(**user_context_dict)
        from config import settings
        settings.ANALYSIS_MODE = mode

        # Re-initialize global logger for this process to ensure isolation
        from sys_logger import sys_logger
        sys_logger.__init__(storage_root=user_ctx.storage_root)
        sys_logger.set_default_task_type("single")
        sys_logger.info(f"🚀 [Orchestrator] 启动 {symbol} 的标准化研判工作流...", task_type="single")

        # Initialize Engine
        engine = TitanWorkflowEngine()

        # Run the professional workflow
        async def _run():
            res_ctx = await engine.execute(
                job_id=f"job_{int(time.time())}",
                ticker=symbol,
                workflow_dsl=TICKER_DEEP_RESEARCH_WORKFLOW,
                user_ctx=user_ctx,
                initial_payload={}
            )
            deep_res = res_ctx.get_output("deep_analysis")
            action = "未知"
            if deep_res and "decision" in deep_res and deep_res["decision"]:
                action = deep_res["decision"].get("action", "未知")
            sys_logger.info(f"✅ {symbol} 研判任务圆满完成！建议: {action}", stage="Completed", progress=100)

        asyncio.run(_run())

    except Exception as e:
        from sys_logger import sys_logger
        sys_logger.info(f"❌ 工作流执行异常: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Scheduled jobs currently run with default_user context (internal/batch mode)
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_job, 'cron', hour=15, minute=5, id='daily_strategy_v2')
    scheduler.start()
    yield
    # 清理所有残余进程
    for p in running_processes.values():
        if p.is_alive(): p.terminate()
    scheduler.shutdown()

# --- FastAPI App Initialization ---
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from config import settings

# --- Authentication Endpoints ---
@app.post("/auth/send-code")
def send_code(email: str):
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address")
    code = user_manager.send_verification_code(email)

    # In Test Mode, we return the code directly to the frontend
    if settings.IS_TEST_MODE:
        return {"message": "Verification code sent", "debug_code": code}
    return {"message": "Verification code sent"}

@app.post("/auth/register")
def register(username: str, password: str, email: str, code: str):
    success = user_manager.register_user(username, password, email, code)
    if not success:
        raise HTTPException(status_code=400, detail="Registration failed. Check code or username/email availability.")
    return {"message": "User registered successfully"}

@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = user_manager.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = user_manager.create_access_token(data={
        "sub": user["username"],
        "role": user["role"],
        "avatar_url": user.get("avatar_url")
    })
    return {"access_token": access_token, "token_type": "bearer"}

# --- General Endpoints ---
@app.get("/")
def root(): return {"status": "ok", "version": "v7.0-stable"}

from pydantic import BaseModel

class RunRequest(BaseModel):
    market: str = "Global"
    mode: str = "solo"

from fastapi import Body

def start_batch_process(user_context_dict, market="Global", mode="solo"):
    """在独立进程中运行全市场扫描任务 (Orchestrator Workflow 版)"""
    try:
        user_ctx = UserContext(**user_context_dict)
        from config import settings
        settings.ANALYSIS_MODE = mode
        from sys_logger import sys_logger
        sys_logger.__init__(storage_root=user_ctx.storage_root)
        sys_logger.set_default_task_type("batch")
        
        # 不再在此处 clear，已在主进程完成
        sys_logger.info(f"🚀 [Orchestrator] 启动[{market}]全市场深度扫描工作流...", task_type="batch")
        
        # Initialize Engine
        engine = TitanWorkflowEngine()
        from orchestrator.workflows import MARKET_SCAN_WORKFLOW

        async def _run():
            # 为工作流注入初始输入 (市场类型)
            job_id = f"batch_{int(time.time())}"
            await engine.execute(
                job_id=job_id,
                ticker="MARKET", # 全局任务使用 MARKET 作为占位符
                workflow_dsl=MARKET_SCAN_WORKFLOW,
                user_ctx=user_ctx,
                initial_payload={"market": market}
            )

        asyncio.run(_run())
        
    except Exception as e:
        from sys_logger import sys_logger
        sys_logger.info(f"❌ 批量扫描工作流执行异常: {e}", stage="Error", task_type="batch")

@app.post("/run")
def run_all(req: RunRequest = Body(...), current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    username = current_user["sub"]
    user_ctx = UserContext(
        user_id=username,
        role=current_user["role"],
        storage_root=f"docs/projects/titan-lite/users/{username}"
    )

    # 1. 在主进程中立即原子化清空旧日志，杜绝残留
    user_logger = SystemLogger(storage_root=user_ctx.storage_root)
    user_logger.clear(stage="Initializing", progress=0, task_type="batch")
    
    # 确保 market 参数被正确解包并传递
    p = multiprocessing.Process(target=start_batch_process, args=(user_ctx.dict(), req.market, req.mode))
    p.start()
    running_processes["BATCH"] = p
    return {"status": "started", "job": "batch", "market": req.market, "mode": req.mode, "task_type": "batch"}

@app.post("/analyze/{symbol}")
def analyze_one(symbol: str, mode: str = "solo", current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    symbol = symbol.upper()
    username = current_user["sub"]
    user_ctx = UserContext(
        user_id=username,
        role=current_user["role"],
        storage_root=f"docs/projects/titan-lite/users/{username}"
    )

    # 1. 在主进程中立即清空日志
    user_logger = SystemLogger(storage_root=user_ctx.storage_root)
    user_logger.clear(stage="Initializing", progress=0, task_type="single")

    # Ensure directory exists
    base_proj_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.makedirs(os.path.join(base_proj_path, user_ctx.storage_root), exist_ok=True)

    p = multiprocessing.Process(target=start_analysis_process, args=(symbol, user_ctx.dict(), mode))
    p.start()
    running_processes[symbol] = p
    return {"status": "started", "symbol": symbol, "user": username, "task_type": "single"}

import os
import multiprocessing
import time
import asyncio
import signal

# --- 信号处理与进程组控制 ---
def start_process_with_grp(target, args):
    """启动带进程组的任务，便于斩草除根"""
    p = multiprocessing.Process(target=target, args=args)
    # 在 Unix 系统下设置进程组
    if os.name != 'nt':
        p = multiprocessing.Process(target=target, args=args)
        # 使用包装器在启动前执行 setpgrp
        def target_wrapper(*args):
            os.setpgrp()
            target(*args)
        p = multiprocessing.Process(target=target_wrapper, args=args)
    
    p.start()
    return p

def kill_process_grp(p):
    """清理进程"""
    if not p or not p.is_alive():
        return
    try:
        p.kill()
    except:
        pass

@app.post("/run")
def run_all(req: RunRequest = Body(...), current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    username = current_user["sub"]
    user_ctx = UserContext(
        user_id=username,
        role=current_user["role"],
        storage_root=f"docs/projects/titan-lite/users/{username}"
    )

    # 1. 在主进程中立即原子化清空旧日志
    user_logger = SystemLogger(storage_root=user_ctx.storage_root)
    user_logger.clear(stage="Initializing", progress=0, task_type="batch")
    
    # 2. 启动带进程组的批量扫描
    p = start_process_with_grp(start_batch_process, (user_ctx.dict(), req.market, req.mode))
    running_processes["BATCH"] = p
    return {"status": "started", "job": "batch", "market": req.market, "mode": req.mode, "task_type": "batch"}

@app.post("/analyze/{symbol}")
def analyze_one(symbol: str, mode: str = "solo", current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    symbol = symbol.upper()
    username = current_user["sub"]
    user_ctx = UserContext(
        user_id=username,
        role=current_user["role"],
        storage_root=f"docs/projects/titan-lite/users/{username}"
    )

    # 1. 在主进程中立即清空日志
    user_logger = SystemLogger(storage_root=user_ctx.storage_root)
    user_logger.clear(stage="Initializing", progress=0, task_type="single")

    # Ensure directory exists
    base_proj_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.makedirs(os.path.join(base_proj_path, user_ctx.storage_root), exist_ok=True)

    # 2. 启动带进程组的个股深研
    p = start_process_with_grp(start_analysis_process, (symbol, user_ctx.dict(), mode))
    running_processes[symbol] = p
    return {"status": "started", "symbol": symbol, "user": username, "task_type": "single"}

@app.post("/stop")
def stop_tasks(task_type: str = "all", current_user: dict = Depends(get_current_user)):
    """停止正在运行的任务，支持按类型停止"""
    if not current_user:
        raise HTTPException(status_code=401)
    
    username = current_user["sub"]
    user_logger = SystemLogger(storage_root=f"docs/projects/titan-lite/users/{username}")
    
    count = 0
    to_delete = []
    
    # 定义要清理的任务通道列表
    # 注意：此时不重置 'none' 通道，除非明确是 'all'
    channels_to_idle = []
    if task_type == "all": channels_to_idle = ["batch", "single"]
    else: channels_to_idle = [task_type]

    for sym, p in list(running_processes.items()):
        is_batch_p = (sym == "BATCH")
        current_p_type = "batch" if is_batch_p else "single"
        
        should_stop = (task_type == "all") or (task_type == current_p_type)
            
        if should_stop:
            # 使用进程组暴力清理
            kill_process_grp(p)
            count += 1
            to_delete.append(sym)
            
            # 记录停止日志
            msg = "🛑 全市场扫描已手动停止" if is_batch_p else f"🛑 {sym} 深度研判已手动停止"
            user_logger.info(msg, stage="Stopped", progress=0, task_type=current_p_type)

    # 核心修复：物理重置特定赛道的状态，解冻 UI
    for t in channels_to_idle:
        user_logger.force_idle(task_type=t)

    for sym in to_delete:
        if sym in running_processes:
            del running_processes[sym]
    
    return {"status": "stopped", "count": count, "task_type": task_type}

@app.get("/search")
async def search_ticker(q: str):
    return await data_provider.search_ticker_async(q)

@app.get("/logs")
def get_logs(type: str = "none", current_user: dict = Depends(get_current_user)):
    # Strict Isolation: Only show logs if authenticated
    if current_user:
        username = current_user["sub"]
        user_logger = SystemLogger(storage_root=f"docs/projects/titan-lite/users/{username}")
        # 如果 type 为 none，则默认返回主日志（向前兼容）
        # 否则返回对应的专项日志
        t_type = None if type == "none" else type
        return sanitize_json_data(user_logger.get_latest(task_type=t_type))
    else:
        # Return empty state instead of falling back to global/stale logs
        return {"logs": ["Please login to see live research progress."], "stage": "Auth Required", "progress": 0}

@app.post("/logs/clear")
def clear_logs(current_user: dict = Depends(get_current_user)):
    if current_user:
        username = current_user["sub"]
        user_logger = SystemLogger(storage_root=f"docs/projects/titan-lite/users/{username}")
    else:
        user_logger = sys_logger
    user_logger.clear()
    return {"status": "ok"}

# --- Archive Management Endpoints ---
@app.get("/archive/list")
def list_archive(current_user: dict = Depends(get_current_user)):
    if not current_user: raise HTTPException(status_code=401)
    username = current_user["sub"]
    storage_root = f"docs/projects/titan-lite/users/{username}"
    user_archive = archive_manager.__class__(storage_root=storage_root)
    return sanitize_json_data(user_archive.get_all_reports())

@app.delete("/archive/{symbol}/{file_ts}")
def delete_report(symbol: str, file_ts: str, current_user: dict = Depends(get_current_user)):
    if not current_user: raise HTTPException(status_code=401)
    username = current_user["sub"]
    storage_root = f"docs/projects/titan-lite/users/{username}"
    user_archive = archive_manager.__class__(storage_root=storage_root)
    success, msg = user_archive.delete_single_report(symbol, file_ts)
    return {"status": "success" if success else "failed", "msg": msg}

@app.delete("/archive/{symbol}")
def delete_symbol(symbol: str, current_user: dict = Depends(get_current_user)):
    if not current_user: raise HTTPException(status_code=401)
    username = current_user["sub"]
    storage_root = f"docs/projects/titan-lite/users/{username}"
    user_archive = archive_manager.__class__(storage_root=storage_root)
    success, msg = user_archive.delete_full_archive(symbol)
    return {"status": "success" if success else "failed", "msg": msg}

# --- Portfolio Endpoints ---
def get_user_pm(current_user: dict):
    if not current_user: raise HTTPException(status_code=401)
    username = current_user["sub"]
    return portfolio_manager.__class__(storage_root=f"docs/projects/titan-lite/users/{username}")

def portfolio_result(success: bool, msg: str, status_code: int = 400):
    if not success:
        raise HTTPException(status_code=status_code, detail=msg)
    return {"status": "success", "msg": msg}

@app.post("/portfolio/trade")
def record_trade(symbol: str, side: str, quantity: float, price: float, date: str = None, current_user: dict = Depends(get_current_user)):

    user_pm = get_user_pm(current_user)
    success, msg = user_pm.record_transaction(symbol, side, quantity, price, date)
    return portfolio_result(success, msg)

@app.get("/portfolio/status")
def get_status(current_user: dict = Depends(get_current_user)):
    user_pm = get_user_pm(current_user)
    return sanitize_json_data(user_pm.calculate_nav())

@app.get("/portfolio/history")
def get_history(current_user: dict = Depends(get_current_user)):
    user_pm = get_user_pm(current_user)
    return sanitize_json_data(user_pm.get_transaction_history())

@app.delete("/portfolio/trade/{tx_id}")
def delete_trade(tx_id: int, current_user: dict = Depends(get_current_user)):
    user_pm = get_user_pm(current_user)
    success, msg = user_pm.delete_transaction(tx_id)
    return portfolio_result(success, msg)

@app.get("/portfolio/analysis")
def get_analysis(current_user: dict = Depends(get_current_user)):
    user_pm = get_user_pm(current_user)
    metrics = user_pm.calculate_risk_metrics()
    history = user_pm.get_nav_history()
    return sanitize_json_data({"metrics": metrics, "history": history})

# --- Pending Orders Endpoints ---
@app.get("/portfolio/pending")
def get_pending(current_user: dict = Depends(get_current_user)):
    user_pm = get_user_pm(current_user)
    return user_pm.get_pending_orders()

@app.delete("/portfolio/pending/{order_id}")
def clear_pending(order_id: int, current_user: dict = Depends(get_current_user)):
    user_pm = get_user_pm(current_user)
    success, msg = user_pm.clear_pending_order(order_id)
    return portfolio_result(success, msg)

@app.post("/portfolio/pending/execute/{order_id}")
def execute_pending(order_id: int, current_user: dict = Depends(get_current_user)):
    user_pm = get_user_pm(current_user)
    orders = user_pm.get_pending_orders()
    order = next((o for o in orders if o['id'] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    success, msg = user_pm.record_transaction(
        order['symbol'], order['side'], order['quantity'], order['price']
    )
    if success:
        user_pm.clear_pending_order(order_id)
    return portfolio_result(success, msg)

@app.get("/portfolio/diagnosis")
def get_diag(current_user: dict = Depends(get_current_user)):
    user_pm = get_user_pm(current_user)
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    macro_path = os.path.join(base_path, "docs", "projects", "titan-lite", "reports", "market_overview.md")
    macro_context = "暂无宏观背景数据"
    if os.path.exists(macro_path):
        with open(macro_path, "r", encoding="utf-8") as f:
            macro_context = f.read()
    return {"report": user_pm.get_portfolio_diagnosis(macro_context)}

@app.get("/market/benchmarks")
def get_benchmarks():
    return sanitize_json_data(data_provider.get_market_benchmarks())

@app.get("/market/sectors")
def get_sectors():
    return sanitize_json_data(data_provider.get_sector_status())

