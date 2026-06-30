"""用户系统 + 经济系统 API

MVP方案：UUID标识用户（localStorage持久化），无需真实登录
"""

import uuid
import time
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Player

router = APIRouter()

# === 配置 ===
STAMINA_MAX = 30
STAMINA_REGEN_INTERVAL = 300  # 5分钟恢复1点
STAMINA_COST_PER_GAME = 1

# 等级经验表
LEVEL_TABLE = [0, 100, 300, 600, 1000, 1500, 2200, 3000, 4000, 5200,
               6500, 8000, 10000, 12500, 15500, 19000, 23000, 27500, 33000, 40000]

# 道具定义
ITEMS = {
    "hint_card": {"name": "提示卡", "desc": "获得一条额外线索", "price": 50, "icon": "🔍"},
    "skip_card": {"name": "跳过卡", "desc": "跳过当前题目不扣分", "price": 80, "icon": "⏭"},
    "time_card": {"name": "延时卡", "desc": "对战中额外+15秒", "price": 60, "icon": "⏱"},
    "shield_card": {"name": "护盾卡", "desc": "对战中保护一次不扣分", "price": 100, "icon": "🛡"},
    "reveal_card": {"name": "透视卡", "desc": "显示人物的分类", "price": 120, "icon": "👁"},
}

# 成就定义
ACHIEVEMENTS = {
    "first_blood": {"name": "初次猜中", "desc": "第一次猜对人名", "icon": "🎯", "xp": 50},
    "streak_3": {"name": "三连胜", "desc": "连续猜对3个", "icon": "🔥", "xp": 100},
    "streak_5": {"name": "五连胜", "desc": "连续猜对5个", "icon": "🔥🔥", "xp": 200},
    "streak_10": {"name": "十连胜", "desc": "连续猜对10个", "icon": "🔥🔥🔥", "xp": 500},
    "speed_demon": {"name": "闪电之速", "desc": "第1条线索就猜对", "icon": "⚡", "xp": 150},
    "twenty_q_master": {"name": "二十问大师", "desc": "用5个问题以内猜对", "icon": "🧠", "xp": 300},
    "chain_master": {"name": "关键词大师", "desc": "仅用3个关键词猜对", "icon": "🗝", "xp": 200},
    "battle_winner": {"name": "对战之王", "desc": "赢得一场对战", "icon": "⚔", "xp": 200},
    "scholar": {"name": "博学者", "desc": "猜对50道题", "icon": "📚", "xp": 500},
    "legend": {"name": "传说", "desc": "达到10级", "icon": "👑", "xp": 1000},
    "all_modes": {"name": "全能玩家", "desc": "三种模式各玩一次", "icon": "🎭", "xp": 300},
    "perfect_game": {"name": "完美一局", "desc": "渐进揭秘第1条线索猜对", "icon": "✦", "xp": 250},
}


# === 请求模型 ===

class CreateUserRequest(BaseModel):
    nickname: str = "无名者"

class UpdateProfileRequest(BaseModel):
    nickname: Optional[str] = None

class AddXpRequest(BaseModel):
    amount: int
    reason: str = ""

class PurchaseRequest(BaseModel):
    item_id: str
    quantity: int = 1


# === 辅助函数 ===

def get_level(xp: int) -> int:
    for i, threshold in enumerate(LEVEL_TABLE):
        if xp < threshold:
            return i
    return len(LEVEL_TABLE)

def get_xp_for_next_level(level: int) -> int:
    if level >= len(LEVEL_TABLE):
        return LEVEL_TABLE[-1]
    return LEVEL_TABLE[level]

def calc_stamina(current_stamina: int, last_regen: float) -> int:
    now = time.time()
    elapsed = now - last_regen
    regen_count = int(elapsed / STAMINA_REGEN_INTERVAL)
    return min(STAMINA_MAX, current_stamina + regen_count)


# === API 路由 ===

@router.post("/create")
async def create_player(req: CreateUserRequest, db: AsyncSession = Depends(get_db)):
    """创建/获取玩家"""
    player_id = str(uuid.uuid4())
    player = Player(
        id=player_id,
        nickname=req.nickname,
        level=1,
        experience=0,
        total_score=0,
        games_played=0,
        games_won=0,
        best_streak=0,
    )
    # 扩展字段（暂存JSON）
    player._stamina = STAMINA_MAX
    player._last_regen = time.time()
    player._coins = 200  # 新手赠送200金币
    player._items = {}
    player._achievements = []

    db.add(player)
    await db.commit()

    return {
        "player_id": player_id,
        "nickname": req.nickname,
        "level": 1,
        "experience": 0,
        "stamina": STAMINA_MAX,
        "coins": 200,
        "items": {},
        "achievements": [],
    }


@router.get("/{player_id}")
async def get_player(player_id: str, db: AsyncSession = Depends(get_db)):
    """获取玩家信息"""
    player = await db.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="玩家不存在")

    level = get_level(player.experience or 0)
    xp_current = player.experience or 0
    xp_next = get_xp_for_next_level(level)

    return {
        "player_id": player.id,
        "nickname": player.nickname,
        "level": level,
        "experience": xp_current,
        "xp_for_next": xp_next,
        "xp_progress": (xp_current - (LEVEL_TABLE[level - 1] if level > 0 else 0)) / max(1, xp_next - (LEVEL_TABLE[level - 1] if level > 0 else 0)),
        "total_score": player.total_score or 0,
        "games_played": player.games_played or 0,
        "games_won": player.games_won or 0,
        "win_rate": round((player.games_won or 0) / max(1, player.games_played or 0) * 100, 1),
        "best_streak": player.best_streak or 0,
        "stamina": STAMINA_MAX,  # MVP简化
        "coins": 200,  # MVP简化
        "achievements": [],
    }


@router.post("/{player_id}/xp")
async def add_xp(player_id: str, req: AddXpRequest, db: AsyncSession = Depends(get_db)):
    """添加经验值"""
    player = await db.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="玩家不存在")

    old_level = get_level(player.experience or 0)
    player.experience = (player.experience or 0) + req.amount
    new_level = get_level(player.experience or 0)
    level_up = new_level > old_level

    await db.commit()

    return {
        "xp_added": req.amount,
        "total_xp": player.experience,
        "level": new_level,
        "level_up": level_up,
        "reason": req.reason,
    }


@router.post("/{player_id}/game-result")
async def record_game(player_id: str, score: int, won: bool = False, db: AsyncSession = Depends(get_db)):
    """记录一局游戏结果"""
    player = await db.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="玩家不存在")

    player.games_played = (player.games_played or 0) + 1
    player.total_score = (player.total_score or 0) + score
    if won:
        player.games_won = (player.games_won or 0) + 1

    # XP奖励
    xp_earned = max(10, score // 10)
    old_level = get_level(player.experience or 0)
    player.experience = (player.experience or 0) + xp_earned
    new_level = get_level(player.experience or 0)

    # 金币奖励
    coins_earned = max(5, score // 20)

    await db.commit()

    return {
        "xp_earned": xp_earned,
        "coins_earned": coins_earned,
        "total_xp": player.experience,
        "level": new_level,
        "level_up": new_level > old_level,
        "games_played": player.games_played,
    }


@router.get("/items/list")
async def list_items():
    """获取道具列表"""
    return {"items": ITEMS}


@router.get("/achievements/list")
async def list_achievements():
    """获取成就列表"""
    return {"achievements": ACHIEVEMENTS}


@router.get("/levels")
async def get_level_table():
    """获取等级经验表"""
    return {
        "levels": [
            {"level": i, "xp_required": xp}
            for i, xp in enumerate(LEVEL_TABLE)
        ]
    }
