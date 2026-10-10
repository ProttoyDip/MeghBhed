import { test, expect } from '@playwright/test'
import { readFile } from 'node:fs/promises'
import { prime } from './helpers'

test.beforeEach(async ({ page }) => {
  await prime(page)
  await page.goto('/statistics')
})

const firstRowName = (page) => page.locator('tbody tr').first().locator('td').first()

test('headline numbers count up to the totals', async ({ page }) => {
  const kpis = page.locator('dl dd.font-display')
  await expect(kpis.nth(0)).toHaveText('112,900')
  await expect(kpis.nth(1)).toHaveText(/24\.9/)
  await expect(kpis.nth(2)).toHaveText(/33/)
  await expect(kpis.nth(3)).toHaveText('12')
})

test('table sorts by people (default desc) and toggles direction', async ({ page }) => {
  await expect(page.locator('tbody tr')).toHaveCount(8)
  await expect(firstRowName(page)).toContainText('Fatikchhari')
  await page.getByRole('button', { name: 'People' }).click()
  await expect(firstRowName(page)).toContainText('Sitakunda')
  await expect(page.locator('th[aria-sort="ascending"]')).toContainText('People')
})

test('table sorts by name', async ({ page }) => {
  await page.getByRole('button', { name: 'Upazila', exact: true }).click()
  await expect(firstRowName(page)).toContainText('Chhagalnaiya')
})

test('district filter and name search work, with an empty state', async ({ page }) => {
  await page.getByLabel('District').selectOption('Feni')
  await expect(page.locator('tbody tr')).toHaveCount(3)
  await expect(page.locator('tfoot')).toContainText('Total · 3 upazilas')

  await page.getByLabel('District').selectOption('')
  await page.getByLabel('Filter by name').fill('zzz')
  await expect(page.getByText('No upazila matches “zzz”.')).toBeVisible()
  await page.getByRole('button', { name: 'Clear filters' }).click()
  await expect(page.locator('tbody tr')).toHaveCount(8)

  await page.getByLabel('Filter by name').fill('hat')
  await expect(page.locator('tbody tr')).toHaveCount(1)
  await expect(firstRowName(page)).toContainText('Hathazari')
})

test('chart shows a tooltip on hover', async ({ page }) => {
  const row = page.locator('#chart-title').locator('xpath=ancestor::section').locator('.space-y-2\\.5 > div').first()
  await row.scrollIntoViewIfNeeded()
  await row.hover({ position: { x: 300, y: 12 } })
  await expect(page.getByText('C-band missed', { exact: true })).toBeVisible()
})

test('CSV export downloads every visible row', async ({ page }) => {
  const [download] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'CSV' }).click()])
  await expect(page.getByRole('status')).toContainText('Downloaded meghbhed_upazilas_concept.csv')
  expect(download.suggestedFilename()).toBe('meghbhed_upazilas_concept.csv')
  const text = (await readFile(await download.path(), 'utf8')).replace(/^﻿/, '')
  const lines = text.trim().split('\n')
  expect(lines[0]).toBe('upazila,upazila_bn,district,hidden_flood_km2,open_water_km2,missed_share_pct,people,status,lon,lat,note')
  expect(lines).toHaveLength(9)
  expect(text).toContain('ILLUSTRATIVE concept data')
})

test('KML export is valid and has one placemark per upazila', async ({ page }) => {
  const [download] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'KML' }).click()])
  const text = await readFile(await download.path(), 'utf8')
  expect(text.startsWith('<?xml')).toBe(true)
  expect(text.match(/<Placemark>/g)).toHaveLength(8)
  expect(text).toContain('<coordinates>91.79,22.7,0</coordinates>')
})

test('clicking a row opens that upazila on the map', async ({ page }) => {
  await page.locator('tbody tr', { hasText: 'Raozan' }).click()
  await expect(page).toHaveURL(/\/map\?u=raozan/)
  await expect(page.locator('aside')).toContainText('2.4 km²')
})
