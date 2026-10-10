// Shared helpers for the e2e suite.

export const ROUTES = ['/', '/map', '/statistics', '/assistant', '/does-not-exist']

// Start a test with a known language + theme (stored the same way the app stores them)
export async function prime(page, { lang = 'en', theme = 'light' } = {}) {
  await page.addInitScript(
    ([l, th]) => {
      if (!sessionStorage.getItem('__primed')) {
        localStorage.setItem('meghbhed-lang', l)
        localStorage.setItem('meghbhed-theme', th)
        sessionStorage.setItem('__primed', '1')
      }
    },
    [lang, theme],
  )
}

// Collect console errors and uncaught exceptions for the whole test
export function trackErrors(page) {
  const errors = []
  page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`))
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(`console: ${msg.text()}`)
  })
  return errors
}

// Wait until both MapLibre maps on the page have drawn their upazila markers
export async function waitForMap(page, markersPerMap = 8, maps = 2) {
  await page.waitForFunction((n) => document.querySelectorAll('.mb-marker').length >= n, markersPerMap * maps, { timeout: 20_000 })
}
