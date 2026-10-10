<template>
  <span ref="el" class="num">{{ text }}</span>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { n } from '../i18n'
import { onVisible, reducedMotion } from '../motion'

// Counts from 0 to `value` the first time it scrolls into view
const props = defineProps({
  value: { type: Number, required: true },
  decimals: { type: Number, default: 0 },
  duration: { type: Number, default: 1400 },
})

const el = ref(null)
const shown = ref(reducedMotion ? props.value : 0)
const text = computed(() => n(shown.value, { minimumFractionDigits: props.decimals, maximumFractionDigits: props.decimals }))

let raf = 0
let stop = () => {}
let done = reducedMotion

// e.g. the language switch turns 1.28 M into 12.8 লাখ
watch(() => props.value, (v) => {
  if (done) shown.value = v
})
const easeOutExpo = (p) => (p === 1 ? 1 : 1 - 2 ** (-10 * p))

onMounted(() => {
  if (reducedMotion) return
  stop = onVisible(el.value, () => {
    const start = performance.now()
    const tick = (now) => {
      const p = Math.min(1, (now - start) / props.duration)
      shown.value = props.value * easeOutExpo(p)
      if (p < 1) raf = requestAnimationFrame(tick)
      else done = true
    }
    raf = requestAnimationFrame(tick)
  })
})

onBeforeUnmount(() => {
  stop()
  cancelAnimationFrame(raf)
})
</script>
