"""猜猜TA是谁 - FastAPI 后端入口"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import game, battle, social, questions

app = FastAPI(
    title="🎭 猜猜TA是谁",
    description="猜人名小游戏 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game.router, prefix="/api/game", tags=["游戏"])
app.include_router(battle.router, prefix="/api/battle", tags=["对战"])
app.include_router(social.router, prefix="/api/social", tags=["社交"])
app.include_router(questions.router, prefix="/api/questions", tags=["题库"])


@app.get("/")
async def root():
    return {"message": "🎭 猜猜TA是谁 API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}
