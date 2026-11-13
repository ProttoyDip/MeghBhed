<template>
  <button
    type="button"
    data-slot="theme-toggle"
    :data-state="theme"
    :aria-label="theme === 'dark' ? t('nav.toLight') : t('nav.toDark')"
    :title="theme === 'dark' ? t('nav.toLight') : t('nav.toDark')"
    class="relative isolate inline-flex h-9 w-9 shrink-0 cursor-pointer items-center justify-center overflow-hidden rounded-full border border-rule transition-[filter] hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-water focus-visible:ring-offset-2 focus-visible:ring-offset-paper"
    @click="toggleTheme"
  >
    <span ref="night" aria-hidden="true" data-sky="night" :class="SKY_CLASS" :style="{ background: NIGHT_SKY, opacity: theme === 'dark' ? 1 : 0 }">
      <span
        v-for="(star, i) in STARS"
        :key="i"
        data-star
        class="absolute rounded-full bg-white"
        :style="{ left: `${star.x}%`, top: `${star.y}%`, width: `${star.r * 2}px`, height: `${star.r * 2}px`, opacity: 0.6 }"
      />
    </span>
    <span ref="day" aria-hidden="true" data-sky="day" :class="SKY_CLASS" :style="{ background: DAY_SKY, opacity: theme === 'light' ? 1 : 0 }" />
    <span ref="moon" aria-hidden="true" data-body="moon" :class="[BODY_CLASS, 'text-amber-200 drop-shadow-[0_0_8px_rgba(252,211,77,0.6)]']" :style="resting(MOON, theme === 'dark')">
      <Moon class="size-1/2" fill="currentColor" />
    </span>
    <span ref="sun" aria-hidden="true" data-body="sun" :class="[BODY_CLASS, 'text-orange-400 drop-shadow-[0_0_10px_rgba(251,146,60,0.7)]']" :style="resting(SUN, theme === 'light')">
      <Sun class="size-1/2" />
    </span>
  </button>
</template>

<script setup>
// Sun / moon theme toggle, ported from the React "SunMoonThemeToggle" (from the CCgather header, via 21st.dev).
// The moon sets and the sun rises along one arc below the button, over a night / day sky. The theme itself
// still lives in theme.js (data-theme on <html>, its own 0.35 s colour fade); this only animates the button.
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { Moon, Sun } from 'lucide-vue-next'
import { theme, toggleTheme } from '../theme'
import { t } from '../i18n'

const DURATION = 1740
const MOON = { side: -1, spin: 25 }
const SUN = { side: 1, spin: 120 }
const ARC_RADIUS = 115
const QUARTER_TURN = Math.PI / 2
const KEYFRAME_STEPS = 30
const BODY_CLASS = 'pointer-events-none absolute inset-0 flex items-center justify-center'
const SKY_CLASS = 'pointer-events-none absolute inset-0 -z-10'
const NIGHT_SKY = 'linear-gradient(180deg, #090f2a 0%, #16204b 60%, #2a2f66 100%)'
const DAY_SKY = 'linear-gradient(180deg, #4ea8ff 0%, #9fd3ff 60%, #e3f3ff 100%)'
const STARS = [
  { x: 24, y: 22, r: 1.6, t: 2100 },
  { x: 66, y: 16, r: 1.2, t: 2600 },
  { x: 80, y: 42, r: 1.8, t: 1900 },
  { x: 38, y: 58, r: 1.1, t: 2900 },
  { x: 58, y: 74, r: 1.4, t: 2300 },
  { x: 14, y: 72, r: 1.2, t: 2500 },
]
const SKY_EASING = 'cubic-bezier(0.65, 0, 0.35, 1)'

// Both bodies ride one circle centred below the button, like a sky dome:
// angle 0 is the middle of the button, a quarter turn is past the lower corner.
function arcPoint(side, angle) {
  return { x: side * ARC_RADIUS * Math.sin(angle), y: ARC_RADIUS * (1 - Math.cos(angle)) }
}
const easeInCubic = (x) => x * x * x
function easeOutBack(x) {
  const overshoot = 1.4
  return 1 + (overshoot + 1) * (x - 1) ** 3 + overshoot * (x - 1) ** 2
}
function settingKeyframes({ side, spin }) {
  return Array.from({ length: KEYFRAME_STEPS + 1 }, (_, i) => {
    const k = i / KEYFRAME_STEPS
    const travelled = easeInCubic(k)
    const { x, y } = arcPoint(side, travelled * QUARTER_TURN)
    return { offset: k, transform: `translate(${x}%, ${y}%) rotate(${side * spin * travelled}deg)`, opacity: k < 0.55 ? 1 : (1 - k) / 0.45 }
  })
}
function risingKeyframes({ side, spin }) {
  return Array.from({ length: KEYFRAME_STEPS + 1 }, (_, i) => {
    const k = i / KEYFRAME_STEPS
    const remaining = 1 - easeOutBack(k)
    const { x, y } = arcPoint(side, remaining * QUARTER_TURN)
    return { offset: k, transform: `translate(${x}%, ${y}%) rotate(${side * spin * remaining}deg) scale(${1 - 0.28 * remaining})`, opacity: Math.min(1, k / 0.3) }
  })
}
const KEYFRAMES = {
  moonSets: settingKeyframes(MOON),
  moonRises: risingKeyframes(MOON),
  sunSets: settingKeyframes(SUN),
  sunRises: risingKeyframes(SUN),
}

const reducedMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

const resting = (body, visible) => ({
  transform: visible ? 'none' : `translate(${body.side * ARC_RADIUS}%, ${ARC_RADIUS}%)`,
  opacity: visible ? 1 : 0,
})

const moon = ref(null)
const sun = ref(null)
const night = ref(null)
const day = ref(null)
let flight = []
let twinkles = []

function swap(next) {
  // Toggling again mid-flight asks for the previous theme: play the running swap backwards from where it is.
  if (flight.length > 0) {
    for (const a of flight) a.reverse()
    return
  }
  if (!moon.value || !sun.value || typeof moon.value.animate !== 'function' || reducedMotion()) return
  const toLight = next === 'light'
  const setting = (toLight ? moon.value : sun.value).animate(toLight ? KEYFRAMES.moonSets : KEYFRAMES.sunSets, { duration: DURATION * 0.65, fill: 'both' })
  const rising = (toLight ? sun.value : moon.value).animate(toLight ? KEYFRAMES.sunRises : KEYFRAMES.moonRises, { duration: DURATION * 0.64, delay: DURATION * 0.36, fill: 'both' })
  const pair = [setting, rising]
  if (night.value && day.value) {
    const opts = { duration: DURATION, easing: SKY_EASING, fill: 'both' }
    pair.push(
      night.value.animate([{ opacity: toLight ? 1 : 0 }, { opacity: toLight ? 0 : 1 }], opts),
      day.value.animate([{ opacity: toLight ? 0 : 1 }, { opacity: toLight ? 1 : 0 }], opts),
    )
  }
  flight = pair
  Promise.all(pair.map((a) => a.finished)).then(
    () => {
      if (flight !== pair) return
      flight = []
      for (const a of pair) a.cancel()
    },
    () => {}, // cancelled on unmount
  )
}

watch(theme, (next) => swap(next), { flush: 'post' })

onMounted(() => {
  if (!night.value || reducedMotion() || typeof night.value.animate !== 'function') return
  twinkles = [...night.value.querySelectorAll('[data-star]')].map((star, i) =>
    star.animate([{ opacity: 0.35 }, { opacity: 1 }, { opacity: 0.35 }], { duration: STARS[i]?.t ?? 2400, delay: -i * 530, iterations: Infinity, easing: 'ease-in-out' }),
  )
})

onBeforeUnmount(() => {
  for (const a of [...flight, ...twinkles]) a.cancel()
  flight = []
})
</script>
