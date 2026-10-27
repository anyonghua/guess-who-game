#!/usr/bin/env python3
"""AI 动态出题 CLI —— 批量生成题库条目并入库（题库扩充用法）

用法：
  # 生成 3 道题（需要 GUESSWHO_LLM_* 环境变量）
  GUESSWHO_LLM_BASE_URL=... GUESSWHO_LLM_API_KEY=... \
    python3 scripts/generate_questions.py --names "苏轼,李白,爱因斯坦" --category 历史人物

  # 预览程序化变体（零依赖，不需要 LLM）
  python3 scripts/generate_questions.py --preview-variant 3

生成结果先写入 data/questions_bank.draft.json 待人工审核，
确认后 --merge 合并进 data/questions_bank.json（自动备份）。
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.generator_service import llm_generate, llm_configured, make_variant, load_bank

DATA = Path(__file__).resolve().parents[1] / "data"
BANK = DATA / "questions_bank.json"
DRAFT = DATA / "questions_bank.draft.json"


def preview_variants(n: int):
    bank = load_bank()
    import random
    rng = random.Random()
    for _ in range(n):
        v = make_variant(rng.choice(bank), rng)
        print(f"\n🔮 变体题 [{v['category']}] 难度{v['difficulty']}")
        for i, c in enumerate(v["clues"], 1):
            print(f"  {i}. {c}")
        print(f"  答案: {v['name']}（别名: {'、'.join(v['aliases']) or '无'}）")


def generate(names, category):
    if not llm_configured():
        print("❌ LLM 未配置。请设置 GUESSWHO_LLM_BASE_URL / GUESSWHO_LLM_API_KEY / GUESSWHO_LLM_MODEL")
        sys.exit(1)
    drafts = []
    for name in names:
        try:
            q = llm_generate(name.strip(), category)
            drafts.append(q)
            print(f"✅ 生成: {q['name']}（{len(q['progressive_clues'])} 条线索）")
        except Exception as e:
            print(f"⚠️ 跳过「{name}」: {e}")
    if drafts:
        existing = []
        if DRAFT.exists():
            existing = json.loads(DRAFT.read_text(encoding="utf-8"))
        DRAFT.write_text(json.dumps(existing + drafts, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n📝 {len(drafts)} 道草稿已写入 {DRAFT}，审核后用 --merge 入库")


def merge():
    if not DRAFT.exists():
        print("没有草稿可合并")
        return
    drafts = json.loads(DRAFT.read_text(encoding="utf-8"))
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    backup = BANK.with_suffix(f".bak-{datetime.now():%Y%m%d%H%M%S}.json")
    shutil.copy(BANK, backup)
    bank.extend(drafts)
    BANK.write_text(json.dumps(bank, ensure_ascii=False, indent=2), encoding="utf-8")
    DRAFT.unlink()
    print(f"✅ 已合并 {len(drafts)} 道题，题库总量 {len(bank)}（备份: {backup.name}）")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", help="逗号分隔的人名列表")
    ap.add_argument("--category", default="当代名人", help="类别")
    ap.add_argument("--preview-variant", type=int, metavar="N", help="预览 N 道程序化变体")
    ap.add_argument("--merge", action="store_true", help="把草稿合并进题库")
    args = ap.parse_args()

    if args.preview_variant:
        preview_variants(args.preview_variant)
    elif args.names:
        generate([n for n in args.names.split(",") if n.strip()], args.category)
    elif args.merge:
        merge()
    else:
        ap.print_help()
