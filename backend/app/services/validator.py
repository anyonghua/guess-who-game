"""答案验证引擎 - 多层匹配策略"""

from typing import Optional


def normalize(text: str) -> str:
    """标准化文本：去空格、统一大小写"""
    return text.strip().lower().replace(" ", "")


def levenshtein_distance(s1: str, s2: str) -> int:
    """计算编辑距离"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def pinyin_match(input_text: str, correct_answer: str) -> bool:
    """拼音匹配（同音字容错）"""
    try:
        from pypinyin import lazy_pinyin
        input_py = "".join(lazy_pinyin(input_text))
        answer_py = "".join(lazy_pinyin(correct_answer))
        return input_py == answer_py
    except ImportError:
        return False


async def ai_semantic_match(input_text: str, correct_answer: str) -> bool:
    """AI 语义匹配（兜底）- 调用 LLM 判断是否是同一个人"""
    # TODO: 调用 LLM API 判断
    # prompt = f"判断以下两个名字是否指同一个人: '{input_text}' vs '{correct_answer}'，只回答 yes 或 no"
    return False


async def validate_answer(
    user_input: str,
    correct_answer: str,
    aliases: list[str],
) -> tuple[bool, str]:
    """
    多层答案验证
    
    Returns:
        (is_correct, match_type) - 匹配结果和匹配类型
    """
    normalized_input = normalize(user_input)

    # 1. 精确匹配
    if normalized_input == normalize(correct_answer):
        return True, "exact"

    # 2. 别名匹配
    for alias in aliases:
        if normalized_input == normalize(alias):
            return True, "alias"

    # 3. 模糊匹配（编辑距离 ≤ 2）
    if levenshtein_distance(normalized_input, normalize(correct_answer)) <= 2:
        return True, "fuzzy"

    # 4. 拼音匹配
    if pinyin_match(user_input, correct_answer):
        return True, "pinyin"

    # 5. AI 语义匹配（最后兜底）
    if await ai_semantic_match(user_input, correct_answer):
        return True, "semantic"

    return False, "none"
