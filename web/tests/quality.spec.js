import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { prime, trackErrors, waitForMap, ROUTES } from './helpers'

// Pre-flight gates from the taste review, run on every page in both languages.

for (const lang of ['en', 'bn']) {
  for (const route of ROUTES) {
    test(`[${lang}] ${route}: no em/en dashes in visible copy, no console errors`, async ({ page }) => {
      const errors = trackErrors(page)
      await prime(page, { lang })
      await page.goto(route)
      if (route === '/map') await waitForMap(page)
      await page.waitForTimeout(600)
      const text = await page.evaluate(() => document.body.innerText)
      const dashes = text.split('\n').filter((l) => /[–—]/.test(l))
      expect(dashes, 'lines containing an em/en dash').toEqual([])
      expect(errors).toEqual([])
    })
  }
}

for (const route of ROUTES) {
  test(`${route}: exactly one h1, alt text on images, named buttons and links`, async ({ page }) => {
    await prime(page)
    await page.goto(route)
    await expect(page.locator('h1')).toHaveCount(1)
    const imgsWithoutAlt = await page.locator('img:not([alt]), img[alt=""]').count()
    expect(imgsWithoutAlt).toBe(0)
    const unnamed = await page.evaluate(() =>
      [...document.querySelectorAll('button, a[href]')]
        .filter((el) => el.offsetParent !== null)
        .filter((el) => !(el.getAttribute('aria-label') || el.textContent.trim() || el.getAttribute('title')))
        .map((el) => el.outerHTML.slice(0, 80)),
    )
    expect(unnamed).toEqual([])
  })
}

for (const theme of ['light', 'dark']) {
  for (const route of ROUTES) {
    test(`[${theme}] ${route}: axe finds no serious accessibility violations`, async ({ browser }) => {
      // Reduced motion so scroll reveals are settled before scanning
      const ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: 1440, height: 900 } })
      const page = await ctx.newPage()
      await prime(page, { theme })
      await page.goto(route)
      if (route === '/map') await waitForMap(page)
      await page.waitForTimeout(500)
      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .exclude('.maplibregl-canvas-container')
        .exclude('canvas')
        .analyze()
      const serious = results.violations
        .filter((v) => ['serious', 'critical'].includes(v.impact))
        .map((v) => `${v.id}: ${v.nodes.length} node(s), e.g. ${v.nodes[0].target.join(' ')}`)
      expect(serious).toEqual([])
      await ctx.close()
    })
  }
}

test('reduced motion: no cursor ring, no smooth-scroll takeover, content visible', async ({ browser }) => {
  const ctx = await browser.newContext({ reducedMotion: 'reduce' })
  const page = await ctx.newPage()
  await page.goto('/')
  await expect(page.locator('.cursor-ring')).toHaveCount(0)
  await expect(page.locator('html')).not.toHaveClass(/lenis/)
  const hidden = await page.evaluate(() => [...document.querySelectorAll('.reveal')].filter((el) => getComputedStyle(el).opacity === '0').length)
  expect(hidden).toBe(0)
  await ctx.close()
})

test('motion on: smooth scrolling, cursor ring and scroll reveals are active', async ({ page }) => {
  await prime(page)
  await page.goto('/')
  await expect(page.locator('html')).toHaveClass(/lenis/)
  await page.mouse.move(400, 400)
  await expect(page.locator('.cursor-ring')).toHaveCount(1)
  const pending = await page.locator('.reveal:not(.is-in)').count()
  expect(pending).toBeGreaterThan(0)
  await page.locator('footer').scrollIntoViewIfNeeded()
  await expect.poll(() => page.locator('footer .reveal.is-in').count()).toBeGreaterThan(0)
})

test('hero gradient renders with WebGL2', async ({ page }) => {
  await prime(page)
  await page.goto('/')
  const hasGl = await page.evaluate(() => {
    const c = document.querySelector('section canvas:not(.maplibregl-canvas)')
    return !!c && c.width > 0 && c.height > 0
  })
  expect(hasGl).toBe(true)
})
