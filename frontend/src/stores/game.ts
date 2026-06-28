import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { questions } from '../data/questions'

export interface Question {
  name: string
  aliases: string[]
  clues: string[]
  category: string
  difficulty: number
}

export const useGameStore = defineStore('game', () => {
  // 状态
  const currentQuestion = ref<Question | null>(null)
  const clueIndex = ref(0)
  const score = ref(0)
  const streak = ref(0)
  const guessCount = ref(0)
  const maxClues = 8
  const difficulty = ref(1.5) // 默认难度倍率
  const gameHistory = ref<Array<{ question: Question; clueIndex: number; correct: boolean; score: number }>>([])

  // 线索系数
  const clueMultipliers = [8, 7, 6, 5, 4, 3, 2, 1]

  // 计算属性
  const currentClue = computed(() => {
    if (!currentQuestion.value) return ''
    return currentQuestion.value.clues[clueIndex.value] || ''
  })

  const progress = computed(() => (clueIndex.value + 1) / maxClues)

  const canGuess = computed(() => clueIndex.value < maxClues)

  const canNextClue = computed(() => clueIndex.value < maxClues - 1)

  // 开始新游戏
  function startGame() {
    const pool = questions.filter(q => q.difficulty <= 3) // MVP只用简单题
    const idx = Math.floor(Math.random() * pool.length)
    currentQuestion.value = pool[idx]
    clueIndex.value = 0
    score.value = 0
    streak.value = 0
    guessCount.value = 0
  }

  // 下一条线索
  function nextClue() {
    if (canNextClue.value) {
      clueIndex.value++
      guessCount.value = 0
    }
  }

  // 验证答案
  function validateAnswer(input: string): { correct: boolean; matchType: string } {
    if (!currentQuestion.value) return { correct: false, matchType: 'none' }

    const normalized = input.trim().toLowerCase().replace(/\s/g, '')
    if (!normalized) return { correct: false, matchType: 'none' }

    // 精确匹配
    const nameNorm = currentQuestion.value.name.toLowerCase().replace(/\s/g, '')
    if (normalized === nameNorm) return { correct: true, matchType: 'exact' }

    // 别名匹配
    for (const alias of currentQuestion.value.aliases) {
      if (normalized === alias.toLowerCase().replace(/\s/g, '')) {
        return { correct: true, matchType: 'alias' }
      }
    }

    // 模糊匹配（编辑距离 ≤ 2）
    if (levenshtein(normalized, nameNorm) <= 2) {
      return { correct: true, matchType: 'fuzzy' }
    }

    return { correct: false, matchType: 'none' }
  }

  // 提交猜测
  function submitGuess(input: string): { correct: boolean; matchType: string; points: number } {
    guessCount.value++
    const result = validateAnswer(input)

    if (result.correct) {
      const multiplier = clueMultipliers[clueIndex.value] || 1
      const comboMult = streak.value >= 5 ? 1.5 : streak.value >= 3 ? 1.2 : 1.0
      const guessPenalty = guessCount.value === 1 ? 1.0 : 0.7
      const points = Math.round(100 * multiplier * difficulty.value * comboMult * guessPenalty)

      score.value += points
      streak.value++

      gameHistory.value.push({
        question: currentQuestion.value!,
        clueIndex: clueIndex.value,
        correct: true,
        score: points,
      })

      return { correct: true, matchType: result.matchType, points }
    } else {
      streak.value = 0
      return { correct: false, matchType: result.matchType, points: 0 }
    }
  }

  // 获取温度等级
  function getTemperature(): { level: number; label: string; color: string } {
    const levels = [
      { level: 0, label: '相距甚远', color: '#4A6A4A' },
      { level: 1, label: '略有眉目', color: '#5A8F6A' },
      { level: 2, label: '渐入佳境', color: '#C8A84E' },
      { level: 3, label: '呼之欲出', color: '#CC8844' },
      { level: 4, label: '触手可及', color: '#C42B2B' },
    ]
    return levels[Math.min(clueIndex.value, 4)]
  }

  // 获取星级
  function getStars(): number {
    return Math.max(1, 5 - clueIndex.value)
  }

  return {
    currentQuestion, clueIndex, score, streak, guessCount,
    maxClues, difficulty, gameHistory,
    currentClue, progress, canGuess, canNextClue,
    startGame, nextClue, submitGuess, getTemperature, getStars,
  }
})

// 编辑距离算法
function levenshtein(s1: string, s2: string): number {
  if (s1.length < s2.length) return levenshtein(s2, s1)
  if (s2.length === 0) return s1.length
  let prev = Array.from({ length: s2.length + 1 }, (_, i) => i)
  for (let i = 0; i < s1.length; i++) {
    const curr = [i + 1]
    for (let j = 0; j < s2.length; j++) {
      const cost = s1[i] === s2[j] ? 0 : 1
      curr.push(Math.min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost))
    }
    prev = curr
  }
  return prev[s2.length]
}
