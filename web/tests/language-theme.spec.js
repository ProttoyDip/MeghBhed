import { test, expect } from '@playwright/test'
import { prime } from './helpers'

test.describe('language', () => {
  test.beforeEach(async ({ page }) => prime(page, { lang: 'en' }))

  test('toggle switches the whole UI to Bangla and back', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('button', { name: /switch to Bangla/i }).click()

    await expect(page.locator('html')).toHaveAttribute('lang', 'bn')
    await expect(page.locator('header nav')).toContainText('সারসংক্ষেপ')
    await expect(page.locator('h1')).toContainText('হারিয়ে যাওয়া')
    await expect(page).toHaveTitle(/মেঘভেদ/)

    await page.getByRole('button', { name: /switch to English/i }).click()
    await expect(page.locator('html')).toHaveAttribute('lang', 'en')
    await expect(page.locator('h1')).toContainText('See the flood')
  })

  test('choice persists across reloads', async ({ page }) => {
    await page.goto('/statistics')
    await page.getByRole('button', { name: /switch to Bangla/i }).click()
    await page.reload()
    await expect(page.locator('h1')).toHaveText('C-band মানচিত্রে কারা বাদ পড়েছেন')
  })

  test('numbers use Bengali digits in Bangla', async ({ page }) => {
    await page.goto('/statistics')
    await page.getByRole('button', { name: /switch to Bangla/i }).click()
    // table total: 1,12,900 people in lakh grouping
    await expect(page.locator('tfoot')).toContainText('১,১২,৯০০')
    await expect(page.locator('tbody tr').first()).toContainText('ফটিকছড়ি')
  })
})

test.describe('theme', () => {
  test('toggle switches light ↔ dark and persists', async ({ page }) => {
    await prime(page, { theme: 'light' })
    await page.goto('/')
    const html = page.locator('html')
    await expect(html).toHaveAttribute('data-theme', 'light')

    await page.getByRole('button', { name: 'Switch to dark theme' }).click()
    await expect(html).toHaveAttribute('data-theme', 'dark')
    const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor)
    expect(bg).toBe('rgb(13, 21, 32)')

    await page.reload()
    await expect(html).toHaveAttribute('data-theme', 'dark')
    await page.getByRole('button', { name: 'Switch to light theme' }).click()
    await expect(html).toHaveAttribute('data-theme', 'light')
  })

  test('first visit follows the system colour scheme', async ({ browser }) => {
    for (const scheme of ['dark', 'light']) {
      const ctx = await browser.newContext({ colorScheme: scheme })
      const page = await ctx.newPage()
      await page.goto('/')
      await expect(page.locator('html')).toHaveAttribute('data-theme', scheme)
      await ctx.close()
    }
  })

  test('dark mode is applied before first paint (no flash)', async ({ browser }) => {
    const ctx = await browser.newContext({ colorScheme: 'dark' })
    const page = await ctx.newPage()
    // Read the attribute as soon as the document exists, before the app boots
    await page.addInitScript(() => {
      document.addEventListener('DOMContentLoaded', () => {
        window.__themeAtDomReady = document.documentElement.dataset.theme
      })
    })
    await page.goto('/')
    expect(await page.evaluate(() => window.__themeAtDomReady)).toBe('dark')
    await ctx.close()
  })
})
