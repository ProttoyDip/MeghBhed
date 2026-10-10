import { test, expect } from '@playwright/test'
import { prime } from './helpers'

test.beforeEach(async ({ page }) => prime(page))

const pages = [
  { path: '/', nav: 'Overview', h1: /See the flood the maps missed/, title: /See the flood the maps missed · MeghBhed/ },
  { path: '/map', nav: 'Flood map', h1: /Flood map/, title: /Flood map · MeghBhed/ },
  { path: '/statistics', nav: 'Upazila figures', h1: /Who the C-band map missed/, title: /Upazila figures · MeghBhed/ },
  { path: '/assistant', nav: 'Ask MeghBhed', h1: /Ask about the flood under the trees/, title: /Ask MeghBhed · MeghBhed/ },
]

for (const p of pages) {
  test(`${p.path} renders its heading, title and active nav item`, async ({ page }) => {
    await page.goto(p.path)
    await expect(page.locator('h1')).toHaveText(p.h1)
    await expect(page).toHaveTitle(p.title)
    const active = page.locator('header nav a[aria-current="page"]')
    await expect(active).toHaveText(p.nav)
  })
}

test('header navigation moves between every page', async ({ page }) => {
  await page.goto('/')
  for (const p of pages.slice(1).concat(pages[0])) {
    await page.locator('header nav').getByRole('link', { name: p.nav, exact: true }).click()
    await expect(page).toHaveURL(new RegExp(`${p.path === '/' ? '/$' : p.path}`))
    await expect(page.locator('h1')).toHaveText(p.h1)
  }
})

test('hero call to action opens the flood map', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('link', { name: 'Open the flood map' }).click()
  await expect(page).toHaveURL(/\/map$/)
})

test('"How the detection works" scrolls to the method section', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('link', { name: 'How the detection works' }).click()
  await expect(page.locator('#method')).toBeInViewport({ ratio: 0.2 })
})

test('unknown URLs show the 404 page with a way back', async ({ page }) => {
  await page.goto('/no/such/page')
  await expect(page.locator('h1')).toHaveText(/survey area/)
  await expect(page).toHaveTitle(/Page not found/)
  await page.getByRole('link', { name: 'Back to overview' }).click()
  await expect(page).toHaveURL(/\/$/)
})

test('skip link targets the main content', async ({ page }) => {
  await page.goto('/')
  await page.keyboard.press('Tab')
  const skip = page.getByRole('link', { name: 'Skip to content' })
  await expect(skip).toBeFocused()
  await expect(skip).toHaveAttribute('href', '#main')
})

test('footer links point at real destinations', async ({ page }) => {
  await page.goto('/')
  const hrefs = await page.locator('footer a').evaluateAll((as) => as.map((a) => a.getAttribute('href')))
  expect(hrefs.length).toBeGreaterThanOrEqual(6)
  for (const h of hrefs) expect(h).toMatch(/^https:\/\//)
})
