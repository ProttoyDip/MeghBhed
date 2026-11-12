import { test, expect } from '@playwright/test'
import { readFile } from 'node:fs/promises'
import { prime } from './helpers'

test.beforeEach(async ({ page }) => {
  await prime(page)
  await page.goto('/statistics')
})

// The page has two tables: the upazila table comes first, the model comparison second
const upazilaRows = (page) => page.locator('tbody').first().locator('tr')
const firstRowName = (page) => upazilaRows(page).first().locator('td').first()

test('headline numbers count up to the totals', async ({ page }) => {
  const kpis = page.locator('dl dd.font-display')
  await expect(kpis.nth(0)).toHaveText('587,479')
  await expect(kpis.nth(1)).toHaveText(/169\.2/)
  await expect(kpis.nth(2)).toHaveText(/90/)
  await expect(kpis.nth(3)).toHaveText('36')
})

test('table sorts by people (default desc) and toggles direction', async ({ page }) => {
  await expect(upazilaRows(page)).toHaveCount(15)
  await expect(firstRowName(page)).toContainText('Satkania')
  await page.getByRole('button', { name: 'People within 100 m' }).click()
  await expect(firstRowName(page)).toContainText('Chandgaon')
  await expect(page.locator('th[aria-sort="ascending"]')).toContainText('People')
})

test('table sorts by name', async ({ page }) => {
  await page.getByRole('button', { name: 'Upazila', exact: true }).click()
  await expect(firstRowName(page)).toContainText('Anowara')
})

test('district filter and name search work, with an empty state', async ({ page }) => {
  await page.getByLabel('District').selectOption('Chattogram')
  await expect(upazilaRows(page)).toHaveCount(15)
  await expect(page.locator('tfoot').first()).toContainText('Total · 15 upazilas')

  await page.getByLabel('District').selectOption('')
  await page.getByLabel('Filter by name').fill('zzz')
  await expect(page.getByText('No upazila matches “zzz”.')).toBeVisible()
  await page.getByRole('button', { name: 'Clear filters' }).click()
  await expect(upazilaRows(page)).toHaveCount(15)

  await page.getByLabel('Filter by name').fill('hat')
  await expect(upazilaRows(page)).toHaveCount(1)
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
  await expect(page.getByRole('status')).toContainText('Downloaded meghbhed_upazilas_provisional.csv')
  expect(download.suggestedFilename()).toBe('meghbhed_upazilas_provisional.csv')
  const text = (await readFile(await download.path(), 'utf8')).replace(/^﻿/, '')
  const lines = text.trim().split('\n')
  expect(lines[0]).toBe('upazila,upazila_bn,district,missed_by_16jul_cband_km2,seen_by_both_km2,missed_share_pct,people_within_100m,people_conservative,drained_by_19jul_pct,status,lon,lat,note')
  expect(lines).toHaveLength(16)
  expect(text).toContain('PROVISIONAL results')
})

test('KML export is valid and has one placemark per upazila', async ({ page }) => {
  const [download] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'KML' }).click()])
  const text = await readFile(await download.path(), 'utf8')
  expect(text.startsWith('<?xml')).toBe(true)
  expect(text.match(/<Placemark>/g)).toHaveLength(15)
  expect(text).toContain('<coordinates>91.704,22.775,0</coordinates>')
})

test('clicking a row opens that upazila on the map', async ({ page }) => {
  await upazilaRows(page).filter({ hasText: 'Raozan' }).click()
  await expect(page).toHaveURL(/\/map\?u=raozan/)
  await expect(page.locator('aside')).toContainText('16.0 km²')
})
