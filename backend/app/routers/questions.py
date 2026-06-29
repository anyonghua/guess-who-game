"""题库管理 API"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Question

router = APIRouter()


class QuestionCreate(BaseModel):
    name: str
    aliases: list[str] = []
    category: str
    subcategory: Optional[str] = None
    difficulty: int = 3
    progressive_clues: list[str]
    twenty_q_meta: dict = {}
    description_keywords: list[list[str]] = []
    emoji_description: list[str] = []


class QuestionBatch(BaseModel):
    questions: list[QuestionCreate]


@router.get("/stats")
async def question_stats(db: AsyncSession = Depends(get_db)):
    """题库统计"""
    total = await db.scalar(select(func.count(Question.id)))
    cats = await db.execute(
        select(Question.category, func.count(Question.id))
        .group_by(Question.category)
    )
    return {
        "total": total or 0,
        "by_category": {row[0]: row[1] for row in cats.fetchall()},
    }


@router.post("/create")
async def create_question(req: QuestionCreate, db: AsyncSession = Depends(get_db)):
    """添加单道题目"""
    q = Question(
        name=req.name,
        aliases=req.aliases,
        category=req.category,
        subcategory=req.subcategory,
        difficulty=req.difficulty,
        progressive_clues=req.progressive_clues,
        twenty_q_meta=req.twenty_q_meta,
        description_keywords=req.description_keywords,
        emoji_description=req.emoji_description,
    )
    db.add(q)
    await db.commit()
    return {"id": q.id, "name": q.name, "message": "题目创建成功"}


@router.post("/batch")
async def batch_create(req: QuestionBatch, db: AsyncSession = Depends(get_db)):
    """批量导入题目"""
    created = 0
    skipped = 0
    for item in req.questions:
        # 检查是否已存在
        exists = await db.scalar(
            select(Question.id).where(Question.name == item.name)
        )
        if exists:
            skipped += 1
            continue

        q = Question(
            name=item.name,
            aliases=item.aliases,
            category=item.category,
            subcategory=item.subcategory,
            difficulty=item.difficulty,
            progressive_clues=item.progressive_clues,
            twenty_q_meta=item.twenty_q_meta,
            description_keywords=item.description_keywords,
            emoji_description=item.emoji_description,
        )
        db.add(q)
        created += 1

    await db.commit()
    return {"created": created, "skipped": skipped, "total": created + skipped}
