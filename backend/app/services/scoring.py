"""计分服务"""

# 线索系数
CLUE_MULTIPLIER = {0: 8, 1: 7, 2: 6, 3: 5, 4: 4, 5: 3, 6: 2, 7: 1}

# 难度倍率
DIFFICULTY_MAP = {"easy": 1.0, "normal": 1.5, "hard": 2.0, "hell": 3.0}


def get_combo_multiplier(streak: int) -> float:
    if streak >= 10: return 2.5
    if streak >= 7: return 2.0
    if streak >= 5: return 1.5
    if streak >= 3: return 1.2
    return 1.0


def calculate_score(clue_index: int, difficulty: str = "normal", streak: int = 0, first_guess: bool = True) -> dict:
    base = 100
    multiplier = CLUE_MULTIPLIER.get(clue_index, 1)
    diff_mult = DIFFICULTY_MAP.get(difficulty, 1.5)
    combo = get_combo_multiplier(streak)
    penalty = 1.0 if first_guess else 0.7

    score = int(base * multiplier * diff_mult * combo * penalty)
    stars = max(1, 5 - clue_index)

    return {
        "score": score,
        "stars": stars,
        "breakdown": {
            "base": base,
            "clue_multiplier": multiplier,
            "difficulty_multiplier": diff_mult,
            "combo_multiplier": combo,
            "guess_penalty": penalty,
        }
    }
