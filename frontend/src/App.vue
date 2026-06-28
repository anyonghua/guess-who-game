<template>
  <div class="app-root">
    <DiabloParticles />
    <router-view />
  </div>
</template>

<script setup lang="ts">
import DiabloParticles from './components/DiabloParticles.vue'
</script>

<style>
.app-root {
  max-width: 420px;
  margin: 0 auto;
  min-height: 100vh;
  padding: 0 16px;
  position: relative;
  z-index: 1;
}
</style>
