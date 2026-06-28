"""计分系统"""


# 线索系数：第1条线索猜对=8倍，第2条=7倍...第8条=1倍
CLUE_MULTIPLIER = {1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}

# 难度倍率
DIFFICULTY_MULTIPLIER = {
    "easy": 1.0,
    "normal": 1.5,
    "hard": 2.0,
    "hell": 3.0,
}

# 连击加成
def get_combo_multiplier(streak: int) -> float:
    """根据连击数返回加成倍率"""
    if streak >= 10:
        return 2.5
    elif streak >= 7:
        return 2.0
    elif streak >= 5:
        return 1.5
    elif streak >= 3:
        return 1.2
    return 1.0


BASE_SCORE = 100


def calculate_progressive_score(
    clue_number: int,
    difficulty: str = "normal",
    streak: int = 0,
    is_first_guess: bool = True,
) -> dict:
    """
    渐进揭秘模式计分
    
    Args:
        clue_number: 第几条线索时猜对 (1-8)
        difficulty: 难度等级
        streak: 当前连击数
        is_first_guess: 是否一次猜对（同一条线索下）
    """
    multiplier = CLUE_MULTIPLIER.get(clue_number, 1)
    diff_mult = DIFFICULTY_MULTIPLIER.get(difficulty, 1.0)
    combo_mult = get_combo_multiplier(streak)
    guess_penalty = 1.0 if is_first_guess else 0.7  # 同一线索多次猜测扣30%

    raw_score = BASE_SCORE * multiplier * diff_mult * combo_mult * guess_penalty
    score = int(raw_score)

    # 评级
    if clue_number <= 2:
        rating = "⭐⭐⭐⭐⭐"
    elif clue_number <= 4:
        rating = "⭐⭐⭐⭐"
    elif clue_number <= 6:
        rating = "⭐⭐⭐"
    elif clue_number <= 7:
        rating = "⭐⭐"
    else:
        rating = "⭐"

    return {
        "score": score,
        "rating": rating,
        "breakdown": {
            "base": BASE_SCORE,
            "clue_multiplier": multiplier,
            "difficulty_multiplier": diff_mult,
            "combo_multiplier": combo_mult,
            "guess_penalty": guess_penalty,
        }
    }


def calculate_twenty_q_score(
    remaining_questions: int,
    difficulty: str = "normal",
) -> dict:
    """二十问模式计分"""
    total_questions = {"easy": 25, "normal": 20, "hard": 15, "hell": 10}
    max_q = total_questions.get(difficulty, 20)
    efficiency = remaining_questions / max_q

    diff_mult = DIFFICULTY_MULTIPLIER.get(difficulty, 1.0)
    score = int(BASE_SCORE * 10 * efficiency * diff_mult)

    if efficiency >= 0.75:
        rating = "⭐⭐⭐⭐⭐"
    elif efficiency >= 0.5:
        rating = "⭐⭐⭐⭐"
    elif efficiency >= 0.25:
        rating = "⭐⭐⭐"
    elif efficiency > 0:
        rating = "⭐⭐"
    else:
        rating = "⭐"

    return {
        "score": score,
        "rating": rating,
        "efficiency": round(efficiency * 100, 1),
    }


def calculate_chain_score(
    keyword_count: int,
    difficulty: str = "normal",
) -> dict:
    """描述接龙模式计分"""
    max_keywords = 7
    efficiency = (max_keywords - keyword_count + 1) / max_keywords

    diff_mult = DIFFICULTY_MULTIPLIER.get(difficulty, 1.0)
    score = int(BASE_SCORE * 8 * efficiency * diff_mult)

    if keyword_count <= 3:
        rating = "⭐⭐⭐⭐⭐"
    elif keyword_count <= 4:
        rating = "⭐⭐⭐⭐"
    elif keyword_count <= 5:
        rating = "⭐⭐⭐"
    elif keyword_count <= 6:
        rating = "⭐⭐"
    else:
        rating = "⭐"

    return {
        "score": score,
        "rating": rating,
        "keywords_used": keyword_count,
    }
