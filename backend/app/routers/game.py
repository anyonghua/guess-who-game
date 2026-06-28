"""游戏核心路由 - 渐进揭秘、二十问、描述接龙"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


# === 数据模型 ===

class GameStartRequest(BaseModel):
    mode: str  # progressive | twenty_q | description_chain
    difficulty: str = "normal"  # easy | normal | hard | hell
    category: Optional[str] = None  # 历史人物 | 影视明星 | etc.

class GuessRequest(BaseModel):
    session_id: str
    answer: str

class QuestionRequest(BaseModel):
    session_id: str
    question: str

class ClueRequest(BaseModel):
    session_id: str  # 描述接龙中请求更多线索


# === 渐进揭秘 ===

@router.post("/progressive/start")
async def start_progressive_game(req: GameStartRequest):
    """开始一局渐进揭秘游戏"""
    # TODO: 从题库选题，生成线索序列
    return {
        "session_id": "demo_session_001",
        "mode": "progressive",
        "difficulty": req.difficulty,
        "total_clues": 8,
        "first_clue": "这是一位中国古代的政治家",
        "message": "游戏开始！根据线索猜猜TA是谁？"
    }

@router.post("/progressive/guess")
async def progressive_guess(req: GuessRequest):
    """渐进揭秘模式下提交猜测"""
    # TODO: 验证答案，计算得分
    return {
        "correct": False,
        "message": "不对哦～再想想！",
        "temperature": "warm",  # cold | cool | warm | hot | boiling
        "current_score": 150,
        "next_clue": "他活跃在东汉末年到三国时期"
    }


# === 二十问 ===

@router.post("/twenty-q/start")
async def start_twenty_q_game(req: GameStartRequest):
    """开始一局二十问游戏"""
    # TODO: AI选定一个人物
    return {
        "session_id": "demo_session_002",
        "mode": "twenty_q",
        "remaining_questions": 20,
        "message": "我已经想好一个人了！来问吧，只能问是/否问题。"
    }

@router.post("/twenty-q/ask")
async def twenty_q_ask(req: QuestionRequest):
    """二十问模式下提问"""
    # TODO: AI分析问题并回答
    return {
        "answer": "不是哦，但他和中国渊源不浅。",
        "remaining_questions": 19,
        "hint_level": "direction_hint"  # none | direction_hint | warm_encouragement
    }

@router.post("/twenty-q/final-guess")
async def twenty_q_final_guess(req: GuessRequest):
    """二十问模式下提交最终猜测"""
    # TODO: 验证答案
    return {
        "correct": True,
        "actual_answer": "诸葛亮",
        "remaining_questions": 15,
        "score": 500,
        "rating": "⭐⭐⭐⭐⭐"
    }


# === 描述接龙 ===

@router.post("/chain/start")
async def start_chain_game(req: GameStartRequest):
    """开始一局描述接龙游戏"""
    # TODO: 选题并生成初始关键词
    return {
        "session_id": "demo_session_003",
        "mode": "description_chain",
        "keywords": ["羽扇", "纶巾", "三国"],
        "max_keywords": 7,
        "current_keyword_count": 3,
        "message": "根据这3个关键词，猜猜TA是谁？"
    }

@router.post("/chain/guess")
async def chain_guess(req: GuessRequest):
    """描述接龙模式下提交猜测"""
    # TODO: 验证答案
    return {
        "correct": False,
        "message": "不对哦！给你追加一个关键词～",
        "new_keyword": "出师表",
        "current_keyword_count": 4,
        "keywords_so_far": ["羽扇", "纶巾", "三国", "出师表"]
    }

@router.post("/chain/hint")
async def chain_hint(req: ClueRequest):
    """请求追加关键词（不猜，直接要线索）"""
    # TODO: 生成新的关键词
    return {
        "new_keyword": "草船借箭",
        "current_keyword_count": 5,
        "keywords_so_far": ["羽扇", "纶巾", "三国", "出师表", "草船借箭"]
    }
