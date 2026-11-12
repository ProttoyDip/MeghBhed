// Real results from the offline pipeline (pipeline/08_stats.py and 10_flood_models.py).
// The files live in web/public/data/ and are fetched once, before the app mounts:
//   stats.json             per-upazila figures, totals and the method block
//   model_comparison.json  rule vs Random Forest vs LightGBM for the open-flood map
//   flood.geojson          flood polygons (read straight by the map)
//   hill_risk.geojson      Hill Risk points (read straight by the map)
// Results are provisional, like the NISAR products they use.
import { reactive } from 'vue'

export const IS_CONCEPT = false

export const DATA_URLS = {
  stats: '/data/stats.json',
  models: '/data/model_comparison.json',
  flood: '/data/flood.geojson',
  floodPreview: '/data/flood_preview.geojson', // small simplified copy for the landing page
  hill: '/data/hill_risk.geojson',
  risk: '/data/risk.json',
}

// 'flood' says what the overlay shows for each NISAR date:
//   none  = before the flood, nothing drawn
//   all   = every flood polygon (the 12 Jul flood pass)
//   still = only polygons still dark on the 19 Jul pass (drained === false)
export const scenes = [
  { id: 'before', iso: '2026-06-30', track: 69, label: 'Before', labelBn: 'আগে', note: 'Pre-flood baseline', noteBn: 'বন্যার আগের ভিত্তি', flood: 'none' },
  { id: 'during1', iso: '2026-07-12', track: 69, label: 'Flood pass', labelBn: 'বন্যার পাস', note: 'Compared with 18 and 30 Jun', noteBn: '১৮ ও ৩০ জুনের সাথে তুলনা', flood: 'all' },
  { id: 'during2', iso: '2026-07-19', track: 163, label: 'A week later', labelBn: 'এক সপ্তাহ পরে', note: 'Flood still wet on this pass', noteBn: 'এই পাসেও যে বন্যা রয়ে গেছে', flood: 'still' },
]

// stats.json has no Bangla names; they are added here.
const BN_NAMES = {
  anowara: 'আনোয়ারা', bakalia: 'বাকলিয়া', banshkhali: 'বাঁশখালী', 'bayejid-bostami': 'বায়েজিদ বোস্তামী',
  boalkhali: 'বোয়ালখালী', chandanaish: 'চন্দনাইশ', chandgaon: 'চান্দগাঁও', 'chittagong-port': 'চট্টগ্রাম বন্দর',
  'double-mooring': 'ডবলমুরিং', fatikchhari: 'ফটিকছড়ি', halishahar: 'হালিশহর', hathazari: 'হাটহাজারী',
  khulshi: 'খুলশী', kotwali: 'কোতোয়ালী', lohagara: 'লোহাগাড়া', mirsharai: 'মীরসরাই', pahartali: 'পাহাড়তলী',
  panchlaish: 'পাঁচলাইশ', patenga: 'পতেঙ্গা', patiya: 'পটিয়া', rangunia: 'রাঙ্গুনিয়া', raozan: 'রাউজান',
  sandwip: 'সন্দ্বীপ', satkania: 'সাতকানিয়া', sitakunda: 'সীতাকুণ্ড',
}
const BN_DISTRICTS = { Chattogram: 'চট্টগ্রাম', Feni: 'ফেনী' }

// hidden: km² of open flood NISAR saw on 12 Jul that the 16 Jul C-band map did not show
// both:   km² of open flood seen by both
// people: WorldPop population living within 100 m of the 'hidden' cells (an upper bound)
// agree:  'both-dates' = drained within a week (no longer dark on 19 Jul);
//         'one-date'   = still wet on 19 Jul, or that pass does not cover the upazila
export const upazilas = reactive([])
export const totals = reactive({ hidden: 0, both: 0, people: 0, hill: 0, people_conservative: 0, under_trees_unverified_km2: 0, drained_pct: null })
export const method = reactive({})
export const modelComparison = reactive({ models: [], test: {}, pipeline_uses: '' })
export const loadState = reactive({ ok: false, error: null })

// Risk maps (pipeline/11_flood_risk.py and 12_landslide_risk.py): likelihood maps, not forecasts.
// risk.flood / risk.landslide hold the per-upazila tables, class cut-offs and validation numbers;
// overlays hold each map image and the lon/lat of its four corners, for MapLibre's image source.
export const risk = reactive({ flood: null, landslide: null })
export const riskOverlays = reactive({ flood: null, landslide: null })
export const RISK_CLASSES = ['low', 'medium', 'high', 'very high']

export const agreeLabel = {
  'both-dates': 'Drained within a week',
  'one-date': 'Still wet on 19 July or not covered',
}

export const agreeLabelBn = {
  'both-dates': 'এক সপ্তাহের মধ্যে পানি নেমে গেছে',
  'one-date': '১৯ জুলাইও ভেজা, অথবা কভারেজ নেই',
}

// Context figures from UN Bangladesh Situation Report #2 (23 Jul 2026) — real, cited.
export const sitrep = {
  affected: 1280000,
  deaths: 59,
  districts: 7,
  source: 'UN Bangladesh Situation Report #2, 23 Jul 2026',
}

export const viewport = { center: [91.98, 22.4], zoom: 8.8 }

async function getJson(url) {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`)
  return res.json()
}

// Risk maps load in the background; the pages that use them react when they arrive.
async function loadRisk() {
  const r = await getJson(DATA_URLS.risk).catch(() => null)
  for (const key of ['flood', 'landslide']) {
    const block = r?.[key]
    if (!block?.overlay) continue
    const bounds = await getJson(`/data/${block.overlay.bounds}`).catch(() => null)
    if (!bounds) continue
    risk[key] = block
    riskOverlays[key] = { url: `/data/${block.overlay.image}`, coordinates: bounds.coordinates }
  }
}

// Called once from main.js before the app mounts, so pages can read the arrays directly.
export async function loadResults() {
  try {
    const [stats, models] = await Promise.all([getJson(DATA_URLS.stats), getJson(DATA_URLS.models).catch(() => null)])
    upazilas.splice(
      0,
      upazilas.length,
      ...stats.upazilas.map((u) => ({ ...u, bn: u.bn || BN_NAMES[u.id] || u.name, districtBn: u.districtBn || BN_DISTRICTS[u.district] || u.district })),
    )
    Object.assign(totals, stats.totals)
    Object.assign(method, stats.method)
    if (models) Object.assign(modelComparison, models)
    loadState.ok = true
    loadRisk() // not awaited: the risk maps are optional and must not delay the first paint
  } catch (e) {
    // The pages still render (with no rows) and say that the figures did not load
    loadState.error = String(e?.message ?? e)
    console.error('MeghBhed results did not load:', e)
  }
}

export function formatInt(n) {
  return Math.round(n).toLocaleString('en-US')
}

const bnDigits = '০১২৩৪৫৬৭৮৯'
export function toBanglaDigits(str) {
  return String(str).replace(/\d/g, (d) => bnDigits[d])
}
