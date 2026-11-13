import { test, expect } from '@playwright/test'
import { prime } from './helpers'

// Chrome's fake microphone plays a steady tone, which counts as speech; /api/transcribe is stubbed,
// so no audio leaves the machine.
test.use({
  launchOptions: { args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'] },
  permissions: ['microphone'],
})

test('with NVIDIA speech-to-text configured, the microphone records, sends 16 kHz audio and fills in the text', async ({ page }) => {
  await prime(page, { transcribe: { text: 'How many people live near the flood in Satkania?' } })
  let sent = null
  page.on('request', (r) => {
    if (r.url().endsWith('/api/transcribe') && r.method() === 'POST') sent = r.postDataJSON()
  })
  await page.goto('/assistant')
  await page.getByRole('button', { name: /Ask about any upazila/ }).click()
  const started = Date.now()
  await page.getByRole('button', { name: 'Speak your question' }).click()
  await expect(page.getByTestId('voice-state')).toHaveText('Listening…')
  await page.waitForTimeout(2500) // the recorder can start late on a busy machine
  await page.getByRole('button', { name: 'Stop listening' }).click()
  const recordedAtMost = (Date.now() - started) / 1000
  await expect(page.getByRole('textbox', { name: 'Your question' })).toHaveValue('How many people live near the flood in Satkania?')
  expect(sent.lang).toBe('en')
  const bytes = Buffer.from(sent.audio, 'base64').length
  expect(bytes).toBeGreaterThan(16000 * 2 * 0.5) // more than half a second of 16 kHz, 16-bit audio
  // No more than 16 kHz, 16-bit audio for the time the mic was on (plus one capture buffer). Audio left at the
  // browser's 44.1 or 48 kHz would be about three times this.
  expect(bytes).toBeLessThanOrEqual(16000 * 2 * (recordedAtMost + 0.2))
})

test('without a speech service, the microphone falls back to the browser and the page still works', async ({ page }) => {
  await prime(page)
  let posted = false
  page.on('request', (r) => {
    if (r.url().endsWith('/api/transcribe') && r.method() === 'POST') posted = true
  })
  await page.goto('/assistant')
  await page.getByRole('button', { name: /Ask about any upazila/ }).click()
  await expect(page.getByRole('textbox', { name: 'Your question' })).toBeVisible()
  expect(posted).toBe(false)
})
