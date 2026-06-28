"""对战服务路由 - 实时对战、好友挑战"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class MatchRequest(BaseModel):
    mode: str  # speed | quiz_each_other | chemistry
    difficulty: str = "normal"

class ChallengeRequest(BaseModel):
    target_user_id: str
    mode: str = "speed"

class AnswerRequest(BaseModel):
    room_id: str
    answer: str


@router.post("/match")
async def find_match(req: MatchRequest):
    """匹配对手"""
    # TODO: 匹配系统
    return {
        "status": "searching",
        "mode": req.mode,
        "message": "正在为你匹配对手..."
    }

@router.post("/challenge/create")
async def create_challenge(req: ChallengeRequest):
    """创建好友挑战"""
    # TODO: 生成挑战码
    return {
        "challenge_id": "challenge_001",
        "share_code": "ABC123",
        "share_link": "https://guesswho.game/c/ABC123",
        "message": "挑战已创建，分享给好友吧！"
    }

@router.get("/challenge/{challenge_id}")
async def get_challenge(challenge_id: str):
    """获取挑战详情"""
    # TODO: 从数据库读取挑战信息
    return {
        "challenge_id": challenge_id,
        "creator": "玩家A",
        "mode": "speed",
        "status": "waiting",
        "questions": []
    }

@router.post("/challenge/{challenge_id}/answer")
async def submit_challenge_answer(challenge_id: str, req: AnswerRequest):
    """提交挑战答案"""
    # TODO: 记录答案并计算分数
    return {
        "correct": True,
        "score": 250,
        "time_taken": 5.2,
        "message": "回答正确！"
    }

@router.get("/challenge/{challenge_id}/result")
async def get_challenge_result(challenge_id: str):
    """获取挑战对比结果"""
    # TODO: 对比双方成绩
    return {
        "player_a": {"name": "玩家A", "score": 1200, "accuracy": 0.8},
        "player_b": {"name": "玩家B", "score": 950, "accuracy": 0.6},
        "winner": "玩家A",
        "verdict": "玩家A 知识面更广！"
    }
