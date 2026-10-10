import Lenis from 'lenis'

export const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

// ---- smooth scrolling -------------------------------------------------------
// Inner scroll areas (map panel, chat) opt out with data-lenis-prevent.
export const lenis = reducedMotion
  ? null
  : new Lenis({
      autoRaf: true,
      lerp: 0.09,
      wheelMultiplier: 1,
      anchors: { offset: -88 },
    })

export function scrollToTop() {
  if (lenis) lenis.scrollTo(0, { immediate: true, force: true })
  else window.scrollTo(0, 0)
}

// ---- v-reveal ---------------------------------------------------------------
// v-reveal            fade/slide the element in when it enters the viewport
// v-reveal="120"      …after a 120 ms delay
// v-reveal.stagger    reveal each child in turn (70 ms apart)
const observer = new IntersectionObserver(
  (entries) => {
    for (const e of entries) {
      if (!e.isIntersecting) continue
      e.target.classList.add('is-in')
      observer.unobserve(e.target)
    }
  },
  { rootMargin: '0px 0px -8% 0px', threshold: 0.08 },
)

function prepare(el, delay) {
  el.classList.add('reveal')
  if (delay) el.style.setProperty('--reveal-delay', `${delay}ms`)
  observer.observe(el)
}

export const vReveal = {
  mounted(el, binding) {
    if (reducedMotion) return
    if (binding.modifiers.stagger) {
      ;[...el.children].forEach((child, i) => prepare(child, (binding.value ?? 0) + i * 70))
    } else {
      prepare(el, binding.value)
    }
  },
  unmounted(el, binding) {
    if (binding.modifiers.stagger) [...el.children].forEach((c) => observer.unobserve(c))
    else observer.unobserve(el)
  },
}

// Run a callback once when an element first becomes visible
export function onVisible(el, cb, threshold = 0.3) {
  if (!el) return () => {}
  const io = new IntersectionObserver(
    ([e]) => {
      if (e.isIntersecting) {
        cb()
        io.disconnect()
      }
    },
    { threshold },
  )
  io.observe(el)
  return () => io.disconnect()
}
