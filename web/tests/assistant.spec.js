import { test, expect } from '@playwright/test'
import { prime } from './helpers'

test.beforeEach(async ({ page }) => {
  await prime(page)
  await page.goto('/assistant')
})

const lastAnswer = (page) => page.locator('ol > li').last()

async function ask(page, text) {
  const pill = page.getByRole('button', { name: /Ask about any upazila/ })
  if (await pill.isVisible()) await pill.click()
  const box = page.getByRole('textbox', { name: 'Your question' })
  await box.fill(text)
  await box.press('Enter')
}

test('suggested question gets a grounded answer, with no source line', async ({ page }) => {
  await page.getByRole('button', { name: 'Which upazila has the most people missed?' }).click()
  await expect(lastAnswer(page)).toContainText('Satkania has the most people living within 100 m of flood the 16 July C-band map missed')
  await expect(lastAnswer(page)).toContainText('106,169 people')
  await expect(lastAnswer(page)).not.toContainText('Source')
})

test('answers a typed question about one upazila and links to the map', async ({ page }) => {
  await ask(page, 'How many people in Hathazari?')
  await expect(lastAnswer(page)).toContainText('About 30,841 people')
  await lastAnswer(page).getByRole('link', { name: /Show Hathazari on the map/ }).click()
  await expect(page).toHaveURL(/\/map\?u=hathazari/)
})

test('answers Bangla questions in Bangla', async ({ page }) => {
  await ask(page, 'ফটিকছড়িতে কত মানুষ বন্যাকবলিত?')
  await expect(lastAnswer(page)).toContainText('৮২,৭৮১')
  await expect(lastAnswer(page)).toContainText('ফটিকছড়ি')
})

test('refuses questions the figures cannot answer', async ({ page }) => {
  await ask(page, 'What will the weather be tomorrow?')
  await expect(lastAnswer(page)).toContainText('I only answer from MeghBhed’s computed figures')
})

test('prompt input expands, grows with Shift+Enter and morphs mic → send', async ({ page }) => {
  const pill = page.getByRole('button', { name: /Ask about any upazila/ })
  await pill.click()
  const box = page.getByRole('textbox', { name: 'Your question' })
  await expect(box).toBeFocused()
  const h0 = (await box.boundingBox()).height

  // empty box: the action button offers voice; with text it becomes Send
  await expect(page.getByRole('button', { name: 'Speak your question' })).toBeVisible()
  await box.type('Line one')
  await expect(page.getByRole('button', { name: 'Send' })).toBeVisible()

  await box.press('Shift+Enter')
  await box.type('Line two')
  await box.press('Shift+Enter')
  await box.type('Line three')
  await expect(box).toHaveValue('Line one\nLine two\nLine three')
  await expect.poll(async () => (await box.boundingBox()).height).toBeGreaterThan(h0)

  // Escape on an empty box collapses it again
  await box.fill('')
  await box.press('Escape')
  await expect(pill).toBeVisible()
})

test('welcome gradient unloads once a conversation starts; reset restores it', async ({ page }) => {
  const section = page.getByRole('region', { name: 'Conversation' })
  await expect(section.locator('canvas')).toHaveCount(1)
  await ask(page, 'How many people in total?')
  await expect(lastAnswer(page)).toContainText('587,479')
  await expect(section.locator('canvas')).toHaveCount(0)
  await page.getByRole('button', { name: 'New chat' }).click()
  await expect(section.locator('canvas')).toHaveCount(1)
  await expect(page.locator('h1')).toBeVisible()
})

test('an answer from an AI service shows only the answer: no source line, no model name, no model picker', async ({ page }) => {
  await prime(page, {
    ask: { reply: { answer: 'In Satkania about 106,169 people live within 100 m of the missed flood (an upper bound).', source: 'stats.json → Satkania', provider: 'NVIDIA', model: 'minimaxai/minimax-m3.1-flash', fallback: false } },
  })
  await page.goto('/assistant')
  await ask(page, 'How many people in Satkania?')
  await expect(lastAnswer(page)).toContainText('106,169 people live within 100 m')
  await expect(lastAnswer(page)).not.toContainText('Source')
  await expect(lastAnswer(page)).not.toContainText('NVIDIA')
  await expect(lastAnswer(page)).not.toContainText('Answered by')
  await expect(page.getByRole('combobox')).toHaveCount(0)
  await expect(page.getByText('Questions are sent to an external AI service.')).toBeVisible()
})

test('a greeting gets a friendly reply, not "I can only answer from the figures"', async ({ page }) => {
  await ask(page, 'hi')
  await expect(lastAnswer(page)).toContainText("Hello! I'm MeghBhed")
  await expect(lastAnswer(page)).not.toContainText('can’t help')
  await ask(page, 'thanks')
  await expect(lastAnswer(page)).toContainText("You're welcome")
})

test('a Bangla greeting gets a Bangla reply', async ({ page }) => {
  await ask(page, 'আসসালামু আলাইকুম')
  await expect(lastAnswer(page)).toContainText('হ্যালো! আমি মেঘভেদ')
})
