<template>
  <div class="twenty-q">
    <!-- HUD -->
    <div class="hud">
      <div class="hud-mode">❓ 二十问</div>
      <div class="hud-remaining">
        剩余 <span class="hud-num">{{ remaining }}</span> 问
      </div>
    </div>

    <!-- 问题进度条 -->
    <div class="q-bar-wrap">
      <div class="q-bar">
        <div class="q-bar-fill" :style="{ width: `${usedPct}%` }" />
      </div>
    </div>

    <!-- 对话区 -->
    <div ref="chatRef" class="chat-area">
      <!-- 系统开场白 -->
      <div class="bubble bubble-ai">
        <div class="bubble-label">Oracle</div>
        <div class="bubble-text">我已经想好一个人了！来问吧，只能问是/否问题。</div>
      </div>

      <!-- 对话历史 -->
      <template v-for="(msg, i) in messages" :key="i">
        <div v-if="msg.role === 'player'" class="bubble bubble-player">
          <div class="bubble-text">{{ msg.content }}</div>
        </div>
        <div v-else class="bubble bubble-ai" :class="`emotion-${msg.emotion || 'neutral'}`">
          <div class="bubble-label">Oracle</div>
          <div class="bubble-text">{{ msg.content }}</div>
          <div v-if="msg.answer" class="bubble-tag" :class="tagClass(msg.answer)">
            {{ msg.answer }}
          </div>
        </div>
      </template>

      <!-- 加载中 -->
      <div v-if="loading" class="bubble bubble-ai loading-bubble">
        <div class="bubble-label">Oracle</div>
        <div class="bubble-text">
          <span class="dot-pulse">思考中</span>
        </div>
      </div>
    </div>

    <!-- 快捷问题标签 -->
    <div class="quick-tags">
      <button v-for="tag in quickQuestions" :key="tag" class="qtag" @click="askQuick(tag)">
        {{ tag }}
      </button>
    </div>

    <!-- 输入区 -->
    <div class="input-area">
      <div class="input-frame" :class="{ focus: focused }">
        <div class="input-icon">❓</div>
        <input
          ref="inputRef"
          v-model="questionText"
          class="q-input"
          placeholder="问一个是/否问题..."
          :disabled="loading || remaining <= 0"
          @keydown.enter="ask"
          @focus="focused = true"
          @blur="focused = false"
        />
        <button class="ask-btn" :disabled="loading || !questionText.trim()" @click="ask">提问</button>
      </div>

      <!-- 最终猜测按钮 -->
      <div v-if="messages.length >= 4" class="guess-row">
        <div class="guess-divider"><span>或</span></div>
        <button class="final-guess-btn" @click="showGuessModal = true">
          ⚔ 我要猜了！
        </button>
      </div>
    </div>

    <!-- 猜测弹窗 -->
    <Teleport to="body">
      <div v-if="showGuessModal" class="modal-overlay" @click.self="showGuessModal = false">
        <OrnateFrame class="guess-modal">
          <div class="modal-title">道出那隐藏之名</div>
          <div class="modal-input-wrap">
            <input
              v-model="finalAnswer"
              class="modal-input"
              placeholder="输入人名..."
              @keydown.enter="submitFinalGuess"
            />
          </div>
          <div class="modal-actions">
            <button class="modal-btn confirm" @click="submitFinalGuess">确认献祭</button>
            <button class="modal-btn cancel" @click="showGuessModal = false">取消</button>
          </div>
        </OrnateFrame>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import OrnateFrame from '../components/OrnateFrame.vue'

const router = useRouter()

// 状态
const sessionId = ref('')
const remaining = ref(20)
const loading = ref(false)
const messages = ref<Array<{ role: string; content: string; answer?: string; emotion?: string }>>([])
const questionText = ref('')
const focused = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)
const chatRef = ref<HTMLElement | null>(null)
const showGuessModal = ref(false)
const finalAnswer = ref('')

const maxQuestions = 20
const usedPct = computed(() => ((maxQuestions - remaining.value) / maxQuestions) * 100)

const quickQuestions = [
  '是中国人吗？',
  '还活着吗？',
  '是虚构角色吗？',
  '是古代人吗？',
  '是男性吗？',
  '是科学家吗？',
]

onMounted(async () => {
  loading.value = true
  try {
    const data = await api.startTwentyQ()
    sessionId.value = data.session_id
    remaining.value = data.remaining_questions
  } catch (e: any) {
    alert('启动失败: ' + e.message)
    router.replace('/')
  } finally {
    loading.value = false
  }
})

async function ask() {
  const text = questionText.value.trim()
  if (!text || loading.value || remaining.value <= 0) return

  // 添加玩家消息
  messages.value.push({ role: 'player', content: text })
  questionText.value = ''
  loading.value = true
  await scrollToBottom()

  try {
    const result = await api.askQuestion(sessionId.value, text)
    messages.value.push({
      role: 'ai',
      content: result.response,
      answer: result.answer,
      emotion: result.emotion,
    })
    remaining.value = result.remaining_questions
  } catch (e: any) {
    messages.value.push({
      role: 'ai',
      content: `出错了: ${e.message}`,
      emotion: 'neutral',
    })
  } finally {
    loading.value = false
    await scrollToBottom()
    nextTick(() => inputRef.value?.focus())
  }
}

function askQuick(tag: string) {
  questionText.value = tag
  ask()
}

async function submitFinalGuess() {
  const answer = finalAnswer.value.trim()
  if (!answer || loading.value) return

  showGuessModal.value = false
  loading.value = true

  try {
    const result = await api.finalGuess(sessionId.value, answer)
    // 跳转到结果页（复用渐进揭秘的结果页，传参数）
    router.push({
      path: '/result',
      query: {
        mode: 'twenty-q',
        session: sessionId.value,
      },
    })
  } catch (e: any) {
    messages.value.push({
      role: 'ai',
      content: `猜测失败: ${e.message}`,
      emotion: 'neutral',
    })
    loading.value = false
  }
}

function tagClass(answer: string) {
  if (answer === '是') return 'tag-yes'
  if (answer === '否') return 'tag-no'
  return 'tag-unknown'
}

async function scrollToBottom() {
  await nextTick()
  if (chatRef.value) {
    chatRef.value.scrollTop = chatRef.value.scrollHeight
  }
}
</script>

<style scoped>
.twenty-q {
  display: flex;
  flex-direction: column;
  height: 100vh;
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
.hud-remaining {
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

/* Progress bar */
.q-bar-wrap { padding: 0 4px; margin-bottom: 8px; }
.q-bar {
  height: 4px;
  background: var(--diablo-stone-border);
  border-radius: 2px;
  overflow: hidden;
}
.q-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--diablo-gold-dim), var(--diablo-gold-bright));
  transition: width 0.5s ease;
  box-shadow: 0 0 6px var(--diablo-gold-glow);
}

/* Chat area */
.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Bubbles */
.bubble {
  max-width: 85%;
  padding: 12px 16px;
  animation: bubbleIn 0.3s ease;
}
@keyframes bubbleIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.bubble-ai {
  align-self: flex-start;
  background: linear-gradient(180deg, var(--diablo-stone), var(--diablo-bg-deep));
  border: 1px solid var(--diablo-stone-border);
  border-radius: 2px 12px 12px 12px;
}
.bubble-player {
  align-self: flex-end;
  background: linear-gradient(180deg, var(--diablo-gold-dim), var(--diablo-stone));
  border: 1px solid var(--diablo-gold-dim);
  border-radius: 12px 2px 12px 12px;
}
.bubble-label {
  font-family: var(--font-cinzel);
  font-size: 9px;
  letter-spacing: 2px;
  color: var(--diablo-gold-dim);
  margin-bottom: 4px;
}
.bubble-text {
  font-size: 14px;
  line-height: 1.6;
  color: var(--diablo-fg-bright);
}
.bubble-tag {
  display: inline-block;
  margin-top: 8px;
  padding: 2px 10px;
  font-family: var(--font-cinzel);
  font-size: 10px;
  letter-spacing: 1px;
  border-radius: 2px;
}
.tag-yes { background: rgba(74,106,74,0.2); color: #6AAF6A; border: 1px solid rgba(74,106,74,0.3); }
.tag-no { background: rgba(196,43,43,0.15); color: #C42B2B; border: 1px solid rgba(196,43,43,0.3); }
.tag-unknown { background: rgba(200,168,78,0.1); color: var(--diablo-gold-dim); border: 1px solid rgba(200,168,78,0.2); }

/* Emotion variants */
.emotion-hint { border-color: rgba(74,106,74,0.3); }
.emotion-warning { border-color: rgba(196,43,43,0.2); }

.loading-bubble { opacity: 0.7; }
.dot-pulse::after {
  content: '';
  animation: dots 1.5s infinite;
}
@keyframes dots {
  0% { content: ''; }
  25% { content: '.'; }
  50% { content: '..'; }
  75% { content: '...'; }
}

/* Quick tags */
.quick-tags {
  display: flex;
  gap: 6px;
  padding: 8px 0;
  overflow-x: auto;
  flex-shrink: 0;
}
.qtag {
  white-space: nowrap;
  padding: 6px 12px;
  font-size: 12px;
  color: var(--diablo-muted);
  background: var(--diablo-stone);
  border: 1px solid var(--diablo-stone-border);
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.2s;
}
.qtag:hover {
  color: var(--diablo-gold);
  border-color: var(--diablo-gold-dim);
}

/* Input */
.input-area { padding-bottom: 16px; flex-shrink: 0; }
.input-frame {
  display: flex;
  align-items: center;
  background: linear-gradient(180deg, var(--diablo-stone), var(--diablo-bg-deep));
  border: 1px solid var(--diablo-stone-border);
  transition: border-color 0.3s;
}
.input-frame.focus { border-color: var(--diablo-gold-dim); }
.input-icon {
  padding: 14px 12px;
  border-right: 1px solid var(--diablo-stone-border);
}
.q-input {
  flex: 1;
  padding: 14px;
  background: none;
  border: none;
  font-size: 15px;
  color: var(--diablo-fg-bright);
}
.q-input::placeholder { color: var(--diablo-stone-border); }
.ask-btn {
  padding: 14px 20px;
  border: none;
  font-family: var(--font-cinzel);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 2px;
  background: linear-gradient(180deg, var(--diablo-gold), var(--diablo-gold-dim));
  color: var(--diablo-bg);
  transition: all 0.2s;
}
.ask-btn:hover:not(:disabled) {
  box-shadow: 0 0 12px var(--diablo-gold-glow);
}
.ask-btn:disabled { opacity: 0.4; }

/* Guess section */
.guess-row { margin-top: 12px; }
.guess-divider {
  text-align: center;
  position: relative;
  margin-bottom: 10px;
}
.guess-divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--diablo-stone-border);
}
.guess-divider span {
  position: relative;
  background: var(--diablo-bg);
  padding: 0 12px;
  font-size: 12px;
  color: var(--diablo-muted);
}
.final-guess-btn {
  width: 100%;
  padding: 14px;
  border: 1px solid var(--diablo-blood);
  background: linear-gradient(180deg, rgba(139,26,26,0.15), var(--diablo-bg-deep));
  color: var(--diablo-blood-bright);
  font-family: var(--font-cinzel);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 2px;
  transition: all 0.3s;
}
.final-guess-btn:hover {
  background: linear-gradient(180deg, rgba(196,43,43,0.2), var(--diablo-bg-deep));
  box-shadow: 0 0 16px var(--diablo-blood-glow);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}
.guess-modal {
  padding: 28px 24px;
  width: 100%;
  max-width: 360px;
  text-align: center;
}
.modal-title {
  font-family: var(--font-cinzel);
  font-size: 16px;
  font-weight: 700;
  color: var(--diablo-gold-bright);
  letter-spacing: 2px;
  margin-bottom: 20px;
}
.modal-input-wrap { margin-bottom: 20px; }
.modal-input {
  width: 100%;
  padding: 14px 16px;
  background: var(--diablo-bg-deep);
  border: 1px solid var(--diablo-stone-border);
  font-size: 16px;
  color: var(--diablo-fg-bright);
  text-align: center;
}
.modal-input:focus {
  border-color: var(--diablo-gold-dim);
  outline: none;
}
.modal-actions {
  display: flex;
  gap: 10px;
}
.modal-btn {
  flex: 1;
  padding: 12px;
  border: none;
  font-family: var(--font-cinzel);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.2s;
}
.modal-btn.confirm {
  background: linear-gradient(180deg, var(--diablo-gold), var(--diablo-gold-dim));
  color: var(--diablo-bg);
}
.modal-btn.confirm:hover { box-shadow: 0 0 12px var(--diablo-gold-glow); }
.modal-btn.cancel {
  background: var(--diablo-stone);
  color: var(--diablo-muted);
  border: 1px solid var(--diablo-stone-border);
}
</style>
