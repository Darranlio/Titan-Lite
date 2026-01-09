from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from strategy import run_job

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    # 每天 15:05 执行
    scheduler.add_job(run_job, 'cron', hour=15, minute=5, id='daily_strategy')
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/")
def root(): return {"status": "ok"}

@app.post("/run")
def manual():
    run_job()
    return {"msg": "triggered"}