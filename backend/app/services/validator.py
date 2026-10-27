"""答案验证服务 - 5层匹配策略"""

from typing import Optional


def normalize(text: str) -> str:
    """标准化：去空格、统一小写"""
    return text.strip().lower().replace(" ", "")


def levenshtein(s1: str, s2: str) -> int:
    """编辑距离"""
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + (c1 != c2)))
        prev = curr
    return prev[-1]


def pinyin_match(input_text: str, correct: str) -> bool:
    """拼音匹配（同音字容错）"""
    try:
        from pypinyin import lazy_pinyin
        return "".join(lazy_pinyin(input_text)) == "".join(lazy_pinyin(correct))
    except ImportError:
        return False


def validate_answer(user_input: str, correct_name: str, aliases: list[str]) -> dict:
    """
    多层答案验证
    返回: {"correct": bool, "match_type": str}
    """
    norm_input = normalize(user_input)
    if not norm_input:
        return {"correct": False, "match_type": "empty"}

    norm_name = normalize(correct_name)

    # 1. 精确匹配
    if norm_input == norm_name:
        return {"correct": True, "match_type": "exact"}

    # 2. 别名匹配
    for alias in aliases:
        if norm_input == normalize(alias):
            return {"correct": True, "match_type": "alias"}

    # 3. 模糊匹配（长度自适应编辑距离阈值）
    # 修复（2026-10-27）：旧版绝对阈值 ≤2 有洞——2字输入能匹配任意2字人名
    # （"测试" vs "雷军" 距离=2 会被判对）。改为按名字长度自适应：
    #   1字名：只能精确；2-3字名：容1个错字（"雷均"→"雷军"）；4字+：容2个错字
    name_len = len(norm_name)
    threshold = 0 if name_len <= 1 else (1 if name_len <= 3 else 2)
    # 单字输入不做模糊匹配（"雷"不能蒙对"雷军"），1字名只能靠精确/别名
    if len(norm_input) >= 2 and levenshtein(norm_input, norm_name) <= threshold:
        return {"correct": True, "match_type": "fuzzy"}

    # 4. 拼音匹配
    if pinyin_match(user_input, correct_name):
        return {"correct": True, "match_type": "pinyin"}

    # 5. 包含匹配（输入包含正确答案的字，至少3字）
    if len(norm_input) >= 3 and norm_name in norm_input:
        return {"correct": True, "match_type": "contains"}

    return {"correct": False, "match_type": "none"}
