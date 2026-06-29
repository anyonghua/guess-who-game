"""猜猜TA是谁 - FastAPI 后端入口"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio as socketio_lib

from app.database import init_db
from app.routers import game, questions, twenty_q, chain, battle
from app.services.battle_service import sio


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


fastapi_app = FastAPI(
    title="🎭 猜猜TA是谁",
    description="猜人名小游戏 API",
    version="0.5.0",
    lifespan=lifespan,
)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fastapi_app.include_router(game.router, prefix="/api/game/progressive", tags=["渐进揭秘"])
fastapi_app.include_router(twenty_q.router, prefix="/api/game/twenty-q", tags=["二十问"])
fastapi_app.include_router(chain.router, prefix="/api/game/chain", tags=["描述接龙"])
fastapi_app.include_router(battle.router, prefix="/api/battle", tags=["对战"])
fastapi_app.include_router(questions.router, prefix="/api/questions", tags=["题库"])


@fastapi_app.get("/")
async def root():
    return {"message": "🎭 猜猜TA是谁 API", "version": "0.5.0"}


@fastapi_app.get("/health")
async def health():
    return {"status": "ok"}


# Socket.IO 挂载到 FastAPI
app = socketio_lib.ASGIApp(sio, other_asgi_app=fastapi_app)
