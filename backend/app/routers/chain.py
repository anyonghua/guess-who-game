"""描述接龙模式 API"""

import uuid
import random
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Question, GameSession
from app.services.validator import validate_answer
from app.services.scoring import calculate_score

router = APIRouter()

MAX_KEYWORDS = 7
INITIAL_KEYWORDS = 3


class GuessRequest(BaseModel):
    answer: str


def filter_keywords(keywords: list[list[str]], name: str, aliases: list[str]) -> list[list[str]]:
    """过滤掉包含答案名字的关键词组"""
    name_chars = set(name)
    alias_chars = set()
    for a in aliases:
        alias_chars.update(a)

    forbidden = name_chars | alias_chars | {"人", "者", "他", "她"}

    filtered = []
    for group in keywords:
        clean_group = []
        for kw in group:
            # 如果关键词包含名字的字，跳过
            kw_chars = set(kw)
            if kw_chars & forbidden and len(kw_chars & forbidden) >= 2:
                continue
            clean_group.append(kw)
        if clean_group:
            filtered.append(clean_group)

    return filtered


# === API 路由 ===

@router.post("/start")
async def start_chain(db: AsyncSession = Depends(get_db)):
    """开始一局描述接龙"""
    query = (
        select(Question)
        .where(Question.description_keywords != [])
        .order_by(func.random())
        .limit(1)
    )
    result = await db.execute(query)
    question = result.scalar_one_or_none()

    if not question:
        raise HTTPException(status_code=404, detail="题库为空")

    # 过滤关键词
    all_keywords = question.description_keywords or []
    filtered = filter_keywords(all_keywords, question.name, question.aliases or [])

    if not filtered:
        # 如果过滤后没有关键词，用emoji描述
        filtered = [[e] for e in (question.emoji_description or ["未知"])]

    # 取前3组关键词
    initial_groups = filtered[:INITIAL_KEYWORDS]
    remaining_groups = filtered[INITIAL_KEYWORDS:]

    # 展平为关键词列表
    initial_keywords = []
    for group in initial_groups:
        initial_keywords.extend(group)

    session = GameSession(
        id=str(uuid.uuid4()),
        mode="chain",
        question_id=question.id,
        conversation=[],
    )
    db.add(session)
    await db.commit()

    return {
        "session_id": session.id,
        "keywords": initial_keywords,
        "keyword_count": len(initial_keywords),
        "max_keywords": MAX_KEYWORDS,
        "remaining_hints": len(remaining_groups),
    }


@router.post("/{session_id}/guess")
async def chain_guess(session_id: str, req: GuessRequest, db: AsyncSession = Depends(get_db)):
    """描述接龙模式下提交猜测"""
    session = await _get_session(session_id, db)
    if session.is_completed:
        raise HTTPException(status_code=400, detail="游戏已结束")

    question = await db.get(Question, session.question_id)
    conversation = session.conversation or []

    # 验证答案
    result = validate_answer(req.answer, question.name, question.aliases or [])

    if result["correct"]:
        # 计算用了几个关键词
        keyword_count = conversation[-1]["keyword_count"] if conversation else INITIAL_KEYWORDS
        # 计分
        efficiency = (MAX_KEYWORDS - keyword_count + 1) / MAX_KEYWORDS
        score = int(100 * 8 * efficiency * 1.5)
        stars = _get_stars(keyword_count)

        session.is_completed = True
        session.is_correct = True
        session.score = score
        await db.commit()

        return {
            "correct": True,
            "match_type": result["match_type"],
            "message": f"✦ 命运已定：{question.name}",
            "score": score,
            "stars": stars,
            "keyword_count": keyword_count,
        }
    else:
        # 猜错，追加关键词
        all_keywords = question.description_keywords or []
        filtered = filter_keywords(all_keywords, question.name, question.aliases or [])

        # 计算当前已有的关键词数
        current_count = conversation[-1]["keyword_count"] if conversation else INITIAL_KEYWORDS

        if current_count >= MAX_KEYWORDS or len(filtered) <= current_count:
            # 线索用完，游戏结束
            session.is_completed = True
            session.is_correct = False
            session.score = 50
            await db.commit()

            return {
                "correct": False,
                "match_type": result["match_type"],
                "message": "线索已用尽，答案揭晓",
                "actual_answer": question.name,
                "score": 50,
                "keyword_count": current_count,
                "game_over": True,
            }

        # 追加一个关键词
        next_group_idx = current_count  # 下一个要展示的组索引
        if next_group_idx < len(filtered):
            new_keyword = random.choice(filtered[next_group_idx])
        else:
            new_keyword = "..."

        new_count = current_count + 1

        conversation.append({
            "role": "guess",
            "content": req.answer,
            "correct": False,
        })
        conversation.append({
            "role": "system",
            "content": f"追加关键词: {new_keyword}",
            "keyword_count": new_count,
        })
        session.conversation = conversation
        await db.commit()

        # 收集所有已展示的关键词
        all_shown = _collect_shown_keywords(filtered, new_count)

        return {
            "correct": False,
            "match_type": result["match_type"],
            "message": f"不对！新线索：{new_keyword}",
            "new_keyword": new_keyword,
            "keywords": all_shown,
            "keyword_count": new_count,
            "remaining_hints": max(0, len(filtered) - new_count),
        }


@router.post("/{session_id}/hint")
async def chain_hint(session_id: str, db: AsyncSession = Depends(get_db)):
    """请求追加关键词（不猜，直接要线索）"""
    session = await _get_session(session_id, db)
    if session.is_completed:
        raise HTTPException(status_code=400, detail="游戏已结束")

    question = await db.get(Question, session.question_id)
    conversation = session.conversation or []

    all_keywords = question.description_keywords or []
    filtered = filter_keywords(all_keywords, question.name, question.aliases or [])

    current_count = conversation[-1]["keyword_count"] if conversation else INITIAL_KEYWORDS

    if current_count >= MAX_KEYWORDS or len(filtered) <= current_count:
        raise HTTPException(status_code=400, detail="已无更多线索")

    next_group_idx = current_count
    if next_group_idx < len(filtered):
        new_keyword = random.choice(filtered[next_group_idx])
    else:
        raise HTTPException(status_code=400, detail="已无更多线索")

    new_count = current_count + 1

    conversation.append({
        "role": "hint",
        "content": f"追加关键词: {new_keyword}",
        "keyword_count": new_count,
    })
    session.conversation = conversation
    await db.commit()

    all_shown = _collect_shown_keywords(filtered, new_count)

    return {
        "new_keyword": new_keyword,
        "keywords": all_shown,
        "keyword_count": new_count,
        "remaining_hints": max(0, len(filtered) - new_count),
    }


@router.get("/{session_id}/result")
async def chain_result(session_id: str, db: AsyncSession = Depends(get_db)):
    """获取结果"""
    session = await _get_session(session_id, db)
    question = await db.get(Question, session.question_id)
    conversation = session.conversation or []
    keyword_count = conversation[-1]["keyword_count"] if conversation else INITIAL_KEYWORDS

    return {
        "session_id": session_id,
        "correct": session.is_correct,
        "answer": question.name,
        "score": session.score,
        "keyword_count": keyword_count,
        "stars": _get_stars(keyword_count) if session.is_correct else 1,
    }


def _collect_shown_keywords(filtered: list[list[str]], count: int) -> list[str]:
    """收集前 count 组关键词，展平"""
    shown = []
    for i in range(min(count, len(filtered))):
        shown.extend(filtered[i])
    return shown


def _get_stars(keyword_count: int) -> int:
    if keyword_count <= 3: return 5
    if keyword_count <= 4: return 4
    if keyword_count <= 5: return 3
    if keyword_count <= 6: return 2
    return 1


async def _get_session(session_id: str, db: AsyncSession) -> GameSession:
    session = await db.get(GameSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="游戏会话不存在")
    return session
