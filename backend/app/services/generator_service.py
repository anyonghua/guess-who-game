"""AI 动态出题引擎（2026-10-27）

双路径设计：
1. 程序化变体（默认，零外部依赖）：
   从题库原子数据（category/description_keywords/名字长度）动态组合出
   「关键词拼图」变体题——同一人物每次拼出的线索组合都不同，题库无限可玩。
2. LLM 增强出题（可选插件）：
   配置 GUESSWHO_LLM_BASE_URL / GUESSWHO_LLM_API_KEY / GUESSWHO_LLM_MODEL
   （任意 OpenAI 兼容端点）后，llm_generate() 可为新名人生成完整题库条目，
   含 schema 校验 + 别名去重，供 scripts/generate_questions.py 批量入库。
"""

import json
import os
import random
import uuid
import urllib.request
from pathlib import Path
from typing import Optional

from app.services.validator import validate_answer
from app.services.scoring import calculate_score

_BANK_PATH = Path(__file__).resolve().parents[2] / "data" / "questions_bank.json"
_bank_cache: Optional[list] = None
SESSIONS: dict = {}


def load_bank() -> list:
    global _bank_cache
    if _bank_cache is None:
        with open(_BANK_PATH, encoding="utf-8") as f:
            _bank_cache = json.load(f)
    return _bank_cache or []


# === 程序化变体生成 ===

def make_variant(q: dict, rng: Optional[random.Random] = None) -> dict:
    """把一道题库题重组成「关键词拼图」变体：
    线索顺序 = 类别提示 → 关键词组（乱序）→ 名字长度 → 姓氏提示
    每次调用组合不同 → 同一人物也有新鲜感
    """
    rng = rng or random.Random()
    name = q["name"]
    clues = [f"TA 属于「{q.get('category', '名人')}」"]

    # 关键词组打散（description_keywords: [[组1词...],[组2词...]]）
    groups = []
    for g in q.get("description_keywords", []):
        if isinstance(g, list) and g:
            groups.append("线索词：" + "、".join(str(w) for w in g[:4]))
        elif isinstance(g, str):
            groups.append("线索词：" + g)
    rng.shuffle(groups)
    clues.extend(groups[:4])

    # 结构性提示收尾
    clues.append(f"TA 的名字有 {len(name)} 个字")
    if len(name) >= 2:
        clues.append(f"TA 姓「{name[0]}」")

    return {
        "variant_id": str(uuid.uuid4()),
        "name": name,
        "aliases": q.get("aliases", []),
        "category": q.get("category", ""),
        "difficulty": q.get("difficulty", 3),
        "clues": clues,
    }


# === 变体对局（内存 session，与 daily 同款取舍）===

def start_variant(seed: Optional[str] = None) -> dict:
    bank = load_bank()
    rng = random.Random(seed) if seed else random.Random()
    q = rng.choice(bank)
    v = make_variant(q, rng)
    sid = v["variant_id"]
    SESSIONS[sid] = {
        "session_id": sid,
        "variant": v,
        "clue_index": 0,
        "wrong_guesses": 0,
        "finished": False,
    }
    return {
        "session_id": sid,
        "clue": v["clues"][0],
        "clue_index": 0,
        "total_clues": len(v["clues"]),
        "category": v["category"],
    }


def reveal_clue(sid: str) -> dict:
    s = SESSIONS.get(sid)
    if not s:
        raise KeyError("session not found")
    if s["finished"]:
        raise ValueError("session finished")
    v = s["variant"]
    if s["clue_index"] < len(v["clues"]) - 1:
        s["clue_index"] += 1
    return {
        "session_id": sid,
        "clue": v["clues"][s["clue_index"]],
        "clue_index": s["clue_index"],
        "total_clues": len(v["clues"]),
    }


def guess(sid: str, answer: str) -> dict:
    s = SESSIONS.get(sid)
    if not s:
        raise KeyError("session not found")
    if s["finished"]:
        raise ValueError("session finished")
    v = s["variant"]
    result = validate_answer(answer, v["name"], v["aliases"])

    if result["correct"]:
        sc = calculate_score(s["clue_index"], "normal", streak=0, first_guess=s["wrong_guesses"] == 0)
        s["finished"] = True
        return {
            "correct": True,
            "match_type": result["match_type"],
            "answer": v["name"],
            "points": sc["score"],
            "stars": sc["stars"],
            "finished": True,
        }

    s["wrong_guesses"] += 1
    if s["clue_index"] < len(v["clues"]) - 1:
        s["clue_index"] += 1
        return {
            "correct": False,
            "match_type": result["match_type"],
            "revealed_clue": v["clues"][s["clue_index"]],
            "clue_index": s["clue_index"],
            "total_clues": len(v["clues"]),
            "finished": False,
        }

    s["finished"] = True
    return {
        "correct": False,
        "match_type": result["match_type"],
        "answer": v["name"],
        "points": 0,
        "finished": True,
    }


# === LLM 增强出题（可选插件）===

LLM_BASE_URL = os.getenv("GUESSWHO_LLM_BASE_URL", "")
LLM_API_KEY = os.getenv("GUESSWHO_LLM_API_KEY", "")
LLM_MODEL = os.getenv("GUESSWHO_LLM_MODEL", "gpt-4o-mini")


def llm_configured() -> bool:
    return bool(LLM_BASE_URL and LLM_API_KEY)


def llm_generate(name: str, category: str = "当代名人") -> dict:
    """LLM 生成一道完整题库条目（schema 校验 + 别名去重）。未配置则抛 RuntimeError。"""
    if not llm_configured():
        raise RuntimeError("LLM 未配置：请设置 GUESSWHO_LLM_BASE_URL / GUESSWHO_LLM_API_KEY")

    prompt = (
        f"你是出题专家。为名人「{name}」（类别：{category}）生成一道猜人名题目，"
        "严格输出 JSON（不要多余文字），格式：\n"
        '{"name": "规范名", "aliases": ["别名1", "别名2"], "category": "类别", '
        '"difficulty": 1到5的整数, "progressive_clues": ["由浅入深的8条线索，不要直接出现人名"], '
        '"twenty_q_meta": {"is_real": true, "is_chinese": true或false, "is_ancient": true或false, '
        '"is_political": true或false, "gender": "male或female"}, '
        '"description_keywords": [["关键词组1"], ["关键词组2"]]}'
    )
    body = json.dumps({
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }).encode()
    req = urllib.request.Request(
        LLM_BASE_URL.rstrip("/") + "/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + LLM_API_KEY},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    text = data["choices"][0]["message"]["content"]

    # 容忍 ```json 包裹
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    q = json.loads(text)
    return validate_entry(q)


def validate_entry(q: dict) -> dict:
    """schema 校验 + 别名去重（防止把已有题目重复入库）"""
    required = ["name", "category", "progressive_clues"]
    for k in required:
        if not q.get(k):
            raise ValueError(f"生成结果缺少字段: {k}")
    if not isinstance(q["progressive_clues"], list) or len(q["progressive_clues"]) < 3:
        raise ValueError("progressive_clues 至少 3 条")
    q.setdefault("aliases", [])
    q.setdefault("difficulty", 3)
    q.setdefault("twenty_q_meta", {})
    q.setdefault("description_keywords", [])

    # 去重：name 或任一别名与题库冲突则拒绝
    bank = load_bank()
    new_names = {q["name"], *q.get("aliases", [])}
    for existing in bank:
        exist_names = {existing["name"], *existing.get("aliases", [])}
        if new_names & exist_names:
            raise ValueError(f"与题库已有题目重复: {existing['name']}")
    return q
