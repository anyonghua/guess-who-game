"""动态出题 API

- POST /api/generator/start          开一局变体出题（关键词拼图，每次组合不同）
- GET  /api/generator/{sid}/clue     再揭一条线索
- POST /api/generator/{sid}/guess    提交猜测
- GET  /api/generator/config         出题引擎配置状态（LLM 是否可用）

LLM 批量入库走 CLI：backend/scripts/generate_questions.py（不开放公网接口防滥用）
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import generator_service

router = APIRouter()


class GuessRequest(BaseModel):
    answer: str


@router.post("/start")
async def start_variant():
    """开始一局变体出题"""
    return generator_service.start_variant()


@router.get("/config")
async def config():
    return {"llm_configured": generator_service.llm_configured()}


@router.get("/{session_id}/clue")
async def get_clue(session_id: str):
    try:
        return generator_service.reveal_clue(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="对局不存在或已过期")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/guess")
async def guess(session_id: str, req: GuessRequest):
    try:
        return generator_service.guess(session_id, req.answer)
    except KeyError:
        raise HTTPException(status_code=404, detail="对局不存在或已过期")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
