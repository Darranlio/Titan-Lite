from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from strategy import run_job
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
def manual():
    run_job()
    return {"msg": "strategy triggered"}

@app.get("/backtest/{symbol}")
def run_backtest(symbol: str):
    result = backtester.run_simple_backtest(symbol)
    return result if result else {"error": "symbol not found"}

@app.get("/forecast/{symbol}")
def run_forecast(symbol: str):
    result = backtester.forecast_price(symbol)
    return result