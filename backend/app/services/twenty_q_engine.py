"""二十问 AI 回答引擎

核心逻辑：基于 twenty_q_meta 查表回答，不是让 AI 自由发挥。
AI 的角色 = 用好听的方式说标准答案。
"""

import re
import random
from typing import Optional


# === 问题解析器：把自然语言映射到 meta 字段 ===

QUESTION_PATTERNS = [
    # (正则模式, meta字段, 是/否对应值)
    (r"(是|为)不?是(真实|真人|现实|真正)(存在|生活)(的|过)?", "is_real", True),
    (r"(是|为)不?是(虚构|假的|编造|杜撰)(的|角色)?", "is_real", False),
    (r"(是|为)不?是(虚构|虚拟|小说|动漫|电影|游戏)(角色|人物|人物)?", "is_fictional", True),
    (r"(还)?活着吗|是不?是(活|在世|健在)", "is_alive", True),
    (r"(已[经]?|早[已]?)(去世|死了|过世|离世|不在了)", "is_alive", False),
    (r"(是|为)不?是中国人|是中国(人|籍)吗|来自中国", "is_chinese", True),
    (r"(是|为)不?是(外国|海外|国外)(人|籍)", "is_chinese", False),
    (r"(是|为)不?是古代(人|的)|生活在古代|是古人", "is_ancient", True),
    (r"(是|为)不?是现代(人|的)|生活在现代|是当代", "is_ancient", False),
    (r"(是|为)不?是(政治家|政客|政治人物|当官)", "is_political", True),
    (r"(是|为)不?是(军人|军事|将军|武将|打仗)", "is_military", True),
    (r"(是|为)不?是(科学家|科研|学者|教授|研究)", "is_scientist", True),
    (r"(是|为)不?是(演员|歌手|明星|娱乐|艺人|音乐|运动员|体育)", "is_entertainer", True),
    (r"(是|为)不?是(男|男性|他|先生)", "gender", "male"),
    (r"(是|为)不?是(女|女性|她|女士|小姐)", "gender", "female"),
    (r"(是|为)不?是(三国|东汉|汉末)", "dynasty", "三国"),
    (r"(是|为)不?是(唐朝|唐代)", "dynasty", "唐朝"),
    (r"名字.*(两|2)个字", "name_length", 2),
    (r"名字.*(三|3)个字", "name_length", 3),
    (r"(姓氏|姓).*(复姓|两个字)", "is_compound_surname", True),
]

# 模糊匹配关键词（当精确模式匹配不上时）
FUZZY_KEYWORDS = {
    "is_real": ["真实", "真人", "现实", "存在", "活过", "历史上"],
    "is_fictional": ["虚构", "虚拟", "小说", "动漫", "电影", "游戏", "漫画", "角色"],
    "is_alive": ["活着", "在世", "健在", "生存", "还活"],
    "is_chinese": ["中国", "华人", "国内", "中华"],
    "is_ancient": ["古代", "古时", "以前", "很久", "千年", "百年前"],
    "is_political": ["政治", "政客", "官", "皇帝", "国王", "总统", "首相"],
    "is_military": ["军事", "军人", "将军", "武将", "打仗", "战争", "兵"],
    "is_scientist": ["科学", "科研", "学者", "教授", "研究", "发明", "物理", "化学", "数学"],
    "is_entertainer": ["演", "唱", "明星", "娱乐", "体育", "运动", "音乐", "歌", "电影", "足球", "篮球"],
    "gender": ["男", "女", "他", "她"],
}


def parse_question(question: str) -> tuple[Optional[str], Optional[any]]:
    """解析玩家的是非问题，返回 (meta字段, 期望值)"""
    q = question.strip()

    # 精确模式匹配
    for pattern, field, value in QUESTION_PATTERNS:
        if re.search(pattern, q):
            return field, value

    # 模糊关键词匹配
    q_lower = q.lower()
    for field, keywords in FUZZY_KEYWORDS.items():
        for kw in keywords:
            if kw in q_lower:
                # 判断问题是正面还是反面问法
                negation_words = ["不", "没", "非", "否", "难道"]
                is_negative = any(neg in q_lower for neg in negation_words)
                if field == "gender":
                    if "女" in q_lower or "她" in q_lower:
                        return "gender", "female"
                    return "gender", "male"
                return field, not is_negative

    return None, None


def lookup_meta(meta: dict, field: str, expected: any) -> Optional[bool]:
    """查表获取答案：True=是, False=否, None=不确定"""
    if field is None:
        return None

    value = meta.get(field)
    if value is None:
        return None

    if field == "gender":
        return value == expected

    if isinstance(value, bool):
        return value == expected

    if isinstance(value, str):
        return value == expected

    return None


# === 回答生成器：带人格化语气 ===

POSITIVE_TEMPLATES = [
    "是的，没错。",
    "没错，你说对了。",
    "是的呢，你猜得很准。",
    "对的！方向正确。",
    "没错～继续保持这个思路。",
    "是的，你问到点子上了。",
]

NEGATIVE_TEMPLATES = [
    "不是哦。",
    "不对，不是这样的。",
    "不是呢，换个方向想想。",
    "否，这个方向不太对。",
    "不是哦，你可能想偏了。",
    "不对～再想想。",
]

UNKNOWN_TEMPLATES = [
    "嗯...这个问题我不太确定怎么回答。",
    "这个问题有点模糊，换一种方式问？",
    "我不太能回答这个问题，试试问别的？",
    "这个角度不太好判断，换一个吧。",
]

# 根据剩余问题数调整语气
URGENCY_TEMPLATES = {
    "low": ["你还有大把问题，慢慢来。", "不急，继续探索。"],
    "medium": ["问题不多了，抓住重点问。", "快到极限了，想好再问。"],
    "high": ["最后几个问题了！每一问都要精准。", "机会不多了，准备好了吗？"],
    "critical": ["最后一个机会了！直接猜还是再问一个？", "最后一个问题，慎重！"],
}


def generate_response(
    answer: Optional[bool],
    question: str,
    remaining: int,
    max_questions: int,
    meta: dict = None,
) -> dict:
    """
    生成带人格的回答

    Returns:
        {
            "answer": "是" | "否" | "不确定",
            "response": "完整回答文本",
            "emotion": "hint" | "encourage" | "warning" | "neutral",
            "remaining": int,
        }
    """
    urgency = max_questions - remaining
    if remaining <= 1:
        urgency_level = "critical"
    elif remaining <= 3:
        urgency_level = "high"
    elif remaining <= max_questions // 2:
        urgency_level = "medium"
    else:
        urgency_level = "low"

    if answer is True:
        base = random.choice(POSITIVE_TEMPLATES)
        emotion = "hint"
    elif answer is False:
        base = random.choice(NEGATIVE_TEMPLATES)
        emotion = "warning"
    else:
        base = random.choice(UNKNOWN_TEMPLATES)
        emotion = "neutral"

    # 加上紧迫感提示
    urgency_msg = random.choice(URGENCY_TEMPLATES[urgency_level])

    response = f"{base}（{urgency_msg}）" if random.random() > 0.5 else base

    return {
        "answer": "是" if answer is True else ("否" if answer is False else "不确定"),
        "response": response,
        "emotion": emotion,
        "remaining": remaining,
    }


# === 主入口 ===

def answer_question(question: str, meta: dict, remaining: int, max_questions: int = 20) -> dict:
    """
    二十问核心：解析问题 → 查表 → 生成回答

    Args:
        question: 玩家的是非问题
        meta: twenty_q_meta 字典
        remaining: 剩余问题数
        max_questions: 最大问题数

    Returns:
        {"answer": str, "response": str, "emotion": str, "remaining": int}
    """
    field, expected = parse_question(question)
    answer = lookup_meta(meta, field, expected)
    return generate_response(answer, question, remaining, max_questions, meta)
