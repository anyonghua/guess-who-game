<template>
  <div class="game">
    <!-- HUD -->
    <div class="hud-top">
      <div class="hud-left">
        <div class="hud-label">SCORE</div>
        <div class="hud-value">{{ game.score }}</div>
      </div>
      <div class="hud-right">
        <div class="hud-label">STREAK</div>
        <div class="hud-streak" :class="{ active: game.streak > 0 }">{{ game.streak }}</div>
      </div>
    </div>

    <!-- 符文进度 -->
    <div class="rune-slots">
      <div
        v-for="i in game.maxClues"
        :key="i"
        class="rune-slot"
        :class="{ lit: i - 1 < game.clueIndex, now: i - 1 === game.clueIndex }"
      >
        <span class="rune-inner">{{ roman[i - 1] }}</span>
      </div>
    </div>

    <!-- 线索卷轴 -->
    <OrnateFrame class="clue-scroll" :key="game.clueIndex">
      <div class="clue-header">
        <span class="clue-sigil">◆</span>
        <span class="clue-label">线索 {{ roman[game.clueIndex] }}</span>
      </div>
      <div class="clue-body">{{ game.clue }}</div>
      <div class="clue-footer">
        <RuneDivider />
        <div class="rune-text">{{ runeTexts[game.clueIndex] }}</div>
      </div>
    </OrnateFrame>

    <!-- 温度指示器 -->
    <OrnateFrame v-if="temperature" class="blood-orb-wrap">
      <div class="blood-orb" :style="{ boxShadow: `0 0 12px ${temperature.color}40` }" />
      <div class="blood-fill">
        <div class="blood-bar" :style="{ width: `${tempPct}%`, background: temperature.color }" />
      </div>
      <div class="blood-label" :style="{ color: temperature.color }">{{ temperature.label }}</div>
    </OrnateFrame>

    <!-- 加载中 -->
    <div v-if="game.loading" class="loading-text">命运流转中...</div>

    <!-- 错误 -->
    <div v-if="game.error" class="error-text">{{ game.error }}</div>

    <!-- 反馈 -->
    <Transition name="toast">
      <div v-if="toastMsg" class="diablo-toast" :class="toastType">
        {{ toastMsg }}
      </div>
    </Transition>

    <!-- 输入区 -->
    <div class="input-area">
      <div class="input-frame" :class="{ focus: inputFocused }">
        <div class="input-rune">⚔</div>
        <input
          ref="inputRef"
          v-model="guessText"
          class="guess-input"
          placeholder="道出那隐藏之名..."
          autocomplete="off"
          :disabled="game.loading"
          @keydown.enter="handleGuess"
          @focus="inputFocused = true"
          @blur="inputFocused = false"
        />
        <button class="guess-btn" :disabled="game.loading" @click="handleGuess">献祭</button>
      </div>
      <div class="skip-row">
        <button class="skip-link" @click="handleSkip">跳过此线索，承受代价 →</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'
import OrnateFrame from '../components/OrnateFrame.vue'
import RuneDivider from '../components/RuneDivider.vue'

const router = useRouter()
const game = useGameStore()

// 如果没有会话，跳回首页
onMounted(() => {
  if (!game.sessionId) router.replace('/')
})

const guessText = ref('')
const inputFocused = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)
const toastMsg = ref('')
const toastType = ref<'correct' | 'wrong'>('wrong')
const temperature = ref<{ level: number; label: string; color: string } | null>(null)

const roman = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII']
const runeTexts = ['ᚠ ᚢ ᚦ', 'ᚨ ᚱ ᚲ', 'ᚷ ᚹ ᚺ', 'ᚾ ᛁ ᛃ', 'ᛇ ᛈ ᛉ', 'ᛊ ᛏ ᛒ', 'ᛖ ᛗ ᛚ', 'ᛜ ᛞ ᛟ']

const tempPct = computed(() => Math.min(100, (game.clueIndex + 1) / game.maxClues * 100))

function showToast(msg: string, type: 'correct' | 'wrong') {
  toastMsg.value = msg
  toastType.value = type
  setTimeout(() => { toastMsg.value = '' }, 1500)
}

async function handleGuess() {
  const text = guessText.value.trim()
  if (!text || game.loading) return

  const result = await game.submitGuess(text)
  if (!result) return

  if (result.correct) {
    showToast(`✦ 命运已定 +${result.points}`, 'correct')
    setTimeout(() => router.push('/result'), 800)
  } else {
    showToast('💀 邪灵低语：此名非也...', 'wrong')
    if (result.temperature) {
      temperature.value = result.temperature
    }
    // 检查是否线索用完
    if (!result.clue && game.clueIndex >= game.maxClues - 1) {
      setTimeout(() => router.push('/result'), 800)
    }
  }

  guessText.value = ''
  nextTick(() => inputRef.value?.focus())
}

function handleSkip() {
  // 跳过 = 猜一个空答案触发推进
  handleGuess()
}
</script>

<style scoped>
.game {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding-top: 12px;
  position: relative;
  z-index: 1;
}
.hud-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 10px 4px;
}
.hud-left, .hud-right { display: flex; align-items: center; gap: 10px; }
.hud-label {
  font-family: var(--font-cinzel);
  font-size: 10px; letter-spacing: 2px; text-transform: uppercase;
  color: var(--diablo-muted);
}
.hud-value {
  font-family: var(--font-cinzel);
  font-size: 18px; font-weight: 700;
  color: var(--diablo-gold-bright);
  text-shadow: 0 0 10px var(--diablo-gold-glow);
}
.hud-streak {
  font-family: var(--font-cinzel);
  font-size: 16px;
  color: var(--diablo-stone-border);
  transition: color 0.3s;
}
.hud-streak.active {
  color: var(--diablo-blood-bright);
  text-shadow: 0 0 8px var(--diablo-blood-glow);
}
.rune-slots {
  display: flex; justify-content: center; gap: 6px; margin-bottom: 16px;
}
.rune-slot {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid var(--diablo-stone-border);
  background: var(--diablo-bg-deep);
  transform: rotate(45deg); transition: all 0.5s ease;
}
.rune-inner {
  transform: rotate(-45deg);
  font-family: var(--font-cinzel);
  font-size: 8px; color: var(--diablo-stone-border);
}
.rune-slot.lit {
  border-color: var(--diablo-gold);
  background: linear-gradient(135deg, var(--diablo-stone), var(--diablo-stone-light));
  box-shadow: 0 0 8px var(--diablo-gold-glow);
}
.rune-slot.lit .rune-inner { color: var(--diablo-gold-bright); }
.rune-slot.now {
  border-color: var(--diablo-gold-bright);
  animation: runePulse 2s infinite;
}
.rune-slot.now .rune-inner { color: var(--diablo-gold-bright); }
@keyframes runePulse {
  0%, 100% { box-shadow: 0 0 8px var(--diablo-gold-glow); }
  50% { box-shadow: 0 0 20px var(--diablo-gold-glow); }
}
.clue-scroll {
  padding: 24px 20px; margin-bottom: 12px;
  animation: scrollReveal 0.6s ease;
}
@keyframes scrollReveal {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
.clue-header {
  display: flex; align-items: center; gap: 10px; margin-bottom: 14px;
}
.clue-sigil {
  font-size: 14px; color: var(--diablo-blood-bright);
  text-shadow: 0 0 8px var(--diablo-blood-glow);
}
.clue-label {
  font-family: var(--font-cinzel);
  font-size: 10px; letter-spacing: 3px; text-transform: uppercase;
  color: var(--diablo-gold-dim);
}
.clue-body {
  font-family: var(--font-cinzel);
  font-size: 17px; font-weight: 400; line-height: 1.8;
  color: var(--diablo-fg-bright);
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}
.clue-footer { margin-top: 14px; text-align: center; }
.rune-text {
  font-family: var(--font-gothic);
  font-size: 11px; color: var(--diablo-stone-border);
  letter-spacing: 6px; margin-top: 6px;
}
.blood-orb-wrap {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px; margin-bottom: 12px;
  animation: scrollReveal 0.4s ease;
}
.blood-orb {
  width: 24px; height: 24px; border-radius: 50%;
  border: 2px solid var(--diablo-blood);
  background: radial-gradient(circle at 40% 35%, var(--diablo-blood-bright), var(--diablo-blood));
  flex-shrink: 0;
}
.blood-fill {
  flex: 1; height: 5px; border-radius: 3px;
  background: var(--diablo-stone-border); overflow: hidden;
}
.blood-bar {
  height: 100%; border-radius: 3px;
  transition: width 0.6s ease, background 0.3s;
}
.blood-label {
  font-family: var(--font-cinzel);
  font-size: 10px; letter-spacing: 1px;
  min-width: 80px; text-align: right; flex-shrink: 0;
}
.loading-text {
  text-align: center; font-family: var(--font-cinzel);
  font-size: 13px; color: var(--diablo-gold-dim);
  animation: pulse 1.5s infinite; margin: 12px 0;
}
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
.error-text {
  text-align: center; font-size: 13px;
  color: var(--diablo-blood-bright); margin: 12px 0;
}
.diablo-toast {
  position: fixed; top: 20px; left: 50%; transform: translateX(-50%);
  padding: 10px 24px; z-index: 200;
  font-family: var(--font-cinzel); font-size: 13px;
  letter-spacing: 1px; border: 1px solid; white-space: nowrap;
}
.diablo-toast.wrong {
  border-color: var(--diablo-blood); color: var(--diablo-blood-bright);
  background: linear-gradient(180deg, rgba(139,26,26,0.2), rgba(11,8,6,0.95));
  box-shadow: 0 4px 20px var(--diablo-blood-glow);
}
.diablo-toast.correct {
  border-color: var(--diablo-gold); color: var(--diablo-gold-bright);
  background: linear-gradient(180deg, rgba(200,168,78,0.15), rgba(11,8,6,0.95));
  box-shadow: 0 4px 20px var(--diablo-gold-glow);
}
.toast-enter-active { animation: toastDown 0.4s ease; }
.toast-leave-active { animation: toastDown 0.3s ease reverse; }
@keyframes toastDown {
  from { opacity: 0; transform: translate(-50%, -12px); }
  to { opacity: 1; transform: translate(-50%, 0); }
}
.input-area { margin-top: auto; padding-bottom: 24px; }
.input-frame {
  display: flex; align-items: center;
  background: linear-gradient(180deg, var(--diablo-stone), var(--diablo-bg-deep));
  border: 1px solid var(--diablo-stone-border);
  margin-bottom: 12px; transition: border-color 0.3s, box-shadow 0.3s;
}
.input-frame.focus {
  border-color: var(--diablo-gold-dim);
  box-shadow: 0 0 12px rgba(200,168,78,0.1);
}
.input-rune {
  padding: 14px 12px; font-size: 14px; color: var(--diablo-gold-dim);
  border-right: 1px solid var(--diablo-stone-border);
}
.guess-input {
  flex: 1; padding: 14px 14px; background: none; border: none;
  font-size: 16px; font-weight: 300; color: var(--diablo-fg-bright);
}
.guess-input::placeholder { color: var(--diablo-stone-border); }
.guess-btn {
  padding: 14px 20px; border: none;
  font-family: var(--font-cinzel); font-size: 12px; font-weight: 700;
  letter-spacing: 2px; text-transform: uppercase;
  background: linear-gradient(180deg, var(--diablo-gold), var(--diablo-gold-dim));
  color: var(--diablo-bg); transition: all 0.2s;
}
.guess-btn:hover:not(:disabled) {
  background: linear-gradient(180deg, var(--diablo-gold-bright), var(--diablo-gold));
  box-shadow: 0 0 12px var(--diablo-gold-glow);
}
.guess-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.skip-row { text-align: center; }
.skip-link {
  font-family: var(--font-cinzel); font-size: 11px;
  color: var(--diablo-muted); background: none; border: none;
  letter-spacing: 1px; transition: color 0.2s;
}
.skip-link:hover { color: var(--diablo-gold); }
</style>
