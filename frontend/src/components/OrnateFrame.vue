<template>
  <div class="ornate-frame">
    <div class="corner corner-tl" />
    <div class="corner corner-tr" />
    <div class="corner corner-bl" />
    <div class="corner corner-br" />
    <slot />
  </div>
</template>

<style scoped>
.ornate-frame {
  position: relative;
  background: linear-gradient(180deg, var(--diablo-stone) 0%, var(--diablo-bg-deep) 100%);
  border: 1px solid var(--diablo-stone-border);
}
.ornate-frame::before {
  content: '';
  position: absolute;
  inset: 3px;
  border: 1px solid rgba(200,168,78,0.1);
  pointer-events: none;
}
.corner {
  position: absolute;
  width: 16px;
  height: 16px;
  z-index: 2;
}
.corner::before, .corner::after {
  content: '';
  position: absolute;
  background: var(--diablo-gold-dim);
}
.corner-tl { top: -1px; left: -1px; }
.corner-tl::before { top: 0; left: 0; width: 16px; height: 1px; }
.corner-tl::after { top: 0; left: 0; width: 1px; height: 16px; }
.corner-tr { top: -1px; right: -1px; }
.corner-tr::before { top: 0; right: 0; width: 16px; height: 1px; }
.corner-tr::after { top: 0; right: 0; width: 1px; height: 16px; }
.corner-bl { bottom: -1px; left: -1px; }
.corner-bl::before { bottom: 0; left: 0; width: 16px; height: 1px; }
.corner-bl::after { bottom: 0; left: 0; width: 1px; height: 16px; }
.corner-br { bottom: -1px; right: -1px; }
.corner-br::before { bottom: 0; right: 0; width: 16px; height: 1px; }
.corner-br::after { bottom: 0; right: 0; width: 1px; height: 16px; }
</style>
