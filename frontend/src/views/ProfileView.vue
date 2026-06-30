<template>
  <div class="profile">
    <!-- 头部 -->
    <div class="profile-header">
      <div class="avatar">{{ user.nickname?.[0] || '?' }}</div>
      <div class="header-info">
        <div class="nick">{{ user.nickname || '未登录' }}</div>
        <div class="level-badge">Lv.{{ user.level }}</div>
      </div>
      <button class="back-btn" @click="$router.push('/')">←</button>
    </div>

    <!-- 经验条 -->
    <div class="xp-section">
      <div class="xp-bar-wrap">
        <div class="xp-bar" :style="{ width: `${(user.xpProgress || 0) * 100}%` }" />
      </div>
      <div class="xp-text">{{ user.xp }} / {{ user.profile?.xp_for_next || '---' }} XP</div>
    </div>

    <!-- 数据面板 -->
    <div class="stats-grid">
      <OrnateFrame class="stat-card">
        <div class="stat-num">{{ user.gamesPlayed }}</div>
        <div class="stat-label">总局数</div>
      </OrnateFrame>
      <OrnateFrame class="stat-card">
        <div class="stat-num">{{ user.winRate }}%</div>
        <div class="stat-label">胜率</div>
      </OrnateFrame>
      <OrnateFrame class="stat-card">
        <div class="stat-num">{{ user.profile?.best_streak || 0 }}</div>
        <div class="stat-label">最高连击</div>
      </OrnateFrame>
      <OrnateFrame class="stat-card">
        <div class="stat-num">{{ user.profile?.total_score || 0 }}</div>
        <div class="stat-label">总得分</div>
      </OrnateFrame>
    </div>

    <!-- 成就列表 -->
    <div class="section-title">成就</div>
    <div class="achievements-grid">
      <div v-for="(ach, key) in achievements" :key="key" class="ach-item" :class="{ unlocked: isUnlocked(key) }">
        <div class="ach-icon">{{ ach.icon }}</div>
        <div class="ach-name">{{ ach.name }}</div>
        <div class="ach-desc">{{ ach.desc }}</div>
      </div>
    </div>

    <!-- 等级称号 -->
    <div class="section-title">等级称号</div>
    <div class="titles-list">
      <div v-for="(title, i) in titles" :key="i" class="title-item" :class="{ active: user.level >= i + 1 }">
        <span class="title-level">Lv.{{ i + 1 }}</span>
        <span class="title-name">{{ title }}</span>
        <span v-if="user.level >= i + 1" class="title-check">✓</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import { api } from '../api/client'
import OrnateFrame from '../components/OrnateFrame.vue'

const user = useUserStore()
const achievements = ref<Record<string, any>>({})
const titles = ['路人甲', '线索猎人', '人名百科', '读心术士', '猜神降临',
                '知识领主', '暗影行者', '谜题征服者', '名字先知', '全知之眼']

function isUnlocked(key: string) {
  return (user.profile?.achievements || []).includes(key)
}

onMounted(async () => {
  await user.loadProfile()
  try {
    const data = await api.getAchievements()
    achievements.value = data.achievements
  } catch (e) {}
})
</script>

<style scoped>
.profile { min-height: 100vh; position: relative; z-index: 1; padding-top: 12px; }
.profile-header { display: flex; align-items: center; gap: 14px; margin-bottom: 20px; }
.avatar { width: 48px; height: 48px; border-radius: 50%; border: 2px solid var(--diablo-gold); display: flex; align-items: center; justify-content: center; font-family: var(--font-cinzel); font-size: 20px; font-weight: 700; color: var(--diablo-gold-bright); background: var(--diablo-stone); }
.header-info { flex: 1; }
.nick { font-family: var(--font-cinzel); font-size: 16px; font-weight: 700; color: var(--diablo-fg-bright); }
.level-badge { font-family: var(--font-cinzel); font-size: 11px; color: var(--diablo-gold); letter-spacing: 1px; margin-top: 2px; }
.back-btn { font-size: 18px; color: var(--diablo-muted); background: none; border: none; cursor: pointer; }

.xp-section { margin-bottom: 20px; }
.xp-bar-wrap { height: 6px; background: var(--diablo-stone-border); border-radius: 3px; overflow: hidden; margin-bottom: 6px; }
.xp-bar { height: 100%; background: linear-gradient(90deg, var(--diablo-gold-dim), var(--diablo-gold-bright)); border-radius: 3px; transition: width 0.5s ease; box-shadow: 0 0 6px var(--diablo-gold-glow); }
.xp-text { font-family: var(--font-cinzel); font-size: 10px; color: var(--diablo-muted); text-align: right; }

.stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 24px; }
.stat-card { padding: 16px; text-align: center; }
.stat-num { font-family: var(--font-cinzel); font-size: 24px; font-weight: 700; color: var(--diablo-gold-bright); text-shadow: 0 0 8px var(--diablo-gold-glow); }
.stat-label { font-size: 11px; color: var(--diablo-muted); margin-top: 4px; }

.section-title { font-family: var(--font-cinzel); font-size: 11px; letter-spacing: 3px; text-transform: uppercase; color: var(--diablo-gold-dim); margin-bottom: 12px; }

.achievements-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 24px; }
.ach-item { padding: 12px; background: var(--diablo-stone); border: 1px solid var(--diablo-stone-border); text-align: center; opacity: 0.4; transition: all 0.3s; }
.ach-item.unlocked { opacity: 1; border-color: var(--diablo-gold-dim); }
.ach-icon { font-size: 24px; margin-bottom: 4px; }
.ach-name { font-size: 12px; font-weight: 600; color: var(--diablo-fg-bright); }
.ach-desc { font-size: 10px; color: var(--diablo-muted); margin-top: 2px; }

.titles-list { display: flex; flex-direction: column; gap: 4px; padding-bottom: 40px; }
.title-item { display: flex; align-items: center; gap: 10px; padding: 10px 14px; background: var(--diablo-stone); border: 1px solid var(--diablo-stone-border); opacity: 0.3; transition: all 0.3s; }
.title-item.active { opacity: 1; }
.title-level { font-family: var(--font-cinzel); font-size: 10px; color: var(--diablo-muted); width: 32px; }
.title-name { flex: 1; font-size: 13px; color: var(--diablo-fg-bright); }
.title-check { color: var(--diablo-gold); font-size: 14px; }
</style>
