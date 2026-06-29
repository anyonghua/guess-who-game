<template>
  <div class="battle">
    <!-- 匹配等待 -->
    <div v-if="state === 'idle'" class="match-screen">
      <div class="match-icon">⚔</div>
      <h2 class="match-title">实时对战</h2>
      <p class="match-desc">与另一位玩家同时猜人名，比谁更快更准</p>
      <div class="match-name-row">
        <input v-model="playerName" class="name-input" placeholder="输入你的昵称..." maxlength="10" />
      </div>
      <button class="match-btn" @click="findMatch">开始匹配</button>
    </div>

    <!-- 匹配中 -->
    <div v-if="state === 'waiting'" class="match-screen">
      <div class="match-spinner">⚔</div>
      <h2 class="match-title">正在匹配对手...</h2>
      <p class="match-desc">{{ waitingMsg }}</p>
      <button class="cancel-btn" @click="cancelMatch">取消</button>
    </div>

    <!-- 对战中 -->
    <div v-if="state === 'battle'" class="battle-screen">
      <!-- 顶部信息 -->
      <div class="battle-hud">
        <div class="player-info you">
          <div class="player-name">{{ playerName }}</div>
          <div class="player-score">{{ myScore }}</div>
        </div>
        <div class="round-info">
          <div class="round-num">第 {{ roundNum }} / {{ maxRounds }} 轮</div>
          <div class="vs-badge">VS</div>
        </div>
        <div class="player-info opponent">
          <div class="player-name">{{ opponentName }}</div>
          <div class="player-score">{{ opponentScore }}</div>
        </div>
      </div>

      <!-- 线索 -->
      <OrnateFrame class="clue-card">
        <div class="clue-header">
          <span class="clue-sigil">◆</span>
          <span class="clue-label">线索 {{ roman[clueIndex] || clueIndex + 1 }}</span>
        </div>
        <div class="clue-body">{{ currentClue }}</div>
      </OrnateFrame>

      <!-- 反馈 -->
      <Transition name="toast">
        <div v-if="battleMsg" class="battle-toast" :class="battleMsgType">
          {{ battleMsg }}
        </div>
      </Transition>

      <!-- 输入 -->
      <div class="battle-input-area">
        <div class="input-frame">
          <input
            ref="inputRef"
            v-model="guessText"
            class="battle-input"
            placeholder="快！猜猜TA是谁..."
            @keydown.enter="submitGuess"
          />
          <button class="submit-btn" :disabled="!guessText.trim()" @click="submitGuess">猜！</button>
        </div>
        <button class="skip-btn" @click="skipClue">跳过线索</button>
      </div>
    </div>

    <!-- 结束 -->
    <div v-if="state === 'result'" class="result-screen">
      <div class="result-icon" :class="battleResult">
        {{ battleResult === 'win' ? '🏆' : battleResult === 'lose' ? '💀' : '🤝' }}
      </div>
      <h2 class="result-title">
        {{ battleResult === 'win' ? '胜利！' : battleResult === 'lose' ? '惜败...' : '平局' }}
      </h2>
      <div class="result-answer">答案是：{{ finalAnswer }}</div>
      <div class="result-scores">
        <div class="rs-item you">
          <div class="rs-name">{{ playerName }}</div>
          <div class="rs-score">{{ myScore }}</div>
        </div>
        <div class="rs-vs">VS</div>
        <div class="rs-item opp">
          <div class="rs-name">{{ opponentName }}</div>
          <div class="rs-score">{{ opponentScore }}</div>
        </div>
      </div>
      <button class="again-btn" @click="backToIdle">再来一局</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { connectSocket, disconnectSocket } from '../api/socket'
import OrnateFrame from '../components/OrnateFrame.vue'
import type { Socket } from 'socket.io-client'

const state = ref<'idle' | 'waiting' | 'battle' | 'result'>('idle')
const playerName = ref('无名者')
const opponentName = ref('对手')
const myScore = ref(0)
const opponentScore = ref(0)
const currentClue = ref('')
const clueIndex = ref(0)
const roundNum = ref(1)
const maxRounds = ref(5)
const guessText = ref('')
const waitingMsg = ref('')
const battleMsg = ref('')
const battleMsgType = ref<'correct' | 'wrong' | 'info'>('info')
const battleResult = ref<'win' | 'lose' | 'draw'>('lose')
const finalAnswer = ref('')
const inputRef = ref<HTMLInputElement | null>(null)

const roman = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII']
let socket: Socket | null = null

onMounted(() => {
  socket = connectSocket()

  socket.on('connected', () => {})
  socket.on('waiting', (data: any) => { waitingMsg.value = data.message })
  socket.on('match_cancelled', () => { state.value = 'idle' })

  socket.on('battle_start', (data: any) => {
    state.value = 'battle'
    opponentName.value = data.opponent
    currentClue.value = data.clue
    clueIndex.value = data.clue_index
    roundNum.value = data.round_num
    maxRounds.value = data.max_rounds
    myScore.value = 0
    opponentScore.value = 0
    showMsg('对战开始！', 'info')
    nextTick(() => inputRef.value?.focus())
  })

  socket.on('round_result', (data: any) => {
    myScore.value = data.scores[Object.keys(data.scores).find(k => k !== socket?.id) || ''] || 0
    // 更新双方分数
    for (const [sid, score] of Object.entries(data.scores)) {
      if (sid === socket?.id) myScore.value = score as number
      else opponentScore.value = score as number
    }
    if (data.is_you) {
      showMsg(`✦ 猜对了！+${data.points}`, 'correct')
    } else {
      showMsg(`${data.correct_player} 先猜对了：${data.answer}`, 'wrong')
    }
  })

  socket.on('new_round', (data: any) => {
    roundNum.value = data.round_num
    currentClue.value = data.clue
    clueIndex.value = data.clue_index
    guessText.value = ''
    showMsg(`第 ${data.round_num} 轮开始！`, 'info')
    nextTick(() => inputRef.value?.focus())
  })

  socket.on('wrong_answer', () => {
    showMsg('不对！再想想...', 'wrong')
  })

  socket.on('next_clue', (data: any) => {
    currentClue.value = data.clue
    clueIndex.value = data.clue_index
  })

  socket.on('battle_end', (data: any) => {
    state.value = 'result'
    battleResult.value = data.result
    myScore.value = data.your_score
    opponentScore.value = data.opponent_score
    opponentName.value = data.opponent_name
    finalAnswer.value = data.answer
  })

  socket.on('opponent_left', () => {
    showMsg('对手已离开', 'info')
    state.value = 'result'
    battleResult.value = 'win'
  })

  socket.on('error', (data: any) => {
    showMsg(data.message, 'wrong')
  })
})

onUnmounted(() => {
  disconnectSocket()
})

function findMatch() {
  socket?.emit('find_match', { name: playerName.value || '无名者' })
  state.value = 'waiting'
  waitingMsg.value = '正在匹配对手...'
}

function cancelMatch() {
  socket?.emit('cancel_match')
  state.value = 'idle'
}

function submitGuess() {
  const text = guessText.value.trim()
  if (!text) return
  socket?.emit('submit_battle_guess', { answer: text })
  guessText.value = ''
}

function skipClue() {
  socket?.emit('next_battle_clue')
}

function backToIdle() {
  state.value = 'idle'
  guessText.value = ''
}

function showMsg(msg: string, type: 'correct' | 'wrong' | 'info') {
  battleMsg.value = msg
  battleMsgType.value = type
  setTimeout(() => { battleMsg.value = '' }, 2000)
}
</script>

<style scoped>
.battle { display: flex; flex-direction: column; min-height: 100vh; position: relative; z-index: 1; }

/* Match screen */
.match-screen { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; text-align: center; }
.match-icon { font-size: 56px; margin-bottom: 16px; filter: drop-shadow(0 0 16px var(--diablo-blood-glow)); }
.match-spinner { font-size: 56px; margin-bottom: 16px; animation: spin 2s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.match-title { font-family: var(--font-cinzel); font-size: 28px; font-weight: 900; color: var(--diablo-gold-bright); letter-spacing: 3px; margin-bottom: 8px; }
.match-desc { font-size: 14px; color: var(--diablo-muted); margin-bottom: 24px; }
.match-name-row { margin-bottom: 20px; width: 100%; max-width: 280px; }
.name-input { width: 100%; padding: 12px 16px; background: var(--diablo-stone); border: 1px solid var(--diablo-stone-border); color: var(--diablo-fg-bright); font-size: 15px; text-align: center; }
.name-input:focus { border-color: var(--diablo-gold-dim); outline: none; }
.match-btn { padding: 16px 56px; font-family: var(--font-cinzel); font-size: 14px; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; background: linear-gradient(180deg, var(--diablo-gold), var(--diablo-gold-dim)); color: var(--diablo-bg); border: none; cursor: pointer; transition: all 0.2s; }
.match-btn:hover { box-shadow: 0 0 20px var(--diablo-gold-glow); }
.cancel-btn { padding: 10px 32px; font-size: 12px; color: var(--diablo-muted); background: none; border: 1px solid var(--diablo-stone-border); cursor: pointer; }

/* Battle screen */
.battle-screen { display: flex; flex-direction: column; min-height: 100vh; }
.battle-hud { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid var(--diablo-stone-border); margin-bottom: 16px; }
.player-info { text-align: center; flex: 1; }
.player-name { font-size: 12px; color: var(--diablo-muted); margin-bottom: 2px; }
.player-score { font-family: var(--font-cinzel); font-size: 24px; font-weight: 700; }
.you .player-score { color: var(--diablo-gold-bright); text-shadow: 0 0 10px var(--diablo-gold-glow); }
.opponent .player-score { color: var(--diablo-blood-bright); text-shadow: 0 0 10px var(--diablo-blood-glow); }
.round-info { text-align: center; }
.round-num { font-family: var(--font-cinzel); font-size: 10px; color: var(--diablo-muted); letter-spacing: 1px; }
.vs-badge { font-family: var(--font-cinzel); font-size: 16px; font-weight: 900; color: var(--diablo-gold-dim); letter-spacing: 4px; }

.clue-card { padding: 24px 20px; margin-bottom: 16px; }
.clue-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.clue-sigil { color: var(--diablo-blood-bright); text-shadow: 0 0 8px var(--diablo-blood-glow); }
.clue-label { font-family: var(--font-cinzel); font-size: 10px; letter-spacing: 3px; color: var(--diablo-gold-dim); }
.clue-body { font-family: var(--font-cinzel); font-size: 17px; line-height: 1.8; color: var(--diablo-fg-bright); }

.battle-toast { position: fixed; top: 20px; left: 50%; transform: translateX(-50%); padding: 10px 24px; z-index: 200; font-family: var(--font-cinzel); font-size: 13px; letter-spacing: 1px; border: 1px solid; white-space: nowrap; }
.battle-toast.correct { border-color: var(--diablo-gold); color: var(--diablo-gold-bright); background: linear-gradient(180deg, rgba(200,168,78,0.15), rgba(11,8,6,0.95)); box-shadow: 0 4px 20px var(--diablo-gold-glow); }
.battle-toast.wrong { border-color: var(--diablo-blood); color: var(--diablo-blood-bright); background: linear-gradient(180deg, rgba(139,26,26,0.2), rgba(11,8,6,0.95)); box-shadow: 0 4px 20px var(--diablo-blood-glow); }
.battle-toast.info { border-color: var(--diablo-stone-border); color: var(--diablo-muted); background: var(--diablo-bg-deep); }
.toast-enter-active { animation: toastDown 0.4s ease; }
.toast-leave-active { animation: toastDown 0.3s ease reverse; }
@keyframes toastDown { from { opacity: 0; transform: translate(-50%, -12px); } to { opacity: 1; transform: translate(-50%, 0); } }

.battle-input-area { margin-top: auto; padding-bottom: 24px; }
.input-frame { display: flex; align-items: center; background: linear-gradient(180deg, var(--diablo-stone), var(--diablo-bg-deep)); border: 1px solid var(--diablo-stone-border); margin-bottom: 10px; }
.battle-input { flex: 1; padding: 14px; background: none; border: none; font-size: 16px; color: var(--diablo-fg-bright); }
.battle-input::placeholder { color: var(--diablo-stone-border); }
.submit-btn { padding: 14px 24px; border: none; font-family: var(--font-cinzel); font-size: 14px; font-weight: 700; letter-spacing: 2px; background: linear-gradient(180deg, var(--diablo-blood-bright), var(--diablo-blood)); color: #fff; cursor: pointer; transition: all 0.2s; }
.submit-btn:hover:not(:disabled) { box-shadow: 0 0 12px var(--diablo-blood-glow); }
.submit-btn:disabled { opacity: 0.4; }
.skip-btn { display: block; margin: 0 auto; font-size: 12px; color: var(--diablo-muted); background: none; border: none; cursor: pointer; }

/* Result screen */
.result-screen { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; text-align: center; animation: fadeUp 0.6s ease; }
@keyframes fadeUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.result-icon { font-size: 64px; margin-bottom: 16px; }
.result-title { font-family: var(--font-cinzel); font-size: 28px; font-weight: 900; letter-spacing: 3px; margin-bottom: 8px; }
.result-title { color: var(--diablo-gold-bright); text-shadow: 0 0 20px var(--diablo-gold-glow); }
.result-answer { font-size: 14px; color: var(--diablo-muted); margin-bottom: 28px; }
.result-scores { display: flex; align-items: center; gap: 24px; margin-bottom: 32px; }
.rs-item { text-align: center; }
.rs-name { font-size: 12px; color: var(--diablo-muted); margin-bottom: 4px; }
.rs-score { font-family: var(--font-cinzel); font-size: 36px; font-weight: 900; }
.you .rs-score { color: var(--diablo-gold-bright); text-shadow: 0 0 12px var(--diablo-gold-glow); }
.opp .rs-score { color: var(--diablo-blood-bright); }
.rs-vs { font-family: var(--font-cinzel); font-size: 14px; color: var(--diablo-stone-border); letter-spacing: 3px; }
.again-btn { padding: 14px 48px; font-family: var(--font-cinzel); font-size: 12px; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; background: linear-gradient(180deg, var(--diablo-gold), var(--diablo-gold-dim)); color: var(--diablo-bg); border: none; cursor: pointer; transition: all 0.2s; }
.again-btn:hover { box-shadow: 0 0 20px var(--diablo-gold-glow); }
</style>
