"""排行榜 + 好友挑战 API"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import GameSession, Question

router = APIRouter()

# 内存排行榜（MVP阶段，后续可换Redis）
leaderboard = {}  # {player_name: {"score": int, "games": int, "wins": int}}
challenges = {}   # {challenge_id: ChallengeState}


class ChallengeCreate(BaseModel):
    player_name: str = "无名者"


class ChallengeSubmit(BaseModel):
    answer: str


@router.get("/leaderboard")
async def get_leaderboard():
    """获取排行榜"""
    sorted_lb = sorted(leaderboard.items(), key=lambda x: x[1]["score"], reverse=True)
    return {
        "ranking": [
            {
                "rank": i + 1,
                "name": name,
                "score": data["score"],
                "games": data["games"],
                "wins": data["wins"],
            }
            for i, (name, data) in enumerate(sorted_lb[:50])
        ]
    }


@router.post("/leaderboard/update")
async def update_leaderboard(name: str, score: int, won: bool = False):
    """更新排行榜（内部调用）"""
    if name not in leaderboard:
        leaderboard[name] = {"score": 0, "games": 0, "wins": 0}
    leaderboard[name]["score"] += score
    leaderboard[name]["games"] += 1
    if won:
        leaderboard[name]["wins"] += 1
    return {"ok": True}


@router.post("/challenge/create")
async def create_challenge(req: ChallengeCreate):
    """创建好友挑战"""
    # 随机选题
    from app.database import async_session
    async with async_session() as db:
        q = await db.execute(select(Question).order_by(func.random()).limit(1))
        question = q.scalar_one_or_none()

    if not question:
        raise HTTPException(status_code=404, detail="题库为空")

    challenge_id = str(uuid.uuid4())[:8].upper()
    clues = question.progressive_clues or []

    challenges[challenge_id] = {
        "id": challenge_id,
        "creator": req.player_name,
        "question_id": question.id,
        "question_name": question.name,
        "aliases": question.aliases or [],
        "clues": clues,
        "clue_index": 0,
        "status": "waiting",  # waiting | playing | done
        "result": None,
    }

    return {
        "challenge_id": challenge_id,
        "share_code": challenge_id,
        "first_clue": clues[0] if clues else "",
        "total_clues": len(clues),
    }


@router.get("/challenge/{challenge_id}")
async def get_challenge(challenge_id: str):
    """获取挑战信息"""
    ch = challenges.get(challenge_id.upper())
    if not ch:
        raise HTTPException(status_code=404, detail="挑战不存在或已过期")

    return {
        "challenge_id": ch["id"],
        "creator": ch["creator"],
        "status": ch["status"],
        "first_clue": ch["clues"][0] if ch["clues"] else "",
        "total_clues": len(ch["clues"]),
    }


@router.post("/challenge/{challenge_id}/guess")
async def challenge_guess(challenge_id: str, req: ChallengeSubmit):
    """提交挑战答案"""
    ch = challenges.get(challenge_id.upper())
    if not ch:
        raise HTTPException(status_code=404, detail="挑战不存在")

    if ch["status"] == "done":
        raise HTTPException(status_code=400, detail="挑战已结束")

    ch["status"] = "playing"

    from app.services.validator import validate_answer
    result = validate_answer(req.answer, ch["question_name"], ch["aliases"])

    if result["correct"]:
        multiplier = [8, 7, 6, 5, 4, 3, 2, 1]
        m = multiplier[min(ch["clue_index"], 7)]
        score = 100 * m
        ch["status"] = "done"
        ch["result"] = {"correct": True, "score": score, "clue_index": ch["clue_index"]}
        return {
            "correct": True,
            "answer": ch["question_name"],
            "score": score,
            "clue_index": ch["clue_index"],
        }
    else:
        # 推进线索
        if ch["clue_index"] < len(ch["clues"]) - 1:
            ch["clue_index"] += 1
            return {
                "correct": False,
                "next_clue": ch["clues"][ch["clue_index"]],
                "clue_index": ch["clue_index"],
            }
        else:
            ch["status"] = "done"
            ch["result"] = {"correct": False, "score": 50}
            return {
                "correct": False,
                "answer": ch["question_name"],
                "score": 50,
                "game_over": True,
            }
