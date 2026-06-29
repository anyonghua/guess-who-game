"""二十问模式 API"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Question, GameSession
from app.services.twenty_q_engine import answer_question
from app.services.validator import validate_answer
from app.services.scoring import calculate_score

router = APIRouter()

MAX_QUESTIONS = 20


class AskRequest(BaseModel):
    question: str


class FinalGuessRequest(BaseModel):
    answer: str


# === API 路由 ===

@router.post("/start")
async def start_twenty_q(db: AsyncSession = Depends(get_db)):
    """开始一局二十问游戏"""
    # 随机选一道有 twenty_q_meta 的题
    query = (
        select(Question)
        .where(Question.twenty_q_meta != {})
        .order_by(func.random())
        .limit(1)
    )
    result = await db.execute(query)
    question = result.scalar_one_or_none()

    if not question:
        raise HTTPException(status_code=404, detail="题库为空")

    session = GameSession(
        id=str(uuid.uuid4()),
        mode="twenty_q",
        question_id=question.id,
        conversation=[],
    )
    db.add(session)
    await db.commit()

    return {
        "session_id": session.id,
        "remaining_questions": MAX_QUESTIONS,
        "message": "我已经想好一个人了！来问吧，只能问是/否问题。",
        "total_clues": MAX_QUESTIONS,
    }


@router.post("/{session_id}/ask")
async def ask_question(session_id: str, req: AskRequest, db: AsyncSession = Depends(get_db)):
    """二十问模式下提问"""
    session = await _get_session(session_id, db)
    if session.is_completed:
        raise HTTPException(status_code=400, detail="游戏已结束")

    question = await db.get(Question, session.question_id)
    meta = question.twenty_q_meta or {}

    # 计算剩余问题数
    conversation = session.conversation or []
    remaining = MAX_QUESTIONS - len(conversation)

    if remaining <= 0:
        raise HTTPException(status_code=400, detail="问题已用完，请提交最终猜测")

    # AI 回答
    response = answer_question(req.question, meta, remaining, MAX_QUESTIONS)

    # 记录对话
    conversation.append({
        "role": "player",
        "content": req.question,
    })
    conversation.append({
        "role": "ai",
        "content": response["response"],
        "answer": response["answer"],
        "emotion": response["emotion"],
    })
    session.conversation = conversation
    await db.commit()

    return {
        "session_id": session_id,
        "answer": response["answer"],
        "response": response["response"],
        "emotion": response["emotion"],
        "remaining_questions": remaining - 1,
        "hint": _get_hint(remaining - 1, MAX_QUESTIONS),
    }


@router.post("/{session_id}/final-guess")
async def final_guess(session_id: str, req: FinalGuessRequest, db: AsyncSession = Depends(get_db)):
    """二十问模式下提交最终猜测"""
    session = await _get_session(session_id, db)
    if session.is_completed:
        raise HTTPException(status_code=400, detail="游戏已结束")

    question = await db.get(Question, session.question_id)
    conversation = session.conversation or []
    remaining = MAX_QUESTIONS - len(conversation)

    # 验证答案
    result = validate_answer(req.answer, question.name, question.aliases or [])

    session.is_completed = True
    session.is_correct = result["correct"]

    if result["correct"]:
        # 计分：基于剩余问题数
        efficiency = remaining / MAX_QUESTIONS
        score = int(100 * 10 * efficiency * 1.5)
        session.score = score
    else:
        session.score = 50  # 猜错给安慰分

    await db.commit()

    return {
        "session_id": session_id,
        "correct": result["correct"],
        "match_type": result["match_type"],
        "actual_answer": question.name,
        "remaining_questions": remaining,
        "score": session.score,
        "efficiency": round(remaining / MAX_QUESTIONS * 100, 1),
        "rating": _get_rating(remaining, MAX_QUESTIONS),
    }


@router.get("/{session_id}/result")
async def get_result(session_id: str, db: AsyncSession = Depends(get_db)):
    """获取游戏结果"""
    session = await _get_session(session_id, db)
    question = await db.get(Question, session.question_id)
    conversation = session.conversation or []
    remaining = MAX_QUESTIONS - len(conversation)

    return {
        "session_id": session_id,
        "correct": session.is_correct,
        "answer": question.name,
        "score": session.score,
        "remaining_questions": remaining,
        "questions_asked": len(conversation) // 2,
        "efficiency": round(remaining / MAX_QUESTIONS * 100, 1),
        "rating": _get_rating(remaining, MAX_QUESTIONS),
        "conversation": conversation,
    }


# === 辅助函数 ===

def _get_hint(remaining: int, max_q: int) -> str:
    """根据剩余问题数给提示"""
    if remaining <= 1:
        return "最后一个问题了！想好再问，或者直接猜。"
    if remaining <= 3:
        return "问题不多了，抓住核心特征问。"
    if remaining <= max_q // 2:
        return "过半了，开始缩小范围吧。"
    return "还有充足的问题，先从大分类问起。"


def _get_rating(remaining: int, max_q: int) -> str:
    """根据剩余问题数评级"""
    efficiency = remaining / max_q
    if efficiency >= 0.75:
        return "⭐⭐⭐⭐⭐"
    if efficiency >= 0.5:
        return "⭐⭐⭐⭐"
    if efficiency >= 0.25:
        return "⭐⭐⭐"
    if efficiency > 0:
        return "⭐⭐"
    return "⭐"


async def _get_session(session_id: str, db: AsyncSession) -> GameSession:
    session = await db.get(GameSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="游戏会话不存在")
    return session
