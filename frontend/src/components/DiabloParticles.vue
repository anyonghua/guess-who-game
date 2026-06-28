<template>
  <div class="particles">
    <div v-for="i in 6" :key="i" class="particle" :style="{ left: `${10 + i * 15}%`, animationDelay: `${i * 1.3}s`, animationDuration: `${7 + i * 2}s` }" />
  </div>
</template>

<style scoped>
.particles {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}
.particle {
  position: absolute;
  width: 2px;
  height: 2px;
  background: var(--diablo-gold);
  border-radius: 50%;
  opacity: 0;
  animation: float 8s infinite;
}
@keyframes float {
  0% { bottom: -10px; opacity: 0; }
  10% { opacity: 0.5; }
  90% { opacity: 0.5; }
  100% { bottom: 110%; opacity: 0; }
}
</style>
