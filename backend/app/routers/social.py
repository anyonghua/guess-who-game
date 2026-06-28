"""社交服务路由 - 好友、排行榜、俱乐部"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


@router.get("/ranking/daily")
async def daily_ranking():
    """每日排行榜"""
    # TODO: 从 Redis Sorted Set 获取
    return {
        "ranking": [
            {"rank": 1, "name": "猜神", "score": 5200, "streak": 15},
            {"rank": 2, "name": "百科全书", "score": 4800, "streak": 12},
            {"rank": 3, "name": "线索猎人", "score": 4500, "streak": 10},
        ],
        "my_rank": 42,
        "my_score": 1200
    }

@router.get("/ranking/weekly")
async def weekly_ranking():
    """每周排行榜"""
    return {"ranking": [], "my_rank": 0}

@router.get("/friends")
async def get_friends():
    """获取好友列表"""
    return {"friends": [], "count": 0}

@router.get("/achievements")
async def get_achievements():
    """获取成就列表"""
    return {
        "achievements": [
            {"id": "first_blood", "name": "初次猜中", "desc": "第一次猜对人名", "unlocked": True},
            {"id": "streak_5", "name": "五连胜", "desc": "连续猜对5个", "unlocked": False},
            {"id": "speed_demon", "name": "闪电之速", "desc": "3秒内猜对", "unlocked": False},
        ],
        "total_unlocked": 1,
        "total_count": 3
    }

@router.get("/share-card/{session_id}")
async def generate_share_card(session_id: str):
    """生成战绩分享卡"""
    # TODO: 生成图片
    return {
        "session_id": session_id,
        "card_url": f"/static/cards/{session_id}.png",
        "message": "战绩卡已生成！"
    }
