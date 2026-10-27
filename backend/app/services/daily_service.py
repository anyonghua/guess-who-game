"""每日挑战服务

设计（2026-10-27）：
- 每日 3 题，按日期确定性抽题（seed = "daily-" + 日期）→ 全球玩家同题
- 难度分层：简单(1-2) / 中等(3) / 困难(4-5) 各一题
- 对局状态存内存 dict（进程内有效，重启即失——与 battle 对局一致的取舍）
- 成绩持久化到 daily_scores 表，支持当日排行
- 题库直接读 data/questions_bank.json（确定性、不依赖数据库种子）
"""

import json
import random
import uuid
from datetime import date as date_cls
from pathlib import Path
from typing import Optional

from app.services.validator import validate_answer
from app.services.scoring import calculate_score

_BANK_PATH = Path(__file__).resolve().parents[2] / "data" / "questions_bank.json"
_bank_cache: Optional[list] = None

# 每日题数
DAILY_SIZE = 3

# 对局状态（内存）
SESSIONS: dict = {}


def load_bank() -> list:
    global _bank_cache
    if _bank_cache is None:
        with open(_BANK_PATH, encoding="utf-8") as f:
            _bank_cache = json.load(f)
    return _bank_cache or []


def today_str() -> str:
    return date_cls.today().isoformat()


def get_daily_questions(day: Optional[str] = None) -> list:
    """按日期确定性抽 3 题（简单/中等/困难各一）。day 格式 YYYY-MM-DD。"""
    day = day or today_str()
    bank = load_bank()
    rng = random.Random("daily-" + day)

    easy = [q for q in bank if q.get("difficulty", 3) <= 2]
    medium = [q for q in bank if q.get("difficulty", 3) == 3]
    hard = [q for q in bank if q.get("difficulty", 3) >= 4]

    picked = []
    for bucket in (easy, medium, hard):
        pool = bucket or bank
        picked.append(rng.choice(pool))
    # 去重（极端情况桶重叠时从 bank 补）
    seen = {id(q) for q in picked}
    i = 0
    while len(picked) < DAILY_SIZE and i < len(bank):
        q = rng.choice(bank)
        if id(q) not in seen:
            picked.append(q)
            seen.add(id(q))
        i += 1
    return picked


def _diff_key(q: dict) -> str:
    d = q.get("difficulty", 3)
    if d <= 2:
        return "easy"
    if d == 3:
        return "normal"
    if d == 4:
        return "hard"
    return "hell"


def start_session(player_name: str = "匿名玩家", day: Optional[str] = None) -> dict:
    """开一局每日挑战"""
    day = day or today_str()
    questions = get_daily_questions(day)
    sid = str(uuid.uuid4())
    SESSIONS[sid] = {
        "session_id": sid,
        "date": day,
        "player_name": player_name or "匿名玩家",
        "questions": questions,
        "q_index": 0,
        "clue_index": 0,
        "wrong_guesses": 0,
        "results": [],      # [{name, correct, clues_used, score}]
        "finished": False,
    }
    first = questions[0]
    return {
        "session_id": sid,
        "date": day,
        "question_index": 0,
        "total_questions": len(questions),
        "clue": first["progressive_clues"][0],
        "clue_index": 0,
        "total_clues": len(first["progressive_clues"]),
        "category": first.get("category", ""),
        "difficulty": first.get("difficulty", 3),
    }


def _current(session: dict) -> dict:
    return session["questions"][session["q_index"]]


def get_clue(sid: str) -> dict:
    """再揭一条线索（不猜直接看线索 = 消耗一次机会）"""
    s = SESSIONS.get(sid)
    if not s:
        raise KeyError("session not found")
    if s["finished"]:
        raise ValueError("session finished")
    q = _current(s)
    if s["clue_index"] < len(q["progressive_clues"]) - 1:
        s["clue_index"] += 1
    return {
        "session_id": sid,
        "question_index": s["q_index"],
        "clue": q["progressive_clues"][s["clue_index"]],
        "clue_index": s["clue_index"],
        "total_clues": len(q["progressive_clues"]),
    }


def submit_guess(sid: str, answer: str) -> dict:
    """提交猜测。对：进下一题；错：曝光下一条线索，线索耗尽则判负进下一题。"""
    s = SESSIONS.get(sid)
    if not s:
        raise KeyError("session not found")
    if s["finished"]:
        raise ValueError("session finished")

    q = _current(s)
    result = validate_answer(answer, q["name"], q.get("aliases", []))

    if result["correct"]:
        sc = calculate_score(s["clue_index"], _diff_key(q), streak=len([r for r in s["results"] if r["correct"]]), first_guess=s["wrong_guesses"] == 0)
        s["results"].append({
            "name": q["name"],
            "correct": True,
            "clues_used": s["clue_index"] + 1,
            "score": sc["score"],
            "stars": sc["stars"],
        })
        advanced = self_advance(s)
        return {
            "correct": True,
            "match_type": result["match_type"],
            "points": sc["score"],
            "answer": q["name"],
            "advanced": advanced,
            **_progress(s),
        }

    # 猜错
    s["wrong_guesses"] += 1
    clues = q["progressive_clues"]
    if s["clue_index"] < len(clues) - 1:
        s["clue_index"] += 1
        return {
            "correct": False,
            "match_type": result["match_type"],
            "points": 0,
            "revealed_clue": clues[s["clue_index"]],
            "advanced": False,
            **_progress(s),
        }

    # 线索耗尽仍未猜对 → 判负，进下一题
    s["results"].append({
        "name": q["name"],
        "correct": False,
        "clues_used": len(clues),
        "score": 0,
        "stars": 0,
    })
    advanced = self_advance(s)
    return {
        "correct": False,
        "match_type": result["match_type"],
        "points": 0,
        "answer": q["name"],
        "advanced": advanced,
        **_progress(s),
    }


def self_advance(s: dict) -> bool:
    """推进到下一题；全部答完则结束。返回是否还有下一题。"""
    s["q_index"] += 1
    s["clue_index"] = 0
    s["wrong_guesses"] = 0
    if s["q_index"] >= len(s["questions"]):
        s["q_index"] = len(s["questions"]) - 1
        s["finished"] = True
        return False
    return True


def _progress(s: dict) -> dict:
    out = {
        "session_id": s["session_id"],
        "question_index": s["q_index"],
        "finished": s["finished"],
        "answered": len(s["results"]),
    }
    if not s["finished"]:
        q = _current(s)
        out.update({
            "clue": q["progressive_clues"][s["clue_index"]],
            "clue_index": s["clue_index"],
            "total_clues": len(q["progressive_clues"]),
            "category": q.get("category", ""),
        })
    return out


def finish_session(sid: str) -> dict:
    """结算：汇总成绩（幂等，重复调用返回同一结果）"""
    s = SESSIONS.get(sid)
    if not s:
        raise KeyError("session not found")
    total = sum(r["score"] for r in s["results"])
    correct = sum(1 for r in s["results"] if r["correct"])
    clues_used = sum(r["clues_used"] for r in s["results"])
    return {
        "session_id": sid,
        "date": s["date"],
        "player_name": s["player_name"],
        "total_score": total,
        "correct": correct,
        "total_questions": len(s["questions"]),
        "total_clues": clues_used,
        "results": s["results"],
        "finished": s["finished"],
    }
