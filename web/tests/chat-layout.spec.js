import { test, expect } from '@playwright/test'
import { prime } from './helpers'

// Regression tests for the "chat page looks broken until you start typing" report:
// the welcome gradient ended in a hard edge above the input, the column sat 16px
// in from the window edges, and the page scrolled by 1px.

for (const route of ['/assistant', '/map']) {
  test(`${route} fits the window exactly (no page scroll)`, async ({ page }) => {
    await prime(page)
    await page.goto(route)
    const overflow = await page.evaluate(() => document.documentElement.scrollHeight - window.innerHeight)
    expect(overflow).toBeLessThanOrEqual(0)
  })
}

test('chat column and side panel run edge to edge', async ({ page }) => {
  await prime(page)
  await page.goto('/assistant')
  const section = await page.getByRole('region', { name: 'Conversation' }).boundingBox()
  const aside = await page.getByRole('complementary', { name: 'About the assistant' }).boundingBox()
  const width = page.viewportSize().width
  expect(section.x).toBe(0)
  expect(Math.round(aside.x + aside.width)).toBe(width)
})

test('welcome gradient fades out above the input instead of ending in a hard edge', async ({ page }) => {
  await prime(page)
  await page.goto('/assistant')
  const section = page.getByRole('region', { name: 'Conversation' })
  const backdrop = section.locator('.fade-bottom')
  await expect(backdrop).toHaveCount(1)
  const mask = await backdrop.evaluate((el) => getComputedStyle(el).maskImage || getComputedStyle(el).webkitMaskImage)
  expect(mask).toContain('linear-gradient')
  // the scroll-under strip above the input only exists once messages do
  await expect(section.locator('.bg-linear-to-t')).toHaveCount(0)
})

test('opening the input does not resize or redraw the gradient', async ({ page }) => {
  await prime(page)
  await page.goto('/assistant')
  const canvas = page.getByRole('region', { name: 'Conversation' }).locator('canvas')
  const before = await canvas.boundingBox()
  await page.getByRole('button', { name: /Ask about any upazila/ }).click()
  await expect(page.getByRole('textbox', { name: 'Your question' })).toBeFocused()
  await page.waitForTimeout(500)
  const after = await canvas.boundingBox()
  expect(after, JSON.stringify({ before, after })).toEqual(before)
})

for (const lang of ['en', 'bn']) {
  test(`[${lang}] collapsed input placeholder is not cut off on a phone`, async ({ browser }) => {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } })
    const page = await ctx.newPage()
    await prime(page, { lang })
    await page.goto('/assistant')
    const label = page.locator('button[tabindex="0"] span.truncate')
    await expect(label).toBeVisible()
    const clipped = await label.evaluate((el) => el.scrollWidth > el.clientWidth)
    expect(clipped).toBe(false)
    await ctx.close()
  })
}
