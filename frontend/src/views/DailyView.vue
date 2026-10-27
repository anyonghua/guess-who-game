<template>
  <div class="daily">
    <!-- 标题 -->
    <div class="daily-header">
      <div class="daily-sigil">📅</div>
      <h1 class="daily-title">每日挑战</h1>
      <div class="daily-date">{{ today.date }} · 全球同题</div>
    </div>

    <!-- 开始前 -->
    <div v-if="phase === 'intro'" class="panel">
      <div class="rules">
        <div class="rule">⚔️ 每天 <b>3 题</b>：简单 / 中等 / 困难各一</div>
        <div class="rule">🕯️ 线索逐条曝光，<b>越早猜对分越高</b></div>
        <div class="rule">🏆 同一天全球玩家<b>同题同榜</b>，同分线索少者胜</div>
      </div>
      <div class="categories" v-if="today.categories?.length">
        今日领域：{{ today.categories.join(' · ') }}
      </div>
      <div class="top3" v-if="today.top3?.length">
        <div class="top3-title">今日榜首</div>
        <div v-for="(t, i) in today.top3" :key="i" class="top3-row">
          <span class="top3-rank">{{ ['🥇','🥈','🥉'][i] }}</span>
          <span class="top3-name">{{ t.player_name }}</span>
          <span class="top3-score">{{ t.score }}</span>
        </div>
      </div>
      <button class="btn-blood" @click="startGame">开始挑战</button>
    </div>

    <!-- 对局中 -->
    <div v-if="phase === 'playing'" class="panel">
      <div class="progress-row">
        <span class="q-badge">第 {{ state.question_index + 1 }} / {{ state.total_questions }} 题</span>
        <span class="diff-badge">{{ diffLabel }}</span>
      </div>

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
    </div>

    <!-- 结算 -->
    <div v-if="phase === 'result'" class="panel">
      <div class="result-total">
        <div class="result-score">{{ result.total_score }}</div>
        <div class="result-label">总积分</div>
        <div class="result-rank">第 {{ result.rank }} 名 / {{ result.total_players }} 人</div>
      </div>

      <div class="result-list">
        <div v-for="(r, i) in result.results" :key="i" class="result-row" :class="{ wrong: !r.correct }">
          <span class="result-stars">{{ '★'.repeat(r.stars) || '✗' }}</span>
          <span class="result-name">{{ r.name }}</span>
          <span class="result-detail">{{ r.correct ? `第${r.clues_used}条线索` : '未猜出' }}</span>
          <span class="result-points">{{ r.correct ? `+${r.score}` : '0' }}</span>
        </div>
      </div>

      <div class="action-row">
        <button class="btn-stone" @click="copyShare">📋 复制战绩</button>
        <button class="btn-blood" @click="backHome">返回首页</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import { useUserStore } from '../stores/user'

const router = useRouter()
const user = useUserStore()

const phase = ref<'intro' | 'playing' | 'result'>('intro')
const loading = ref(false)
const guessInput = ref('')
const feedback = ref('')
const feedbackClass = ref('')
const revealedClues = ref<string[]>([])

const today = ref<{ date: string; total_questions: number; categories: string[]; top3: Array<{ player_name: string; score: number }> }>({
  date: '', total_questions: 3, categories: [], top3: [],
})

const state = ref<any>({})
const result = ref<any>({})

const diffLabel = computed(() => {
  const map: Record<number, string> = { 1: '★', 2: '★★', 3: '★★★', 4: '★★★★', 5: '★★★★★' }
  return map[state.value.difficulty] || '★★★'
})

const cluesExhausted = computed(() => {
  return state.value.clue_index >= (state.value.total_clues || 1) - 1
})

onMounted(async () => {
  try {
    today.value = await api.dailyToday()
  } catch (e) {
    console.error('加载今日概览失败', e)
  }
})

async function startGame() {
  loading.value = true
  try {
    const s = await api.dailyStart(user.nickname || '匿名玩家')
    state.value = s
    revealedClues.value = [s.clue]
    phase.value = 'playing'
    feedback.value = ''
  } finally {
    loading.value = false
  }
}

async function revealClue() {
  loading.value = true
  try {
    const c = await api.dailyClue(state.value.session_id)
    revealedClues.value.push(c.clue)
    state.value = { ...state.value, clue_index: c.clue_index, total_clues: c.total_clues }
    feedback.value = ''
  } finally {
    loading.value = false
  }
}

async function submitGuess() {
  const answer = guessInput.value.trim()
  if (!answer || loading.value) return
  loading.value = true
  try {
    const r = await api.dailyGuess(state.value.session_id, answer)
    if (r.correct) {
      feedback.value = `✦ 猜中！${r.answer}　+${r.points} 分`
      feedbackClass.value = 'good'
    } else if (r.revealed_clue) {
      feedback.value = `💀 此名非也……新线索已曝光`
      feedbackClass.value = 'bad'
      revealedClues.value.push(r.revealed_clue)
    } else {
      feedback.value = `💀 ${r.answer} 未被识破，进入下一题`
      feedbackClass.value = 'bad'
    }
    guessInput.value = ''

    if (r.advanced) {
      // 进入下一题
      state.value = { ...state.value, ...stripProgress(r) }
      revealedClues.value = r.clue ? [r.clue] : []
      setTimeout(() => (feedback.value = ''), 800)
    } else {
      state.value = { ...state.value, ...stripProgress(r) }
    }

    if (r.finished) {
      const fin = await api.dailyFinish(state.value.session_id, user.nickname || '匿名玩家')
      result.value = fin
      phase.value = 'result'
    }
  } finally {
    loading.value = false
  }
}

function stripProgress(r: any) {
  const { clue, clue_index, total_clues, question_index, category, finished } = r
  return { clue, clue_index, total_clues, question_index, category, finished }
}

function copyShare() {
  const r = result.value
  const text = `📅 猜猜TA是谁·每日挑战 ${r.date}\n🏆 ${r.total_score}分 · 第${r.rank}名/${r.total_players}人\n` +
    r.results.map((x: any) => `${x.correct ? '★'.repeat(x.stars) : '✗'} ${x.name} ${x.correct ? `+${x.score}` : ''}`).join('\n')
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text)
    feedback.value = ''
    alert('战绩已复制，去炫耀吧！')
  }
}

function backHome() {
  router.push('/')
}
</script>

<style scoped>
.daily {
  min-height: 100vh;
  background: var(--diablo-bg);
  color: var(--diablo-fg);
  padding: 24px 16px 48px;
  font-family: var(--font-sans);
}

.daily-header {
  text-align: center;
  margin-bottom: 24px;
}

.daily-sigil {
  font-size: 44px;
}

.daily-title {
  font-family: var(--font-gothic);
  color: var(--diablo-gold-bright);
  font-size: 28px;
  margin: 8px 0 4px;
  letter-spacing: 4px;
}

.daily-date {
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

.rules {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.rule {
  font-size: 14px;
  line-height: 1.6;
}

.rule b {
  color: var(--diablo-gold);
}

.categories {
  color: var(--diablo-muted);
  font-size: 12px;
  margin-bottom: 12px;
}

.top3 {
  border-top: 1px solid var(--diablo-stone-border);
  padding-top: 12px;
  margin-bottom: 16px;
}

.top3-title {
  color: var(--diablo-gold);
  font-size: 13px;
  margin-bottom: 8px;
}

.top3-row {
  display: flex;
  gap: 8px;
  font-size: 13px;
  padding: 4px 0;
}

.top3-name {
  flex: 1;
}

.top3-score {
  color: var(--diablo-gold-bright);
}

.progress-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 14px;
}

.q-badge {
  color: var(--diablo-gold);
  font-size: 14px;
}

.diff-badge {
  color: var(--diablo-gold-dim);
  font-size: 13px;
  letter-spacing: 2px;
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

.feedback.good {
  color: var(--diablo-gold-bright);
  background: var(--diablo-gold-glow);
}

.feedback.bad {
  color: var(--diablo-blood-bright);
  background: var(--diablo-blood-glow);
}

.result-total {
  text-align: center;
  margin-bottom: 20px;
}

.result-score {
  font-family: var(--font-gothic);
  font-size: 52px;
  color: var(--diablo-gold-bright);
  text-shadow: 0 0 24px var(--diablo-gold-glow);
}

.result-label {
  color: var(--diablo-muted);
  font-size: 13px;
}

.result-rank {
  color: var(--diablo-gold);
  margin-top: 6px;
  font-size: 15px;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
}

.result-row {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--diablo-stone-light);
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  font-size: 14px;
}

.result-row.wrong {
  opacity: 0.6;
}

.result-stars {
  color: var(--diablo-gold);
  width: 72px;
  letter-spacing: 2px;
}

.result-name {
  flex: 1;
  color: var(--diablo-fg-bright);
}

.result-detail {
  color: var(--diablo-muted);
  font-size: 12px;
}

.result-points {
  color: var(--diablo-gold-bright);
  width: 48px;
  text-align: right;
}
</style>
