"""猜猜TA是谁 - FastAPI 后端入口"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import game, questions


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    await init_db()
    yield


app = FastAPI(
    title="🎭 猜猜TA是谁",
    description="猜人名小游戏 API",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game.router, prefix="/api/game", tags=["游戏"])
app.include_router(questions.router, prefix="/api/questions", tags=["题库"])


@app.get("/")
async def root():
    return {"message": "🎭 猜猜TA是谁 API", "version": "0.2.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}
