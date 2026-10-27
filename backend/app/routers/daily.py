"""每日挑战 API

- POST /api/daily/start       开局（同日期全球同题）
- GET  /api/daily/{sid}/clue  再揭一条线索
- POST /api/daily/{sid}/guess 提交猜测
- POST /api/daily/{sid}/finish 结算并入榜
- GET  /api/daily/leaderboard 当日排行
- GET  /api/daily/today       今日概览（题目数+榜首，首页展示用）
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import DailyScore
from app.services import daily_service

router = APIRouter()


class StartRequest(BaseModel):
    player_name: Optional[str] = "匿名玩家"


class GuessRequest(BaseModel):
    answer: str


class FinishRequest(BaseModel):
    player_name: Optional[str] = None


@router.post("/start")
async def start_daily(req: StartRequest):
    """开始今日挑战（3 题：简单/中等/困难各一）"""
    return daily_service.start_session(req.player_name or "匿名玩家")


@router.get("/{session_id}/clue")
async def get_clue(session_id: str):
    """再揭一条线索"""
    try:
        return daily_service.get_clue(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="对局不存在或已过期")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/guess")
async def guess(session_id: str, req: GuessRequest):
    """提交猜测"""
    try:
        return daily_service.submit_guess(session_id, req.answer)
    except KeyError:
        raise HTTPException(status_code=404, detail="对局不存在或已过期")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/finish")
async def finish(session_id: str, req: FinishRequest, db: AsyncSession = Depends(get_db)):
    """结算成绩并写入当日排行榜（幂等）"""
    try:
        result = daily_service.finish_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="对局不存在或已过期")

    if req.player_name:
        result["player_name"] = req.player_name

    # 幂等：同一 session 只写一条
    existing = await db.execute(
        select(DailyScore).where(DailyScore.date == result["date"]).where(
            DailyScore.player_name == result["player_name"]
        ).where(DailyScore.score == result["total_score"])
    )
    if existing.scalars().first() is None:
        db.add(DailyScore(
            date=result["date"],
            player_name=result["player_name"],
            score=result["total_score"],
            correct=result["correct"],
            total_clues=result["total_clues"],
        ))
        await db.commit()

    # 当日排名
    rows = await db.execute(
        select(DailyScore).where(DailyScore.date == result["date"]).order_by(
            desc(DailyScore.score), DailyScore.total_clues
        )
    )
    scores = rows.scalars().all()
    rank = 1
    for i, row in enumerate(scores):
        if row.player_name == result["player_name"] and row.score == result["total_score"]:
            rank = i + 1
            break
    result["rank"] = rank
    result["total_players"] = len(scores)
    return result


@router.get("/leaderboard")
async def leaderboard(date: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """当日排行榜（分数降序，同分线索少者靠前）"""
    day = date or daily_service.today_str()
    rows = await db.execute(
        select(DailyScore).where(DailyScore.date == day).order_by(
            desc(DailyScore.score), DailyScore.total_clues
        ).limit(20)
    )
    scores = rows.scalars().all()
    return {
        "date": day,
        "leaderboard": [
            {
                "rank": i + 1,
                "player_name": r.player_name,
                "score": r.score,
                "correct": r.correct,
                "total_clues": r.total_clues,
            }
            for i, r in enumerate(scores)
        ],
    }


@router.get("/today")
async def today(db: AsyncSession = Depends(get_db)):
    """今日概览：题目数 + 榜首（不泄露答案）"""
    day = daily_service.today_str()
    questions = daily_service.get_daily_questions(day)
    rows = await db.execute(
        select(DailyScore).where(DailyScore.date == day).order_by(
            desc(DailyScore.score), DailyScore.total_clues
        ).limit(3)
    )
    top = rows.scalars().all()
    return {
        "date": day,
        "total_questions": len(questions),
        "categories": [q.get("category", "") for q in questions],
        "top3": [{"player_name": r.player_name, "score": r.score} for r in top],
    }
