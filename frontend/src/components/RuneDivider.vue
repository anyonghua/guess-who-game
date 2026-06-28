<template>
  <div class="rune-divider">
    <div class="rune-line" />
    <div class="rune-diamond" />
    <div class="rune-line" />
  </div>
</template>

<style scoped>
.rune-divider {
  display: flex;
  align-items: center;
  gap: 8px;
}
.rune-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--diablo-gold-dim), transparent);
}
.rune-diamond {
  width: 6px;
  height: 6px;
  transform: rotate(45deg);
  background: var(--diablo-gold-dim);
  border: 1px solid var(--diablo-gold);
}
</style>
