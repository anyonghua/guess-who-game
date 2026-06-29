<template>
  <div class="leaderboard">
    <div class="lb-header">
      <div class="lb-title">🏆 排行榜</div>
      <button class="back-btn" @click="$router.push('/')">← 返回</button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="ranking.length === 0" class="empty">
      <div class="empty-icon">🏆</div>
      <div class="empty-text">暂无排行数据</div>
      <div class="empty-hint">完成一局对战即可上榜</div>
    </div>

    <div v-else class="rank-list">
      <div v-for="item in ranking" :key="item.rank" class="rank-item" :class="{ 'top-3': item.rank <= 3 }">
        <div class="rank-num">
          {{ item.rank <= 3 ? ['🥇','🥈','🥉'][item.rank-1] : item.rank }}
        </div>
        <div class="rank-info">
          <div class="rank-name">{{ item.name }}</div>
          <div class="rank-meta">{{ item.games }}局 · {{ item.wins }}胜</div>
        </div>
        <div class="rank-score">{{ item.score }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../api/client'

const ranking = ref<Array<{ rank: number; name: string; score: number; games: number; wins: number }>>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const data = await fetch('http://localhost:8000/api/battle/leaderboard').then(r => r.json())
    ranking.value = data.ranking || []
  } catch (e) {} finally {
    loading.value = false
  }
})
</script>

<style scoped>
.leaderboard { min-height: 100vh; position: relative; z-index: 1; padding-top: 12px; }
.lb-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.lb-title { font-family: var(--font-cinzel); font-size: 18px; font-weight: 700; color: var(--diablo-gold-bright); letter-spacing: 2px; }
.back-btn { font-size: 12px; color: var(--diablo-muted); background: none; border: none; cursor: pointer; }
.loading { text-align: center; padding: 40px; color: var(--diablo-muted); }
.empty { text-align: center; padding: 60px 0; }
.empty-icon { font-size: 48px; margin-bottom: 12px; opacity: 0.3; }
.empty-text { font-family: var(--font-cinzel); font-size: 16px; color: var(--diablo-muted); margin-bottom: 4px; }
.empty-hint { font-size: 12px; color: var(--diablo-stone-border); }
.rank-list { display: flex; flex-direction: column; gap: 4px; }
.rank-item { display: flex; align-items: center; gap: 14px; padding: 14px 16px; background: var(--diablo-stone); border: 1px solid var(--diablo-stone-border); transition: border-color 0.2s; }
.rank-item:hover { border-color: var(--diablo-gold-dim); }
.rank-item.top-3 { border-color: rgba(200,168,78,0.2); }
.rank-num { width: 32px; text-align: center; font-family: var(--font-cinzel); font-size: 14px; font-weight: 700; color: var(--diablo-muted); }
.rank-info { flex: 1; }
.rank-name { font-size: 14px; font-weight: 500; color: var(--diablo-fg-bright); }
.rank-meta { font-size: 11px; color: var(--diablo-muted); margin-top: 2px; }
.rank-score { font-family: var(--font-cinzel); font-size: 18px; font-weight: 700; color: var(--diablo-gold-bright); text-shadow: 0 0 8px var(--diablo-gold-glow); }
</style>
