<template>
  <div class="home">
    <!-- 用户状态栏 -->
    <div v-if="user.isLoggedIn" class="user-bar" @click="$router.push('/profile')">
      <div class="user-avatar">{{ user.nickname?.[0] || '?' }}</div>
      <div class="user-info">
        <div class="user-name">{{ user.nickname }}</div>
        <div class="user-level">Lv.{{ user.level }} · {{ user.gamesPlayed }}局</div>
      </div>
      <div class="user-xp-bar">
        <div class="user-xp-fill" :style="{ width: `${(user.xpProgress || 0) * 100}%` }" />
      </div>
    </div>
    <div v-else class="register-bar">
      <input v-model="regName" class="reg-input" placeholder="输入昵称开始冒险..." maxlength="10" @keydown.enter="doRegister" />
      <button class="reg-btn" @click="doRegister">启程</button>
    </div>

    <div class="home-skull">💀</div>
    <h1 class="home-title">猜猜TA是谁</h1>
    <div class="home-subtitle">SANCTUM OF NAMES</div>
    <RuneDivider style="max-width: 200px; margin: 0 auto 16px;" />
    <p class="home-desc">
      在黑暗中追寻线索的微光，<br />
      以智慧之刃劈开迷雾，<br />
      唤出那隐藏于阴影之名。
    </p>

    <div class="section-label">单人挑战</div>
    <div class="mode-panel">
      <OrnateFrame v-for="mode in soloModes" :key="mode.id" class="mode-entry" @click="handleModeClick(mode)">
        <div class="mode-glow" />
        <div class="mode-row">
          <div class="mode-sigil">{{ mode.icon }}</div>
          <div class="mode-info">
            <div class="mode-name">{{ mode.name }}</div>
            <div class="mode-desc">{{ mode.desc }}</div>
          </div>
          <div class="mode-seal">进入</div>
        </div>
      </OrnateFrame>
    </div>

    <div class="section-label">多人对战</div>
    <div class="mode-panel">
      <OrnateFrame v-for="mode in battleModes" :key="mode.id" class="mode-entry" @click="handleModeClick(mode)">
        <div class="mode-glow" />
        <div class="mode-row">
          <div class="mode-sigil">{{ mode.icon }}</div>
          <div class="mode-info">
            <div class="mode-name">{{ mode.name }}</div>
            <div class="mode-desc">{{ mode.desc }}</div>
          </div>
          <div class="mode-seal">进入</div>
        </div>
      </OrnateFrame>
    </div>

    <div v-if="stats" class="stats-bar">题库: {{ stats.total }} 题</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'
import { useUserStore } from '../stores/user'
import { api } from '../api/client'
import OrnateFrame from '../components/OrnateFrame.vue'
import RuneDivider from '../components/RuneDivider.vue'

const router = useRouter()
const game = useGameStore()
const user = useUserStore()
const stats = ref<{ total: number } | null>(null)
const regName = ref('')

const soloModes = [
  { id: 'progressive', icon: '🔦', name: '渐进揭秘', desc: '线索逐条出现，越早猜对越厉害', route: '/game' },
  { id: 'twentyq', icon: '❓', name: '二十问', desc: '只问是非题，二十个问题内破案', route: '/twenty-q' },
  { id: 'chain', icon: '🤝', name: '描述接龙', desc: '关键词逐条追加，越少猜对越厉害', route: '/chain' },
]
const battleModes = [
  { id: 'battle', icon: '⚔', name: '实时对战', desc: '与真人玩家同时猜，比谁更快', route: '/battle' },
  { id: 'leaderboard', icon: '🏆', name: '排行榜', desc: '查看全服最强猜名者', route: '/leaderboard' },
]

onMounted(async () => {
  if (user.isLoggedIn) await user.loadProfile()
  try { stats.value = await api.getQuestionStats() } catch (e) {}
})

async function doRegister() {
  if (!regName.value.trim()) return
  await user.register(regName.value.trim())
}

async function handleModeClick(mode: any) {
  if (mode.id === 'progressive') {
    await game.startGame('normal')
    if (!game.error) router.push('/game')
  } else {
    router.push(mode.route)
  }
}
</script>

<style scoped>
.home { display: flex; flex-direction: column; justify-content: center; min-height: 100vh; text-align: center; position: relative; z-index: 1; }

/* User bar */
.user-bar { display: flex; align-items: center; gap: 10px; padding: 10px 12px; background: var(--diablo-stone); border: 1px solid var(--diablo-stone-border); margin-bottom: 20px; cursor: pointer; transition: border-color 0.2s; }
.user-bar:hover { border-color: var(--diablo-gold-dim); }
.user-avatar { width: 32px; height: 32px; border-radius: 50%; border: 1.5px solid var(--diablo-gold); display: flex; align-items: center; justify-content: center; font-family: var(--font-cinzel); font-size: 14px; font-weight: 700; color: var(--diablo-gold-bright); background: var(--diablo-bg-deep); flex-shrink: 0; }
.user-info { flex: 1; text-align: left; }
.user-name { font-size: 13px; font-weight: 600; color: var(--diablo-fg-bright); }
.user-level { font-size: 10px; color: var(--diablo-muted); }
.user-xp-bar { width: 48px; height: 4px; background: var(--diablo-stone-border); border-radius: 2px; overflow: hidden; }
.user-xp-fill { height: 100%; background: var(--diablo-gold); border-radius: 2px; }

/* Register bar */
.register-bar { display: flex; gap: 8px; margin-bottom: 20px; }
.reg-input { flex: 1; padding: 10px 14px; background: var(--diablo-stone); border: 1px solid var(--diablo-stone-border); color: var(--diablo-fg-bright); font-size: 14px; }
.reg-input:focus { border-color: var(--diablo-gold-dim); outline: none; }
.reg-btn { padding: 10px 20px; font-family: var(--font-cinzel); font-size: 12px; font-weight: 700; letter-spacing: 2px; background: linear-gradient(180deg, var(--diablo-gold), var(--diablo-gold-dim)); color: var(--diablo-bg); border: none; cursor: pointer; }

.home-skull { font-size: 40px; margin-bottom: 8px; filter: drop-shadow(0 0 12px var(--diablo-blood-glow)); }
.home-title { font-family: var(--font-cinzel); font-size: 36px; font-weight: 900; color: var(--diablo-gold-bright); text-shadow: 0 0 20px var(--diablo-gold-glow), 0 2px 4px rgba(0,0,0,0.8); letter-spacing: 3px; margin-bottom: 4px; }
.home-subtitle { font-family: var(--font-gothic); font-size: 13px; color: var(--diablo-muted); letter-spacing: 4px; margin-bottom: 16px; }
.home-desc { font-size: 14px; color: var(--diablo-muted); line-height: 1.8; font-style: italic; margin-bottom: 28px; }
.section-label { font-family: var(--font-cinzel); font-size: 10px; letter-spacing: 4px; text-transform: uppercase; color: var(--diablo-gold-dim); margin-bottom: 10px; margin-top: 8px; }
.mode-panel { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.mode-entry { padding: 18px 20px; cursor: pointer; text-align: left; transition: all 0.3s ease; }
.mode-entry:hover { border-color: var(--diablo-gold-dim); box-shadow: 0 0 16px rgba(200,168,78,0.08); }
.mode-entry:hover .mode-glow { opacity: 1; }
.mode-glow { position: absolute; inset: 0; opacity: 0; background: radial-gradient(ellipse at center, rgba(200,168,78,0.06), transparent 70%); transition: opacity 0.3s; pointer-events: none; }
.mode-row { display: flex; align-items: center; gap: 14px; position: relative; z-index: 1; }
.mode-sigil { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; font-size: 18px; border: 1px solid var(--diablo-gold-dim); background: linear-gradient(135deg, var(--diablo-stone), var(--diablo-bg-deep)); flex-shrink: 0; }
.mode-info { flex: 1; }
.mode-name { font-family: var(--font-cinzel); font-size: 15px; font-weight: 700; color: var(--diablo-fg-bright); letter-spacing: 1px; }
.mode-desc { font-size: 12px; color: var(--diablo-muted); margin-top: 2px; }
.mode-seal { font-family: var(--font-cinzel); font-size: 9px; letter-spacing: 2px; text-transform: uppercase; padding: 3px 10px; border: 1px solid var(--diablo-gold-dim); color: var(--diablo-gold); flex-shrink: 0; }
.stats-bar { margin-top: 16px; font-family: var(--font-cinzel); font-size: 11px; color: var(--diablo-muted); letter-spacing: 2px; }
</style>
