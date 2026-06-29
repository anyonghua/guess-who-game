"""游戏核心 API - 渐进揭秘模式"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Question, GameSession
from app.services.validator import validate_answer
from app.services.scoring import calculate_score

router = APIRouter()


# === 请求/响应模型 ===

class StartRequest(BaseModel):
    difficulty: str = "normal"
    category: Optional[str] = None


class GuessRequest(BaseModel):
    answer: str


class SessionResponse(BaseModel):
    session_id: str
    clue_index: int
    clue: str
    total_clues: int
    score: int
    streak: int


class GuessResponse(BaseModel):
    correct: bool
    match_type: str
    message: str
    points: int
    session_id: str
    clue_index: int
    clue: Optional[str] = None
    score: int
    streak: int
    temperature: Optional[dict] = None


# === API 路由 ===

@router.post("/progressive/start", response_model=SessionResponse)
async def start_game(req: StartRequest, db: AsyncSession = Depends(get_db)):
    """开始一局渐进揭秘游戏"""
    # 随机选一道题
    query = select(Question)
    if req.category:
        query = query.where(Question.category == req.category)
    query = query.order_by(func.random()).limit(1)

    result = await db.execute(query)
    question = result.scalar_one_or_none()

    if not question:
        raise HTTPException(status_code=404, detail="题库为空，请先导入题目")

    # 创建游戏会话
    session = GameSession(
        id=str(uuid.uuid4()),
        mode="progressive",
        difficulty=req.difficulty,
        question_id=question.id,
        clue_index=0,
    )
    db.add(session)
    await db.commit()

    clues = question.progressive_clues or []
    return SessionResponse(
        session_id=session.id,
        clue_index=0,
        clue=clues[0] if clues else "无线索",
        total_clues=len(clues),
        score=0,
        streak=0,
    )


@router.get("/progressive/{session_id}/clue")
async def get_clue(session_id: str, db: AsyncSession = Depends(get_db)):
    """获取当前线索"""
    session = await _get_session(session_id, db)
    question = await db.get(Question, session.question_id)
    clues = question.progressive_clues or []

    if session.clue_index >= len(clues):
        raise HTTPException(status_code=400, detail="已无更多线索")

    return {
        "session_id": session_id,
        "clue_index": session.clue_index,
        "clue": clues[session.clue_index],
        "total_clues": len(clues),
    }


@router.post("/progressive/{session_id}/guess", response_model=GuessResponse)
async def submit_guess(session_id: str, req: GuessRequest, db: AsyncSession = Depends(get_db)):
    """提交猜测"""
    session = await _get_session(session_id, db)
    if session.is_completed:
        raise HTTPException(status_code=400, detail="游戏已结束")

    question = await db.get(Question, session.question_id)
    clues = question.progressive_clues or []

    # 验证答案
    result = validate_answer(req.answer, question.name, question.aliases or [])
    session.guess_count += 1

    if result["correct"]:
        # 计分
        score_result = calculate_score(
            session.clue_index,
            session.difficulty,
            session.streak,
            first_guess=(session.guess_count == 1)
        )
        session.score += score_result["score"]
        session.streak += 1
        session.is_completed = True
        session.is_correct = True

        await db.commit()

        return GuessResponse(
            correct=True,
            match_type=result["match_type"],
            message=f"✦ 命运已定：{question.name}",
            points=score_result["score"],
            session_id=session_id,
            clue_index=session.clue_index,
            clue=None,
            score=session.score,
            streak=session.streak,
        )
    else:
        session.streak = 0
        # 移到下一条线索
        next_index = session.clue_index + 1
        next_clue = None

        if next_index < len(clues):
            session.clue_index = next_index
            session.guess_count = 0
            next_clue = clues[next_index]
        else:
            # 线索用完，游戏结束
            session.is_completed = True
            session.is_correct = False

        await db.commit()

        # 温度提示
        temp_levels = [
            {"level": 0, "label": "相距甚远", "color": "#4A6A4A"},
            {"level": 1, "label": "略有眉目", "color": "#5A8F6A"},
            {"level": 2, "label": "渐入佳境", "color": "#C8A84E"},
            {"level": 3, "label": "呼之欲出", "color": "#CC8844"},
            {"level": 4, "label": "触手可及", "color": "#C42B2B"},
        ]
        temp = temp_levels[min(session.clue_index, 4)]

        return GuessResponse(
            correct=False,
            match_type=result["match_type"],
            message="💀 邪灵低语：此名非也...",
            points=0,
            session_id=session_id,
            clue_index=session.clue_index,
            clue=next_clue,
            score=session.score,
            streak=session.streak,
            temperature=temp,
        )


@router.get("/progressive/{session_id}/result")
async def get_result(session_id: str, db: AsyncSession = Depends(get_db)):
    """获取游戏结果"""
    session = await _get_session(session_id, db)
    question = await db.get(Question, session.question_id)

    return {
        "session_id": session_id,
        "correct": session.is_correct,
        "answer": question.name,
        "score": session.score,
        "clue_index": session.clue_index,
        "streak": session.streak,
        "stars": max(1, 5 - session.clue_index),
        "difficulty": session.difficulty,
    }


async def _get_session(session_id: str, db: AsyncSession) -> GameSession:
    session = await db.get(GameSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="游戏会话不存在")
    return session
