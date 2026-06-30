/* 用户状态管理 - localStorage 持久化 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../api/client'

const PLAYER_KEY = 'guess_who_player_id'
const NICKNAME_KEY = 'guess_who_nickname'

export const useUserStore = defineStore('user', () => {
  const playerId = ref(localStorage.getItem(PLAYER_KEY) || '')
  const nickname = ref(localStorage.getItem(NICKNAME_KEY) || '')
  const profile = ref<any>(null)
  const loading = ref(false)

  const isLoggedIn = computed(() => !!playerId.value)
  const level = computed(() => profile.value?.level || 1)
  const xp = computed(() => profile.value?.experience || 0)
  const xpProgress = computed(() => profile.value?.xp_progress || 0)
  const gamesPlayed = computed(() => profile.value?.games_played || 0)
  const winRate = computed(() => profile.value?.win_rate || 0)

  async function register(name: string) {
    loading.value = true
    try {
      const data = await api.createPlayer(name)
      playerId.value = data.player_id
      nickname.value = data.nickname
      localStorage.setItem(PLAYER_KEY, data.player_id)
      localStorage.setItem(NICKNAME_KEY, data.nickname)
      await loadProfile()
    } finally {
      loading.value = false
    }
  }

  async function loadProfile() {
    if (!playerId.value) return
    try {
      profile.value = await api.getPlayer(playerId.value)
      nickname.value = profile.value.nickname
    } catch (e) {
      // 玩家可能被清除，重新注册
      playerId.value = ''
      localStorage.removeItem(PLAYER_KEY)
    }
  }

  async function recordGameResult(score: number, won: boolean) {
    if (!playerId.value) return null
    try {
      const result = await api.recordGame(playerId.value, score, won)
      await loadProfile()
      return result
    } catch (e) {
      return null
    }
  }

  function logout() {
    playerId.value = ''
    nickname.value = ''
    profile.value = null
    localStorage.removeItem(PLAYER_KEY)
    localStorage.removeItem(NICKNAME_KEY)
  }

  return {
    playerId, nickname, profile, loading,
    isLoggedIn, level, xp, xpProgress, gamesPlayed, winRate,
    register, loadProfile, recordGameResult, logout,
  }
})
