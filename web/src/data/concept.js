// Concept data for the pre-hackathon demo.
// Every figure and polygon here is ILLUSTRATIVE. Real values come from the
// offline pipeline (stats.json + GeoJSON) built on 13–14 Nov 2026.

export const IS_CONCEPT = true

export const scenes = [
  { id: 'before', iso: '2026-06-30', track: 69, label: 'Before', labelBn: 'আগে', note: 'Pre-flood baseline', noteBn: 'বন্যার আগের ভিত্তি', scale: 0 },
  { id: 'during1', iso: '2026-07-12', track: 69, label: 'During', labelBn: 'চলাকালীন', note: 'Compared with 30 Jun', noteBn: '৩০ জুনের সাথে তুলনা', scale: 1 },
  { id: 'during2', iso: '2026-07-19', track: 163, label: 'During', labelBn: 'চলাকালীন', note: 'Compared with 25 Jun', noteBn: '২৫ জুনের সাথে তুলনা', scale: 0.82 },
]

// hidden: km² NISAR-only (under canopy, not water in DSWx-S1)
// both:   km² flagged by both C-band and L-band (open water)
// people: WorldPop 100 m count inside hidden-flood pixels
// agree:  'both-dates' = flagged on 12 and 19 Jul; 'one-date' = only one NISAR date
export const upazilas = [
  { id: 'fatikchhari', name: 'Fatikchhari', bn: 'ফটিকছড়ি', district: 'Chattogram', districtBn: 'চট্টগ্রাম', center: [91.79, 22.70], hidden: 5.2, both: 7.9, people: 24560, agree: 'both-dates', hill: 4 },
  { id: 'hathazari', name: 'Hathazari', bn: 'হাটহাজারী', district: 'Chattogram', districtBn: 'চট্টগ্রাম', center: [91.81, 22.51], hidden: 3.8, both: 6.1, people: 18240, agree: 'both-dates', hill: 2 },
  { id: 'fulgazi', name: 'Fulgazi', bn: 'ফুলগাজী', district: 'Feni', districtBn: 'ফেনী', center: [91.43, 23.14], hidden: 3.5, both: 8.7, people: 16820, agree: 'one-date', hill: 0 },
  { id: 'parshuram', name: 'Parshuram', bn: 'পরশুরাম', district: 'Feni', districtBn: 'ফেনী', center: [91.445, 23.215], hidden: 4.1, both: 9.4, people: 15130, agree: 'both-dates', hill: 0 },
  { id: 'chhagalnaiya', name: 'Chhagalnaiya', bn: 'ছাগলনাইয়া', district: 'Feni', districtBn: 'ফেনী', center: [91.51, 23.03], hidden: 2.9, both: 6.2, people: 12390, agree: 'both-dates', hill: 1 },
  { id: 'raozan', name: 'Raozan', bn: 'রাউজান', district: 'Chattogram', districtBn: 'চট্টগ্রাম', center: [91.92, 22.54], hidden: 2.4, both: 4.3, people: 11970, agree: 'one-date', hill: 1 },
  { id: 'mirsharai', name: 'Mirsharai', bn: 'মীরসরাই', district: 'Chattogram', districtBn: 'চট্টগ্রাম', center: [91.57, 22.78], hidden: 1.9, both: 5.6, people: 8310, agree: 'one-date', hill: 1 },
  { id: 'sitakunda', name: 'Sitakunda', bn: 'সীতাকুণ্ড', district: 'Chattogram', districtBn: 'চট্টগ্রাম', center: [91.67, 22.62], hidden: 1.1, both: 2.8, people: 5480, agree: 'both-dates', hill: 3 },
]

export const agreeLabel = {
  'both-dates': 'Likely missed by C-band',
  'one-date': 'Possibly flooded',
}

export const agreeLabelBn = {
  'both-dates': 'সম্ভবত C-band মিস করেছে',
  'one-date': 'সম্ভবত প্লাবিত',
}

export const totals = upazilas.reduce(
  (t, u) => ({
    hidden: t.hidden + u.hidden,
    both: t.both + u.both,
    people: t.people + u.people,
    hill: t.hill + u.hill,
  }),
  { hidden: 0, both: 0, people: 0, hill: 0 },
)

// Context figures from UN Bangladesh Situation Report #2 (23 Jul 2026) — real, cited.
export const sitrep = {
  affected: 1280000,
  deaths: 59,
  districts: 7,
  source: 'UN Bangladesh Situation Report #2, 23 Jul 2026',
}

export const viewport = { center: [91.64, 22.86], zoom: 8.7 }

// ---- illustrative geometry ---------------------------------------------------

function mulberry32(seed) {
  return function () {
    let t = (seed += 0x6d2b79f5)
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const LAT_K = 1 / 111.0
const lngK = (lat) => 1 / (111.0 * Math.cos((lat * Math.PI) / 180))

// Irregular blob around a point; r in km
function blob([cx, cy], rKm, rand, verts = 14) {
  const ring = []
  const phase = rand() * Math.PI * 2
  const stretch = 0.6 + rand() * 0.8
  for (let i = 0; i < verts; i++) {
    const a = (i / verts) * Math.PI * 2
    const r = rKm * (0.6 + rand() * 0.55) * (1 + 0.35 * Math.sin(2 * a + phase))
    ring.push([cx + Math.cos(a) * r * stretch * lngK(cy), cy + Math.sin(a) * r * LAT_K])
  }
  ring.push(ring[0])
  return [ring]
}

const feature = (geometry, properties = {}) => ({ type: 'Feature', geometry, properties })
const collection = (features) => ({ type: 'FeatureCollection', features })

// Build illustrative layers for a scene. scale 0 = pre-flood baseline (no flood drawn).
export function buildLayers(sceneId) {
  const scene = scenes.find((s) => s.id === sceneId) ?? scenes[1]
  const s = scene.scale

  // Permanent rivers come from the basemap; only flood extent is drawn here.
  const openWater = []
  const hidden = []
  if (s > 0) {
    for (const u of upazilas) {
      const r2 = mulberry32(u.id.length * 977 + Math.round(u.hidden * 100))
      const [cx, cy] = u.center
      // open-water flood (seen by both sensors): a few merged lobes
      const lobes = 2 + Math.round(u.both / 2.5)
      for (let i = 0; i < lobes; i++) {
        const c = [cx + (r2() - 0.5) * 0.06, cy + (r2() - 0.5) * 0.08]
        openWater.push(feature({ type: 'Polygon', coordinates: blob(c, (0.7 + r2() * 0.8) * s, r2) }, { kind: 'open', upazila: u.id }))
      }
      // hidden flood: small homestead patches around the open water, under trees
      const patches = Math.round(u.hidden * 3 * s)
      for (let i = 0; i < patches; i++) {
        const ang = r2() * Math.PI * 2
        const d = 0.025 + r2() * 0.045
        const c = [cx + Math.cos(ang) * d, cy + Math.sin(ang) * d * 1.2]
        hidden.push(
          feature(
            { type: 'Polygon', coordinates: blob(c, (0.25 + r2() * 0.45) * (0.7 + 0.3 * s), r2, 11) },
            { kind: 'hidden', upazila: u.id, agree: u.agree },
          ),
        )
      }
    }
  }

  // Hill Risk: places to check on the ground, east of the floodplain
  const hillRand = mulberry32(4242)
  const hill = []
  for (const u of upazilas) {
    for (let i = 0; i < u.hill; i++) {
      hill.push(
        feature(
          { type: 'Point', coordinates: [u.center[0] + 0.03 + hillRand() * 0.06, u.center[1] + (hillRand() - 0.5) * 0.08] },
          { upazila: u.id, slope: Math.round(24 + hillRand() * 16), rain: Math.round(310 + hillRand() * 260) },
        ),
      )
    }
  }

  return {
    openWater: collection(openWater),
    hidden: collection(hidden),
    hill: collection(hill),
  }
}

export function formatInt(n) {
  return Math.round(n).toLocaleString('en-US')
}

const bnDigits = '০১২৩৪৫৬৭৮৯'
export function toBanglaDigits(str) {
  return String(str).replace(/\d/g, (d) => bnDigits[d])
}
