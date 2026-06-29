import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../api/client'

export interface GameSession {
  session_id: string
  clue_index: number
  clue: string
  total_clues: number
  score: number
  streak: number
}

export interface GuessResult {
  correct: boolean
  match_type: string
  message: string
  points: number
  session_id: string
  clue_index: number
  clue: string | null
  score: number
  streak: number
  temperature: { level: number; label: string; color: string } | null
}

export const useGameStore = defineStore('game', () => {
  const session = ref<GameSession | null>(null)
  const lastGuess = ref<GuessResult | null>(null)
  const loading = ref(false)
  const error = ref('')

  // 计算属性
  const sessionId = computed(() => session.value?.session_id || '')
  const clueIndex = computed(() => session.value?.clue_index || 0)
  const clue = computed(() => session.value?.clue || '')
  const totalClues = computed(() => session.value?.total_clues || 8)
  const score = computed(() => session.value?.score || 0)
  const streak = computed(() => session.value?.streak || 0)
  const maxClues = 8

  const canNextClue = computed(() => clueIndex.value < maxClues - 1)

  // 开始游戏
  async function startGame(difficulty = 'normal') {
    loading.value = true
    error.value = ''
    try {
      const data = await api.startGame(difficulty)
      session.value = data
      lastGuess.value = null
    } catch (e: any) {
      error.value = e.message || '启动失败'
    } finally {
      loading.value = false
    }
  }

  // 提交猜测
  async function submitGuess(answer: string): Promise<GuessResult | null> {
    if (!sessionId.value) return null
    loading.value = true
    error.value = ''
    try {
      const result = await api.submitGuess(sessionId.value, answer)
      lastGuess.value = result
      // 更新 session 状态
      if (session.value) {
        session.value.clue_index = result.clue_index
        session.value.clue = result.clue || session.value.clue
        session.value.score = result.score
        session.value.streak = result.streak
      }
      return result
    } catch (e: any) {
      error.value = e.message || '提交失败'
      return null
    } finally {
      loading.value = false
    }
  }

  // 跳过线索（本地处理，不需要调API）
  function skipClue() {
    if (session.value && canNextClue.value) {
      // 跳过相当于猜错一次，但不提交答案
      // 我们需要调 API 来推进线索
      // 暂时用本地逻辑
    }
  }

  // 获取结果
  async function getResult() {
    if (!sessionId.value) return null
    try {
      return await api.getResult(sessionId.value)
    } catch (e: any) {
      error.value = e.message
      return null
    }
  }

  // 重置
  function reset() {
    session.value = null
    lastGuess.value = null
    error.value = ''
  }

  return {
    session, lastGuess, loading, error,
    sessionId, clueIndex, clue, totalClues, score, streak, maxClues, canNextClue,
    startGame, submitGuess, getResult, reset,
  }
})
