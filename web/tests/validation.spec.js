import { test, expect } from '@playwright/test'
import { prime, waitForMap, trackErrors } from './helpers'

test.beforeEach(async ({ page }) => prime(page))

test('validation page shows a verdict, four model cards and the rule as the map model', async ({ page }) => {
  const errors = trackErrors(page)
  await page.goto('/validation')
  await expect(page.locator('h1')).toHaveText('How well it works')
  await expect(page.getByTestId('verdict')).toContainText('the map uses the rule')
  await expect(page.locator('[data-model]')).toHaveCount(4)
  const rule = page.locator('[data-model="rule"]')
  await expect(rule).toContainText('Used on the map')
  await expect(rule).toContainText('91.9%') // precision of the rule, from model_comparison.json
  await expect(page.locator('[data-model="lgbm"]')).toContainText('Tuned cut-off')
  expect(errors).toEqual([])
})

test('validation page lists the independent tests and SHAP rankings', async ({ page }) => {
  await page.goto('/validation')
  const rows = page.locator('[data-table="independent"] tbody tr')
  await expect(rows).toHaveCount(4)
  await expect(rows.first()).toContainText('27.5%') // rule, near reported-flooded places
  await expect(page.locator('[data-shap="lightgbm"] li').first()).toContainText('HV change')
  await expect(page.locator('[data-shap="random_forest"] li')).toHaveCount(7)
  await expect(page.getByRole('heading', { name: 'Under the trees: not confirmed' })).toBeVisible()
  // three rows per trained model plus the rule; the break-even rows are marked and explained
  await expect(page.locator('[data-table="cutoffs"] tbody tr')).toHaveCount(10)
  await expect(page.locator('[data-cutoff="breakEven"]')).toHaveCount(3)
  await expect(page.locator('[data-cutoff="breakEven"]').first()).toContainText('Precision-recall break-even point on cross-validated predictions')
  await expect(page.getByText('equal by definition')).toBeVisible()
})

test('validation page reads in Bangla', async ({ page }) => {
  await page.goto('/validation')
  await page.getByRole('button', { name: /switch to Bangla/i }).click()
  await expect(page.locator('h1')).toHaveText('কতটা ভালো কাজ করে')
  await expect(page.locator('[data-model="rule"]')).toContainText('মানচিত্রে ব্যবহৃত')
})

test('risk layers are off by default and show a legend when switched on', async ({ page }) => {
  const requests = []
  page.on('request', (r) => { if (r.url().includes('_risk.png')) requests.push(r.url()) })
  await page.goto('/map')
  await waitForMap(page)
  const flood = page.getByLabel('Flood risk on open land')
  const slide = page.getByLabel('Landslide risk')
  await expect(flood).not.toBeChecked()
  await expect(slide).not.toBeChecked()
  expect(requests).toHaveLength(0) // the images are only fetched when a layer is switched on
  await flood.check()
  const legend = page.locator('[data-risk-legend="flood"]')
  await expect(legend.locator('li')).toHaveCount(4)
  await expect(legend).toContainText('Likelihood map, not a forecast')
  await slide.check()
  await expect(page.locator('[data-risk-legend="landslide"]')).toContainText('Very high')
  await expect.poll(() => requests.length).toBeGreaterThanOrEqual(2)
})

test('statistics page has a separate high-risk table', async ({ page }) => {
  await page.goto('/statistics')
  await expect(page.getByRole('heading', { name: 'People in high-risk areas' })).toBeVisible()
  const table = page.locator('[data-table="risk"]')
  await expect(table.locator('tfoot')).toContainText('265,921') // people in high or very high flood risk on open land, from risk.json
  await expect(table.locator('tbody tr').first()).toContainText('Khulshi')
})

test('assistant answers about the models and the risk maps from the JSON files', async ({ page }) => {
  await page.goto('/assistant')
  const ask = async (text) => {
    const box = page.getByRole('textbox')
    if (!(await box.isVisible().catch(() => false))) await page.getByRole('button', { name: /Ask about any upazila/ }).click()
    await page.getByRole('textbox').fill(text)
    await page.getByRole('textbox').press('Enter')
  }
  await ask('How accurate are the models?')
  await expect(page.locator('ol > li').last()).toContainText('but the map uses the threshold rule')
  await expect(page.locator('ol > li').last()).toContainText('LightGBM')
  await ask('What is the flood risk?')
  await expect(page.locator('ol > li').last()).toContainText('likelihood, not a forecast')
  await expect(page.locator('ol > li').last()).toContainText('265,921')
})
