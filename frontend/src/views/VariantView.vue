<template>
  <div class="variant">
    <div class="v-header">
      <div class="v-sigil">🔮</div>
      <h1 class="v-title">变体出题</h1>
      <div class="v-sub">关键词拼图 · 每局全新组合</div>
    </div>

    <div class="panel">
      <template v-if="!finished">
        <div class="clue-list">
          <div v-for="(c, i) in revealedClues" :key="i" class="clue-item">
            <span class="clue-num">🕯️{{ i + 1 }}</span>
            <span class="clue-text">{{ c }}</span>
          </div>
        </div>

        <div class="guess-row">
          <input
            v-model="guessInput"
            class="guess-input"
            placeholder="输入人名..."
            maxlength="20"
            @keydown.enter="submitGuess"
          />
          <button class="btn-blood" :disabled="loading" @click="submitGuess">猜测</button>
        </div>

        <div class="action-row">
          <button class="btn-stone" :disabled="loading || cluesExhausted" @click="revealClue">
            {{ cluesExhausted ? '线索已尽' : '揭示下一条线索' }}
          </button>
        </div>

        <div v-if="feedback" class="feedback" :class="feedbackClass">{{ feedback }}</div>
      </template>

      <template v-else>
        <div class="finish-box">
          <div class="finish-emoji">{{ won ? '🎉' : '💀' }}</div>
          <div class="finish-text">{{ won ? `猜中！+${points} 分` : '未能识破' }}</div>
          <div class="finish-answer">答案是：{{ answer }}</div>
          <div class="action-row">
            <button class="btn-blood" @click="startGame">再来一局</button>
            <button class="btn-stone" @click="$router.push('/')">返回首页</button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { api } from '../api/client'

const loading = ref(false)
const guessInput = ref('')
const feedback = ref('')
const feedbackClass = ref('')
const revealedClues = ref<string[]>([])
const state = ref<any>({})
const finished = ref(false)
const won = ref(false)
const points = ref(0)
const answer = ref('')

const cluesExhausted = computed(() => {
  return state.value.clue_index >= (state.value.total_clues || 1) - 1
})

async function startGame() {
  loading.value = true
  try {
    const s = await api.variantStart()
    state.value = s
    revealedClues.value = [s.clue]
    finished.value = false
    won.value = false
    points.value = 0
    answer.value = ''
    feedback.value = ''
    guessInput.value = ''
  } finally {
    loading.value = false
  }
}

async function revealClue() {
  loading.value = true
  try {
    const c = await api.variantClue(state.value.session_id)
    revealedClues.value.push(c.clue)
    state.value = { ...state.value, clue_index: c.clue_index, total_clues: c.total_clues }
    feedback.value = ''
  } finally {
    loading.value = false
  }
}

async function submitGuess() {
  const g = guessInput.value.trim()
  if (!g || loading.value) return
  loading.value = true
  try {
    const r = await api.variantGuess(state.value.session_id, g)
    guessInput.value = ''
    if (r.correct) {
      won.value = true
      points.value = r.points
      answer.value = r.answer
      finished.value = true
      return
    }
    if (r.finished) {
      won.value = false
      answer.value = r.answer || ''
      finished.value = true
      return
    }
    feedback.value = '💀 此名非也……新线索已曝光'
    feedbackClass.value = 'bad'
    revealedClues.value.push(r.revealed_clue)
    state.value = { ...state.value, clue_index: r.clue_index, total_clues: r.total_clues }
  } finally {
    loading.value = false
  }
}

startGame()
</script>

<style scoped>
.variant {
  min-height: 100vh;
  background: var(--diablo-bg);
  color: var(--diablo-fg);
  padding: 24px 16px 48px;
  font-family: var(--font-sans);
}

.v-header {
  text-align: center;
  margin-bottom: 24px;
}

.v-sigil {
  font-size: 44px;
}

.v-title {
  font-family: var(--font-gothic);
  color: var(--diablo-gold-bright);
  font-size: 28px;
  margin: 8px 0 4px;
  letter-spacing: 4px;
}

.v-sub {
  color: var(--diablo-muted);
  font-size: 13px;
}

.panel {
  max-width: 480px;
  margin: 0 auto;
  background: var(--diablo-stone);
  border: 1px solid var(--diablo-stone-border);
  border-radius: var(--radius-md);
  padding: 20px;
}

.clue-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.clue-item {
  display: flex;
  gap: 10px;
  background: var(--diablo-stone-light);
  border-left: 3px solid var(--diablo-gold-dim);
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  line-height: 1.6;
}

.clue-num {
  color: var(--diablo-gold);
  flex-shrink: 0;
}

.guess-row {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.guess-input {
  flex: 1;
  background: var(--diablo-bg-deep);
  border: 1px solid var(--diablo-stone-border);
  border-radius: var(--radius-sm);
  color: var(--diablo-fg-bright);
  padding: 10px 14px;
  font-size: 15px;
  outline: none;
}

.guess-input:focus {
  border-color: var(--diablo-gold-dim);
}

.action-row {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 8px;
}

.btn-blood {
  background: linear-gradient(180deg, var(--diablo-blood-bright), var(--diablo-blood));
  border: 1px solid var(--diablo-blood-bright);
  color: var(--diablo-fg-bright);
  padding: 10px 28px;
  border-radius: var(--radius-sm);
  font-size: 15px;
  cursor: pointer;
  font-family: var(--font-gothic);
  letter-spacing: 2px;
}

.btn-blood:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-stone {
  background: var(--diablo-stone-light);
  border: 1px solid var(--diablo-stone-border);
  color: var(--diablo-fg);
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
}

.btn-stone:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.feedback {
  margin-top: 14px;
  text-align: center;
  font-size: 15px;
  padding: 10px;
  border-radius: var(--radius-sm);
}

.feedback.bad {
  color: var(--diablo-blood-bright);
  background: var(--diablo-blood-glow);
}

.finish-box {
  text-align: center;
  padding: 16px 0;
}

.finish-emoji {
  font-size: 52px;
}

.finish-text {
  font-family: var(--font-gothic);
  font-size: 24px;
  color: var(--diablo-gold-bright);
  margin: 8px 0;
}

.finish-answer {
  color: var(--diablo-muted);
  font-size: 15px;
  margin-bottom: 20px;
}
</style>
