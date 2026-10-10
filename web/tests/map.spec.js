import { test, expect } from '@playwright/test'
import { prime, waitForMap, trackErrors } from './helpers'

test.beforeEach(async ({ page }) => {
  await prime(page)
})

test('both maps load with upazila markers and no errors', async ({ page }) => {
  const errors = trackErrors(page)
  await page.goto('/map')
  await waitForMap(page)
  await expect(page.locator('.maplibregl-canvas')).toHaveCount(2)
  await expect(page.getByText('C-band · OPERA DSWx-S1')).toBeVisible()
  await expect(page.getByText('NISAR L-band · GCOV')).toBeVisible()
  expect(errors).toEqual([])
})

test('swipe handle is keyboard operable', async ({ page }) => {
  await page.goto('/map')
  await waitForMap(page)
  const handle = page.getByRole('slider', { name: /Swipe between/ })
  await expect(handle).toHaveAttribute('aria-valuenow', '50')
  await handle.focus()
  await page.keyboard.press('ArrowLeft')
  await page.keyboard.press('ArrowLeft')
  await expect(handle).toHaveAttribute('aria-valuenow', '42')
  await page.keyboard.press('ArrowRight')
  await expect(handle).toHaveAttribute('aria-valuenow', '46')
})

test('swipe handle can be dragged', async ({ page }) => {
  await page.goto('/map')
  await waitForMap(page)
  const handle = page.getByRole('slider', { name: /Swipe between/ })
  const box = await handle.boundingBox()
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2)
  await page.mouse.down()
  await page.mouse.move(box.x + 250, box.y + box.height / 2, { steps: 8 })
  await page.mouse.up()
  expect(Number(await handle.getAttribute('aria-valuenow'))).toBeGreaterThan(60)
})

test('view mode switches between compare and NISAR only', async ({ page }) => {
  await page.goto('/map')
  await waitForMap(page)
  await page.getByRole('button', { name: 'NISAR only' }).click()
  await expect(page.getByRole('button', { name: 'NISAR only' })).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByRole('slider', { name: /Swipe between/ })).toHaveCount(0)
  await page.getByRole('button', { name: 'Compare' }).click()
  await expect(page.getByRole('slider', { name: /Swipe between/ })).toBeVisible()
})

test('acquisition dates, layers and basemap respond', async ({ page }) => {
  await page.goto('/map')
  await waitForMap(page)

  await page.getByRole('radio', { name: /19 Jul 2026/ }).check()
  await expect(page.getByText('Track 163 · 19 Jul 2026')).toBeVisible()

  const hill = page.getByRole('checkbox', { name: /Hill Risk/ })
  await expect(hill).not.toBeChecked()
  await hill.check()
  await expect(hill).toBeChecked()

  await page.getByRole('button', { name: 'Satellite' }).click()
  await expect(page.getByRole('button', { name: 'Satellite' })).toHaveAttribute('aria-pressed', 'true')
  await expect(page.locator('.maplibregl-ctrl-attrib')).toContainText('Maxar')
})

test('selecting an upazila shows its figures; selecting again clears it', async ({ page }) => {
  await page.goto('/map')
  await waitForMap(page)
  const row = page.getByRole('button', { name: /Fatikchhari\s*Chattogram/ })
  await row.click()
  const detail = page.locator('aside').getByText('5.2 km²')
  await expect(detail).toBeVisible()
  await expect(page.locator('aside')).toContainText('Likely missed by C-band')
  await expect(page.locator('.mb-marker.is-selected')).toHaveCount(2)

  await row.click()
  await expect(detail).toHaveCount(0)
})

test('clicking a map marker selects that upazila', async ({ page }) => {
  await page.goto('/map')
  await waitForMap(page)
  await page.locator('.mb-marker[data-id="parshuram"]').first().click({ force: true })
  await expect(page.locator('aside')).toContainText('9.4 km²')
})

test('deep link from the figures table opens with the upazila selected', async ({ page }) => {
  await page.goto('/map?u=hathazari')
  await waitForMap(page)
  await expect(page.locator('aside')).toContainText('3.8 km²')
  await expect(page.locator('.mb-marker.is-selected[data-id="hathazari"]')).toHaveCount(2)
})

test('cursor position readout updates over the map', async ({ page }) => {
  await page.goto('/map')
  await waitForMap(page)
  const canvas = page.locator('.maplibregl-canvas').first()
  const box = await canvas.boundingBox()
  await page.mouse.move(box.x + box.width * 0.75, box.y + box.height * 0.4)
  await expect(page.getByText(/\d+\.\d{4}°N \d+\.\d{4}°E/)).toBeVisible()
})

test('zoom buttons change the zoom readout', async ({ page }) => {
  await page.goto('/map')
  await waitForMap(page)
  const readout = page.getByText(/z\d+\.\d$/)
  const before = await readout.textContent()
  await page.getByRole('button', { name: 'Zoom in' }).click()
  await expect(readout).not.toHaveText(before)
})
