import { test, expect } from '@playwright/test'
import { prime, ROUTES } from './helpers'

// Runs in the "mobile" project (Pixel 7 viewport, touch).

for (const route of ROUTES) {
  test(`${route}: no horizontal overflow on a phone`, async ({ page }) => {
    await prime(page)
    await page.goto(route)
    await page.waitForTimeout(500)
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
    expect(overflow).toBeLessThanOrEqual(0)
  })
}

test('mobile menu opens, navigates and closes', async ({ page }) => {
  await prime(page)
  await page.goto('/')
  await page.getByRole('button', { name: 'Menu' }).click()
  const nav = page.locator('#mobile-nav')
  await expect(nav).toBeVisible()
  await nav.getByRole('link', { name: 'Upazila figures' }).click()
  await expect(page).toHaveURL(/\/statistics$/)
  await expect(nav).toHaveCount(0)
})

test('map control panel slides up as a bottom sheet', async ({ page }) => {
  await prime(page)
  await page.goto('/map')
  const toggle = page.getByRole('button', { name: 'Layers, dates & upazilas' })
  await expect(toggle).toHaveAttribute('aria-expanded', 'false')
  await toggle.click()
  await expect(toggle).toHaveAttribute('aria-expanded', 'true')
  await expect(page.getByRole('radio', { name: /12 Jul 2026/ })).toBeInViewport()
})

test('no cursor ring on touch devices', async ({ page }) => {
  await prime(page)
  await page.goto('/')
  await expect(page.locator('.cursor-ring')).toHaveCount(0)
})

test('"New chat" is reachable on a phone and starts over', async ({ page }) => {
  await prime(page)
  await page.goto('/assistant')
  await expect(page.getByRole('button', { name: 'New chat' })).toHaveCount(0)
  await page.getByRole('button', { name: 'How many people in total?' }).click()
  await expect(page.locator('ol > li').last()).toContainText('112,900')

  const newChat = page.getByRole('button', { name: 'New chat' })
  await expect(newChat).toBeInViewport()
  await newChat.click()
  await expect(page.locator('ol > li')).toHaveCount(0)
  await expect(page.locator('h1')).toBeVisible()
  await expect(newChat).toHaveCount(0)
})

test('"New chat" cancels an answer that is still loading', async ({ page }) => {
  await prime(page)
  await page.goto('/assistant')
  await page.getByRole('button', { name: 'How many people in total?' }).click()
  await page.getByRole('button', { name: 'New chat' }).click()
  await page.waitForTimeout(900)
  await expect(page.locator('ol > li')).toHaveCount(0)
  // and the input is usable again straight away
  await page.getByRole('button', { name: /Ask about any upazila/ }).click()
  await expect(page.getByRole('textbox', { name: 'Your question' })).toBeEnabled()
})
