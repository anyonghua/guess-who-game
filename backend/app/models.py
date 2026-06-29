"""数据库模型"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    aliases = Column(JSON, nullable=False, default=list)  # ["孔明", "卧龙"]
    category = Column(String(50), nullable=False, index=True)
    subcategory = Column(String(50))
    difficulty = Column(Integer, nullable=False, default=3)  # 1-5
    era = Column(String(50))
    nationality = Column(String(50))

    # 渐进揭秘线索 (JSON array of 8 strings)
    progressive_clues = Column(JSON, nullable=False)

    # 二十问元数据
    twenty_q_meta = Column(JSON, default=dict)

    # 描述接龙关键词 (JSON array of arrays)
    description_keywords = Column(JSON, default=list)

    # emoji描述
    emoji_description = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(String(36), primary_key=True)  # UUID
    player_id = Column(String(36), nullable=True)
    mode = Column(String(20), nullable=False)  # progressive | twenty_q | chain
    difficulty = Column(String(20), default="normal")
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)

    clue_index = Column(Integer, default=0)
    score = Column(Integer, default=0)
    streak = Column(Integer, default=0)
    guess_count = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    is_correct = Column(Boolean, default=False)

    # 二十问对话历史
    conversation = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    question = relationship("Question")


class Player(Base):
    __tablename__ = "players"

    id = Column(String(36), primary_key=True)
    nickname = Column(String(50), default="无名者")
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
