// Builds the compact "facts block" the language model must answer from, and the set of numbers
// the grounding check accepts. Everything comes from the pipeline's JSON files in public/data/.
// Server-side only: this file is never imported by the browser bundle.
import { readFileSync } from 'node:fs'

const read = (name) => JSON.parse(readFileSync(new URL(`../public/data/${name}`, import.meta.url), 'utf8'))

const pct = (v) => `${(v * 100).toFixed(1)}%`
const int = (v) => Math.round(v).toLocaleString('en-US')

const MODEL_NAMES = {
  'rule (HH drop and HH level)': 'Threshold rule',
  logistic_regression: 'Logistic regression',
  random_forest: 'Random Forest',
  lightgbm: 'LightGBM',
}

export function buildFacts({ stats, risk, models } = {}) {
  stats ??= read('stats.json')
  try { risk ??= read('risk.json') } catch { risk = null }
  try { models ??= read('model_comparison.json') } catch { models = null }
  const L = []
  const t = stats.totals
  const d = stats.method?.dates ?? {}

  L.push('# MeghBhed facts (Chattogram district, Bangladesh; July 2026 floods). Results are provisional.')
  L.push('')
  L.push('## stats.json → method')
  L.push(`- The flood map is for 12 July 2026: open flood seen by NISAR L-band radar on ${d.nisar_flood_pass ?? '2026-07-12'}, compared with the free C-band map (${d.cband_map ?? 'OPERA DSWx-S1 2026-07-16'}), which is from 16 July 2026, 4 days later.`)
  L.push(`- Rule: ${stats.method?.rule ?? ''}`)
  L.push('- "Missed" means flood seen on 12 July that the 16 July C-band map does not show. "Seen by both" means both show it.')
  L.push('- People = WorldPop population living within 100 m of the missed flood. It is an upper bound: about 14% of open low ground away from reported flooding is also flagged. The conservative figure counts only patches of 5 ha or more.')
  L.push('- "Drained within a week" means no longer dark on the 19 July 2026 NISAR pass.')
  L.push('- Flooding under trees could not be confirmed; under-tree cells are unverified and are in no total.')
  L.push('- Hill Risk points are places to check on the ground, not confirmed landslides.')
  L.push('')
  L.push('## stats.json → totals')
  L.push(`- Missed by the 16 July C-band map: ${t.hidden} km². Seen by both: ${t.both} km².`)
  L.push(`- People within 100 m of missed flood (upper bound): ${int(t.people)}. Conservative: ${int(t.people_conservative)}. Within 100 m of all flood: ${int(t.people_within_100m_all_flood)}.`)
  L.push(`- Drained by 19 July: ${t.drained_pct}%. Under trees, unverified: ${t.under_trees_unverified_km2} km². Hill Risk points: ${t.hill}. Upazilas with flood: ${stats.upazilas.filter((u) => u.hidden > 0).length}.`)
  L.push('')
  L.push('## stats.json → upazilas (missed km² | seen by both km² | people within 100 m, upper bound | people, conservative | drained by 19 July % | status | Hill Risk points)')
  for (const u of stats.upazilas) {
    const status = u.agree === 'both-dates' ? 'drained within a week' : 'still wet on 19 July or not covered'
    L.push(`- ${u.name}: ${u.hidden} | ${u.both} | ${int(u.people)} | ${int(u.people_conservative ?? 0)} | ${u.drained_pct ?? 'n/a'} | ${status} | ${u.hill}`)
  }

  if (models?.tuned?.length) {
    L.push('')
    L.push('## model_comparison.json → models (5 km spatial cross-validation; classifiers at their tuned cut-off)')
    L.push('- Columns: precision | recall | F1 | accuracy | open ground flagged near reported-flooded test places % | near no-report test places % | area flagged km²')
    for (const m of models.tuned) {
      const name = MODEL_NAMES[m.model] ?? m.model
      L.push(`- ${name}${m.model === models.pipeline_uses ? ' (used on the map)' : ''}: ${pct(m.precision)} | ${pct(m.recall)} | ${pct(m.f1)} | ${pct(m.accuracy)} | ${m.test_flagged_pct_near_flooded_points.toFixed(1)} | ${m.test_flagged_pct_near_dry_points.toFixed(1)} | ${Math.round(m.flagged_km2)}`)
    }
    const best = [...models.tuned].filter((m) => m.model !== models.pipeline_uses).sort((x, y) => y.f1 - x.f1)[0]
    if (best) L.push(`- Best benchmark score: ${MODEL_NAMES[best.model] ?? best.model} (highest F1 and accuracy). It is NOT used on the map.`)
    L.push('- The classifiers score higher, but they flag far more open ground near places with no flood report, so the map uses the threshold rule.')
  }

  if (risk?.flood) {
    const f = risk.flood
    L.push('')
    L.push('## risk.json → flood (a likelihood map, not a forecast; trained on one flood, July 2026; covers open land only, tree-covered land is not scored, so people figures are a lower bound)')
    L.push(`- Model: ${MODEL_NAMES[f.chosen_model] ?? f.chosen_model}. High or very high flood risk: ${f.totals.high_or_very_high_km2} km², ${int(f.totals.high_or_very_high_people)} people.`)
    L.push('- Upazilas (people in high or very high flood risk | km²):')
    for (const u of f.upazilas.filter((x) => x.high_or_very_high_people > 0).slice(0, 15)) L.push(`  - ${u.name}: ${int(u.high_or_very_high_people)} | ${u.high_or_very_high_km2}`)
  }
  if (risk?.landslide) {
    const s = risk.landslide
    L.push('')
    L.push('## risk.json → landslide (a likelihood map, not a forecast; a weighted index of slope, relief, rain and land cover, not a trained model; only slopes that rise 20 m or more within 300 m are counted)')
    L.push(`- High or very high landslide risk: ${s.totals.high_or_very_high_km2} km² of steep land. People within 100 m: ${int(s.totals.people_within_100m_high_or_very_high)}.`)
    L.push('- Upazilas (people within 100 m of high or very high slopes | high km² | very high km²):')
    for (const u of s.upazilas.filter((x) => x.people_within_100m_high_or_very_high > 0).slice(0, 15)) L.push(`  - ${u.name}: ${int(u.people_within_100m_high_or_very_high)} | ${u.high_km2} | ${u.very_high_km2}`)
  }

  const text = L.join('\n')
  return { text, numbers: extractNumbers(text), dates: extractDates(text) }
}

const BN = '০১২৩৪৫৬৭৮৯'

// Every number in a text as { value, decimals }, with Bangla digits and thousands separators handled
// (both 587,479 and the Indian grouping 5,87,479).
export function extractNumbers(text) {
  const ascii = String(text).replace(/[০-৯]/g, (c) => String(BN.indexOf(c)))
  const out = []
  for (const m of ascii.matchAll(/\d[\d,]*(?:\.\d+)?/g)) {
    const raw = m[0].replace(/,+$/, '')
    const plain = raw.replace(/,/g, '')
    if (!/^\d+(\.\d+)?$/.test(plain)) continue
    const decimals = plain.includes('.') ? plain.split('.')[1].length : 0
    out.push({ value: Number(plain), decimals, digits: plain.replace('.', '').length })
  }
  return out
}

const MONTHS = { june: 6, jun: 6, 'জুন': 6, july: 7, jul: 7, 'জুলাই': 7, august: 8, aug: 8, 'আগস্ট': 8 }
const MONTH_RE = /(\d{1,2})(?:st|nd|rd|th)?\s*(june|jun|july|jul|august|aug|জুন|জুলাই|আগস্ট)(?![a-z])/gi

// Day-and-month dates in a text, e.g. "12 July" or "১২ জুলাই" -> ["7-12"]
export function extractDates(text) {
  const ascii = String(text).replace(/[০-৯]/g, (c) => String(BN.indexOf(c)))
  return [...ascii.matchAll(MONTH_RE)].map((m) => `${MONTHS[m[2].toLowerCase()]}-${Number(m[1])}`)
}

// True when every number of two or more digits in the answer appears in the facts, allowing the
// answer to round a fact to fewer decimals (27.7 for 27.70, 79 for 78.7), and every date it gives
// (such as "12 July") appears in the facts as that date. factDates is optional.
export function numbersAreGrounded(answer, factNumbers, factDates = null) {
  const unknown = []
  if (factDates) for (const d of extractDates(answer)) if (!factDates.includes(d)) unknown.push(d)
  for (const n of extractNumbers(answer)) {
    if (n.digits < 2) continue
    const scale = 10 ** n.decimals
    const ok = factNumbers.some((f) => Math.abs(Math.round(f.value * scale) / scale - n.value) < 1e-9)
    if (!ok) unknown.push(n.value)
  }
  return { ok: unknown.length === 0, unknown }
}
