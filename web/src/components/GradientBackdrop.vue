<template>
  <!-- SOFFIT GRADIENT (trial): animated backdrop + a page-colour fade that keeps text readable -->
  <div class="pointer-events-none absolute inset-0" :class="{ 'fade-bottom': fadeBottom }" aria-hidden="true">
    <SoffitGradient />
    <div class="absolute inset-0" :class="`scrim-${fade}`"></div>
  </div>
</template>

<script setup>
import SoffitGradient from './SoffitGradient.vue'

// side:   text on the left (top on phones), gradient shows on the right
// radial: text in the centre column, gradient shows around the edges
// fadeBottom: dissolve into the page before the bottom edge (e.g. above a chat input)
defineProps({
  fade: { type: String, default: 'side' },
  fadeBottom: { type: Boolean, default: false },
})
</script>

<style scoped>
.fade-bottom {
  -webkit-mask-image: linear-gradient(to bottom, #000 0, #000 calc(100% - 300px), transparent calc(100% - 140px));
  mask-image: linear-gradient(to bottom, #000 0, #000 calc(100% - 300px), transparent calc(100% - 140px));
}
.scrim-side {
  background: linear-gradient(
    to bottom,
    var(--color-paper) 55%,
    color-mix(in oklab, var(--color-paper) 70%, transparent) 70%,
    transparent
  );
}
.scrim-radial {
  background: radial-gradient(
    ellipse 120% 70% at 50% 35%,
    var(--color-paper) 45%,
    color-mix(in oklab, var(--color-paper) 70%, transparent) 72%,
    transparent
  );
}
@media (min-width: 1024px) {
  .scrim-side {
    background: linear-gradient(
      to right,
      var(--color-paper) 30%,
      color-mix(in oklab, var(--color-paper) 70%, transparent) 45%,
      transparent 75%
    );
  }
  .scrim-radial {
    background: radial-gradient(
      ellipse 62% 75% at 50% 35%,
      var(--color-paper) 45%,
      color-mix(in oklab, var(--color-paper) 70%, transparent) 72%,
      transparent
    );
  }
}
</style>
