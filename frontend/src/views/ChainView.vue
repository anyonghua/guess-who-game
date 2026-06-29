<template>
  <div class="chain">
    <!-- HUD -->
    <div class="hud">
      <div class="hud-mode">🤝 描述接龙</div>
      <div class="hud-info">
        关键词 <span class="hud-num">{{ keywordCount }}</span> / {{ maxKeywords }}
      </div>
    </div>

    <!-- 关键词卡片区 -->
    <div class="cards-area">
      <TransitionGroup name="card" tag="div" class="cards-grid">
        <div
          v-for="(kw, i) in keywords"
          :key="kw + i"
          class="kw-card"
          :class="{ 'card-new': i === keywords.length - 1 && animateNew }"
          :style="{ animationDelay: `${i * 0.08}s` }"
        >
          <div class="kw-card-inner">
            <div class="kw-index">{{ i + 1 }}</div>
            <div class="kw-text">{{ kw }}</div>
          </div>
        </div>
      </TransitionGroup>

      <!-- 追加关键词按钮 -->
      <div v-if="remainingHints > 0 && !gameOver" class="add-card-row">
        <button class="add-card-btn" :disabled="loading" @click="requestHint">
          <span class="add-icon">＋</span>
          <span class="add-text">追加线索 ({{ remainingHints }})</span>
        </button>
      </div>
    </div>

    <!-- 反馈消息 -->
    <Transition name="toast">
      <div v-if="toastMsg" class="diablo-toast" :class="toastType">
        {{ toastMsg }}
      </div>
    </Transition>

    <!-- 输入区 -->
    <div class="input-area">
      <div class="input-frame" :class="{ focus: focused }">
        <div class="input-icon">🗝</div>
        <input
          ref="inputRef"
          v-model="answerText"
          class="chain-input"
          placeholder="根据关键词，猜猜TA是谁..."
          :disabled="loading || gameOver"
          @keydown.enter="submitGuess"
          @focus="focused = true"
          @blur="focused = false"
        />
        <button class="guess-btn" :disabled="loading || !answerText.trim()" @click="submitGuess">
          猜！
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'

const router = useRouter()

const sessionId = ref('')
const keywords = ref<string[]>([])
const keywordCount = ref(0)
const maxKeywords = ref(7)
const remainingHints = ref(0)
const loading = ref(false)
const gameOver = ref(false)
const answerText = ref('')
const focused = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)
const toastMsg = ref('')
const toastType = ref<'correct' | 'wrong'>('wrong')
const animateNew = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const data = await api.startChain()
    sessionId.value = data.session_id
    keywords.value = data.keywords
    keywordCount.value = data.keyword_count
    maxKeywords.value = data.max_keywords
    remainingHints.value = data.remaining_hints
  } catch (e: any) {
    alert('启动失败: ' + e.message)
    router.replace('/')
  } finally {
    loading.value = false
  }
})

async function submitGuess() {
  const text = answerText.value.trim()
  if (!text || loading.value || gameOver.value) return

  loading.value = true
  try {
    const result = await api.chainGuess(sessionId.value, text)

    if (result.correct) {
      showToast(`✦ 命运已定：+${result.score}`, 'correct')
      setTimeout(() => {
        router.push({ path: '/result', query: { mode: 'chain', session: sessionId.value } })
      }, 800)
    } else if (result.game_over) {
      gameOver.value = true
      showToast(`线索已尽，答案是：${result.actual_answer}`, 'wrong')
    } else {
      showToast('💀 不对！新线索浮现...', 'wrong')
      // 更新关键词
      if (result.keywords) {
        keywords.value = result.keywords
      }
      keywordCount.value = result.keyword_count
      remainingHints.value = result.remaining_hints || 0
      // 新关键词动画
      animateNew.value = true
      setTimeout(() => { animateNew.value = false }, 600)
    }
  } catch (e: any) {
    showToast('出错了: ' + e.message, 'wrong')
  } finally {
    loading.value = false
    answerText.value = ''
    nextTick(() => inputRef.value?.focus())
  }
}

async function requestHint() {
  if (loading.value || remainingHints.value <= 0) return

  loading.value = true
  try {
    const result = await api.chainHint(sessionId.value)
    keywords.value = result.keywords
    keywordCount.value = result.keyword_count
    remainingHints.value = result.remaining_hints
    animateNew.value = true
    setTimeout(() => { animateNew.value = false }, 600)
  } catch (e: any) {
    showToast(e.message, 'wrong')
  } finally {
    loading.value = false
  }
}

function showToast(msg: string, type: 'correct' | 'wrong') {
  toastMsg.value = msg
  toastType.value = type
  setTimeout(() => { toastMsg.value = '' }, 2000)
}
</script>

<style scoped>
.chain {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

/* HUD */
.hud {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 4px;
}
.hud-mode {
  font-family: var(--font-cinzel);
  font-size: 12px;
  letter-spacing: 2px;
  color: var(--diablo-muted);
}
.hud-info {
  font-family: var(--font-cinzel);
  font-size: 12px;
  color: var(--diablo-muted);
}
.hud-num {
  font-size: 18px;
  font-weight: 700;
  color: var(--diablo-gold-bright);
  text-shadow: 0 0 10px var(--diablo-gold-glow);
}

/* Cards area */
.cards-area {
  flex: 1;
  padding: 8px 0;
}
.cards-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

/* Keyword card */
.kw-card {
  animation: cardIn 0.4s ease backwards;
}
@keyframes cardIn {
  from { opacity: 0; transform: scale(0.8) translateY(12px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
.kw-card-inner {
  background: linear-gradient(180deg, var(--diablo-stone), var(--diablo-bg-deep));
  border: 1px solid var(--diablo-stone-border);
  padding: 14px 20px;
  min-width: 100px;
  text-align: center;
  position: relative;
  transition: all 0.3s;
}
.kw-card-inner::before {
  content: '';
  position: absolute;
  inset: 2px;
  border: 1px solid rgba(200,168,78,0.06);
  pointer-events: none;
}
.kw-card-inner:hover {
  border-color: var(--diablo-gold-dim);
  box-shadow: 0 0 12px rgba(200,168,78,0.1);
}
.kw-index {
  font-family: var(--font-cinzel);
  font-size: 9px;
  color: var(--diablo-gold-dim);
  letter-spacing: 1px;
  margin-bottom: 6px;
}
.kw-text {
  font-size: 15px;
  font-weight: 500;
  color: var(--diablo-fg-bright);
}
.card-new .kw-card-inner {
  border-color: var(--diablo-gold);
  box-shadow: 0 0 16px var(--diablo-gold-glow);
  animation: cardGlow 0.6s ease;
}
@keyframes cardGlow {
  0% { box-shadow: 0 0 30px var(--diablo-gold-glow); }
  100% { box-shadow: 0 0 8px rgba(200,168,78,0.1); }
}

/* TransitionGroup */
.card-enter-active { animation: cardIn 0.4s ease; }
.card-leave-active { animation: cardIn 0.3s ease reverse; }

/* Add card button */
.add-card-row {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}
.add-card-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: none;
  border: 1px dashed var(--diablo-stone-border);
  color: var(--diablo-muted);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
}
.add-card-btn:hover:not(:disabled) {
  border-color: var(--diablo-gold-dim);
  color: var(--diablo-gold);
}
.add-card-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.add-icon { font-size: 16px; }

/* Toast */
.diablo-toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 24px;
  z-index: 200;
  font-family: var(--font-cinzel);
  font-size: 13px;
  letter-spacing: 1px;
  border: 1px solid;
  white-space: nowrap;
}
.diablo-toast.wrong {
  border-color: var(--diablo-blood);
  color: var(--diablo-blood-bright);
  background: linear-gradient(180deg, rgba(139,26,26,0.2), rgba(11,8,6,0.95));
  box-shadow: 0 4px 20px var(--diablo-blood-glow);
}
.diablo-toast.correct {
  border-color: var(--diablo-gold);
  color: var(--diablo-gold-bright);
  background: linear-gradient(180deg, rgba(200,168,78,0.15), rgba(11,8,6,0.95));
  box-shadow: 0 4px 20px var(--diablo-gold-glow);
}
.toast-enter-active { animation: toastDown 0.4s ease; }
.toast-leave-active { animation: toastDown 0.3s ease reverse; }
@keyframes toastDown {
  from { opacity: 0; transform: translate(-50%, -12px); }
  to { opacity: 1; transform: translate(-50%, 0); }
}

/* Input */
.input-area {
  padding-bottom: 24px;
  flex-shrink: 0;
}
.input-frame {
  display: flex;
  align-items: center;
  background: linear-gradient(180deg, var(--diablo-stone), var(--diablo-bg-deep));
  border: 1px solid var(--diablo-stone-border);
  transition: border-color 0.3s;
}
.input-frame.focus {
  border-color: var(--diablo-gold-dim);
  box-shadow: 0 0 12px rgba(200,168,78,0.1);
}
.input-icon {
  padding: 14px 12px;
  border-right: 1px solid var(--diablo-stone-border);
  font-size: 14px;
}
.chain-input {
  flex: 1;
  padding: 14px;
  background: none;
  border: none;
  font-size: 16px;
  color: var(--diablo-fg-bright);
}
.chain-input::placeholder { color: var(--diablo-stone-border); }
.guess-btn {
  padding: 14px 24px;
  border: none;
  font-family: var(--font-cinzel);
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 2px;
  background: linear-gradient(180deg, var(--diablo-gold), var(--diablo-gold-dim));
  color: var(--diablo-bg);
  transition: all 0.2s;
}
.guess-btn:hover:not(:disabled) {
  background: linear-gradient(180deg, var(--diablo-gold-bright), var(--diablo-gold));
  box-shadow: 0 0 12px var(--diablo-gold-glow);
}
.guess-btn:disabled { opacity: 0.4; }
</style>
