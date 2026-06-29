"""题库导入脚本 - 从 JSON 文件批量导入到数据库"""

import asyncio
import json
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, async_session, init_db, Base
from app.models import Question
from sqlalchemy import select


async def seed_questions(json_path: str):
    """从 JSON 文件导入题库"""
    await init_db()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    async with async_session() as db:
        created = 0
        skipped = 0

        for item in data:
            # 检查是否已存在
            exists = await db.scalar(
                select(Question.id).where(Question.name == item["name"])
            )
            if exists:
                skipped += 1
                continue

            q = Question(
                name=item["name"],
                aliases=item.get("aliases", []),
                category=item.get("category", "未分类"),
                subcategory=item.get("subcategory"),
                difficulty=item.get("difficulty", 3),
                progressive_clues=item.get("progressive_clues", []),
                twenty_q_meta=item.get("twenty_q_meta", {}),
                description_keywords=item.get("description_keywords", []),
                emoji_description=item.get("emoji_description", []),
            )
            db.add(q)
            created += 1

        await db.commit()

    print(f"✅ 导入完成: 新增 {created} 题, 跳过 {skipped} 题 (已存在)")


if __name__ == "__main__":
    json_path = sys.argv[1] if len(sys.argv) > 1 else "../../data/questions_sample.json"
    asyncio.run(seed_questions(json_path))
