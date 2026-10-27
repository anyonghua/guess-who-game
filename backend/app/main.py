"""猜猜TA是谁 - FastAPI 后端入口"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio as socketio_lib

from app.database import init_db
from app.routers import game, questions, twenty_q, chain, battle, user, daily, generator
from app.services.battle_service import sio


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


fastapi_app = FastAPI(
    title="🎭 猜猜TA是谁",
    description="猜人名小游戏 API",
    version="0.6.0",
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
fastapi_app.include_router(user.router, prefix="/api/user", tags=["用户"])
fastapi_app.include_router(questions.router, prefix="/api/questions", tags=["题库"])
fastapi_app.include_router(daily.router, prefix="/api/daily", tags=["每日挑战"])
fastapi_app.include_router(generator.router, prefix="/api/generator", tags=["动态出题"])


@fastapi_app.get("/api")
async def root():
    return {"message": "🎭 猜猜TA是谁 API", "version": "0.6.0"}


@fastapi_app.get("/health")
async def health():
    return {"status": "ok"}


# === SPA 静态托管（单体部署：前端 dist 由 FastAPI 直接服务，无需 nginx）===
# 路由优先级：/api/* 与 /health 已在上面注册，mount("/") 只兜底剩余路径；
# history 路由模式需要未命中的路径回退到 index.html
from pathlib import Path
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.staticfiles import StaticFiles

_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404:
                return await super().get_response("index.html", scope)
            raise


if _DIST.is_dir():
    fastapi_app.mount("/", SPAStaticFiles(directory=str(_DIST), html=True), name="spa")


app = socketio_lib.ASGIApp(sio, other_asgi_app=fastapi_app)
