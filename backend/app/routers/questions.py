"""题库管理路由"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class QuestionCreate(BaseModel):
    name: str
    aliases: list[str]
    category: str
    difficulty: int  # 1-5
    progressive_clues: list[str]
    description_keywords: list[list[str]]

class QuestionQuery(BaseModel):
    category: Optional[str] = None
    difficulty_min: int = 1
    difficulty_max: int = 5
    limit: int = 10


@router.get("/stats")
async def question_stats():
    """题库统计"""
    return {
        "total": 0,
        "by_category": {
            "历史人物": 0,
            "影视明星": 0,
            "音乐人": 0,
            "体育明星": 0,
            "科学家": 0,
            "虚构角色": 0,
        },
        "by_difficulty": {
            "1": 0, "2": 0, "3": 0, "4": 0, "5": 0
        }
    }

@router.post("/search")
async def search_questions(req: QuestionQuery):
    """搜索题库"""
    return {"questions": [], "total": 0}

@router.post("/create")
async def create_question(req: QuestionCreate):
    """添加新题目（管理员）"""
    return {
        "id": "q_001",
        "name": req.name,
        "message": "题目创建成功"
    }

@router.post("/generate")
async def ai_generate_question(category: str, difficulty: int = 3):
    """AI 自动生成新题目"""
    # TODO: 调用 LLM 生成线索和关键词
    return {
        "name": "???",
        "message": "AI 出题功能开发中...",
        "status": "coming_soon"
    }
