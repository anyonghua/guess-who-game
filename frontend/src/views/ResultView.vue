<template>
  <div class="result">
    <div class="result-circle" :class="{ success: isCorrect }">
      <span>{{ isCorrect ? '✦' : '○' }}</span>
    </div>
    <h2 class="result-heading">{{ isCorrect ? '命运已定' : '迷雾散尽' }}</h2>
    <div class="result-name">{{ resultData?.answer || '---' }}</div>

    <OrnateFrame class="result-frame">
      <div class="result-label">灵魂献祭</div>
      <div class="result-score">{{ resultData?.score || 0 }}</div>
      <div class="result-stars">
        <span v-for="i in 5" :key="i" :class="{ lit: i <= (resultData?.stars || 0) }">✦</span>
      </div>
      <div class="result-note">
        第{{ (resultData?.clue_index || 0) + 1 }}条线索 · 难度 ×{{ resultData?.difficulty || 1.5 }}
      </div>
    </OrnateFrame>

    <button class="replay-btn" @click="replay">再入深渊</button>
    <button class="home-link" @click="goHome">返回大厅</button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'
import OrnateFrame from '../components/OrnateFrame.vue'

const router = useRouter()
const game = useGameStore()
const resultData = ref<any>(null)

onMounted(async () => {
  if (!game.sessionId) {
    router.replace('/')
    return
  }
  resultData.value = await game.getResult()
})

const isCorrect = computed(() => resultData.value?.correct || false)

async function replay() {
  game.reset()
  await game.startGame('normal')
  if (!game.error) router.push('/game')
}

function goHome() {
  game.reset()
  router.push('/')
}
</script>

<style scoped>
.result {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; min-height: 100vh; text-align: center;
  position: relative; z-index: 1;
  animation: fadeUp 0.6s ease;
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
.result-circle {
  width: 80px; height: 80px; border-radius: 50%;
  border: 2px solid var(--diablo-gold-dim);
  display: flex; align-items: center; justify-content: center;
  font-size: 32px; margin-bottom: 20px;
  box-shadow: 0 0 30px var(--diablo-gold-glow);
  position: relative;
}
.result-circle::before {
  content: ''; position: absolute; inset: -6px; border-radius: 50%;
  border: 1px solid rgba(200,168,78,0.15);
}
.result-circle.success { border-color: var(--diablo-gold); color: var(--diablo-gold-bright); }
.result-circle:not(.success) { border-color: var(--diablo-stone-border); color: var(--diablo-muted); }
.result-heading {
  font-family: var(--font-cinzel); font-size: 24px; font-weight: 900;
  color: var(--diablo-gold-bright); letter-spacing: 3px;
  text-shadow: 0 0 20px var(--diablo-gold-glow); margin-bottom: 6px;
}
.result-name {
  font-family: var(--font-gothic); font-size: 18px;
  color: var(--diablo-fg); margin-bottom: 28px;
}
.result-frame { padding: 28px 44px; margin-bottom: 32px; text-align: center; }
.result-label {
  font-family: var(--font-cinzel); font-size: 9px;
  letter-spacing: 4px; text-transform: uppercase;
  color: var(--diablo-muted); margin-bottom: 8px;
}
.result-score {
  font-family: var(--font-cinzel); font-size: 52px; font-weight: 900;
  color: var(--diablo-gold-bright);
  text-shadow: 0 0 30px var(--diablo-gold-glow);
}
.result-stars {
  font-size: 18px; margin: 10px 0; letter-spacing: 6px;
  color: var(--diablo-stone-border);
}
.result-stars .lit { color: var(--diablo-gold); }
.result-note {
  font-family: var(--font-cinzel); font-size: 11px;
  color: var(--diablo-muted); letter-spacing: 1px;
}
.replay-btn {
  padding: 14px 48px; cursor: pointer;
  font-family: var(--font-cinzel); font-size: 12px; font-weight: 700;
  letter-spacing: 3px; text-transform: uppercase;
  background: linear-gradient(180deg, var(--diablo-gold), var(--diablo-gold-dim));
  color: var(--diablo-bg); border: none; transition: all 0.2s;
  position: relative; margin-bottom: 16px;
}
.replay-btn::before {
  content: ''; position: absolute; inset: -4px;
  border: 1px solid var(--diablo-gold-dim);
}
.replay-btn:hover {
  background: linear-gradient(180deg, var(--diablo-gold-bright), var(--diablo-gold));
  box-shadow: 0 0 24px var(--diablo-gold-glow);
}
.home-link {
  font-family: var(--font-cinzel); font-size: 11px;
  color: var(--diablo-muted); background: none; border: none;
  letter-spacing: 1px; transition: color 0.2s;
}
.home-link:hover { color: var(--diablo-gold); }
</style>
