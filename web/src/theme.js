import { ref, watch } from 'vue'

const KEY = 'meghbhed-theme'
const media = window.matchMedia('(prefers-color-scheme: dark)')

function stored() {
  try {
    const v = localStorage.getItem(KEY)
    return v === 'light' || v === 'dark' ? v : null
  } catch {
    return null
  }
}

// index.html sets data-theme before first paint; this keeps it in sync after.
export const theme = ref(stored() ?? (media.matches ? 'dark' : 'light'))

function apply(t) {
  const root = document.documentElement
  root.dataset.theme = t
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', t === 'dark' ? '#0d1520' : '#f6f8fa')
}
apply(theme.value)

watch(theme, (t) => {
  const root = document.documentElement
  root.classList.add('theme-anim')
  apply(t)
  window.setTimeout(() => root.classList.remove('theme-anim'), 400)
  try {
    localStorage.setItem(KEY, t)
  } catch {
    // storage blocked: the choice still applies for this visit
  }
})

// Follow the OS setting until the user picks one explicitly
media.addEventListener('change', (e) => {
  if (!stored()) theme.value = e.matches ? 'dark' : 'light'
})

export const toggleTheme = () => {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
}
