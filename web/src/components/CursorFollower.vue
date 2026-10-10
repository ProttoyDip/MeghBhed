<template>
  <div v-if="enabled" ref="ringRef" class="cursor-ring is-hidden" :class="{ 'is-hover': hover, 'is-down': down }" aria-hidden="true"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { reducedMotion } from '../motion'

// A soft ring that trails the pointer. Mouse/trackpad only; the native cursor stays.
const enabled = window.matchMedia('(pointer: fine)').matches && !reducedMotion
const ringRef = ref(null)
const hover = ref(false)
const down = ref(false)

const INTERACTIVE = 'a, button, [role="button"], [role="slider"], label, select, summary, tr.cursor-pointer, .mb-marker'
// Over these the ring steps aside: the map has its own cursors, text fields need a clear caret
const HIDE = '.maplibregl-canvas, input[type="text"], input[type="search"], textarea'

let x = -100
let y = -100
let tx = -100
let ty = -100
let raf = 0
let seen = false

function loop() {
  x += (tx - x) * 0.2
  y += (ty - y) * 0.2
  if (ringRef.value) ringRef.value.style.transform = `translate3d(${x}px, ${y}px, 0)`
  raf = requestAnimationFrame(loop)
}

function onMove(e) {
  tx = e.clientX
  ty = e.clientY
  if (!seen) {
    x = tx
    y = ty
    seen = true
  }
  const el = e.target instanceof Element ? e.target : null
  const hidden = !!el?.closest(HIDE)
  ringRef.value?.classList.toggle('is-hidden', hidden)
  hover.value = !hidden && !!el?.closest(INTERACTIVE)
}

const onDown = () => (down.value = true)
const onUp = () => (down.value = false)
const onLeave = () => ringRef.value?.classList.add('is-hidden')

onMounted(() => {
  if (!enabled) return
  window.addEventListener('pointermove', onMove, { passive: true })
  window.addEventListener('pointerdown', onDown, { passive: true })
  window.addEventListener('pointerup', onUp, { passive: true })
  document.documentElement.addEventListener('pointerleave', onLeave)
  raf = requestAnimationFrame(loop)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  window.removeEventListener('pointermove', onMove)
  window.removeEventListener('pointerdown', onDown)
  window.removeEventListener('pointerup', onUp)
  document.documentElement.removeEventListener('pointerleave', onLeave)
})
</script>
