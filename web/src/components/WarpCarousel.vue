<template>
  <div
    ref="wrap"
    role="region"
    aria-roledescription="carousel"
    :aria-label="ariaLabel"
    tabindex="0"
    class="relative aspect-[5/4] w-full cursor-grab touch-pan-y select-none overflow-hidden rounded-sm outline-none focus-visible:ring-2 focus-visible:ring-water"
  >
    <canvas ref="canvas" aria-hidden="true" class="absolute inset-0 block h-full w-full" />
    <div aria-live="polite" class="sr-only">{{ liveText }}</div>
  </div>
</template>

<script setup>
// Warp Carousel by Louis Studios (https://studios.lou15.com/), ported from React; the engine is in ./warp/engine.js.
// It only starts once it is near the screen, pauses off screen, and rebuilds when the theme or the cards change.
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { createWarpCarousel } from './warp/engine'
import { theme } from '../theme'

const props = defineProps({
  cards: { type: Array, required: true },
  autoplay: { type: Boolean, default: true },
  interval: { type: Number, default: 3.6667 },
  step: { type: Number, default: 2 },
  warp: { type: Number, default: 1 },
  ariaLabel: { type: String, default: 'Stat cards' },
})

const wrap = ref(null)
const canvas = ref(null)
const index = ref(0)
let instance = null
let near = false
let io = null

const front = computed(() => props.cards[index.value % props.cards.length])
const liveText = computed(() => (front.value ? `${front.value.title.replace('\n', ' ')}: ${front.value.value}${front.value.unit || ''}. ${front.value.footer || ''}` : ''))

const motion = typeof window !== 'undefined' && window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null

function mount() {
  instance?.destroy()
  instance = null
  if (!near || !wrap.value || !canvas.value || !props.cards.length) return
  const css = getComputedStyle(document.documentElement)
  instance = createWarpCarousel(wrap.value, canvas.value, {
    cards: props.cards,
    startIndex: index.value,
    autoplay: props.autoplay,
    interval: props.interval,
    step: props.step,
    warp: props.warp,
    background: css.getPropertyValue('--color-paper').trim() || '#f6f8fa',
    font: getComputedStyle(document.body).fontFamily,
    reduced: () => !!motion?.matches,
    onIndexChange: (i) => (index.value = i),
  })
}

onMounted(() => {
  io = new IntersectionObserver(
    (entries) => {
      if (near || !entries.some((e) => e.isIntersecting)) return
      near = true
      io.disconnect()
      mount()
    },
    { rootMargin: '300px 0px' },
  )
  io.observe(wrap.value)
})

// the stage colour follows the theme; wait a frame so the new CSS variables are in place
watch(theme, () => requestAnimationFrame(mount))
watch(() => props.cards, mount)

onBeforeUnmount(() => {
  io?.disconnect()
  instance?.destroy()
  instance = null
})
</script>
