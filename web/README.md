# MeghBhed web

The MeghBhed website: a swipe flood map, upazila figures with CSV/KML export, and a Bangla/English assistant.

> [!IMPORTANT]
> This is a **concept demo**. Every figure and flood polygon comes from [`src/data/concept.js`](src/data/concept.js) and is **illustrative**. Real values will come from the offline pipeline (`stats.json` and GeoJSON) built at the hackathon on 13–14 Nov 2026.

## Run it

Needs Node.js 20.19 or newer.

```bash
npm install
npm run dev        # dev server at http://localhost:5173
npm run build      # production build in dist/
npm run preview    # serve the production build
npm run test:e2e   # Playwright tests (uses your installed Chrome)
```

## Stack

Vue 3 and Vue Router · MapLibre GL JS · Tailwind CSS 4 · Vite · Playwright with axe-core for accessibility checks.

## Where things are

| Path | What it is |
| --- | --- |
| `src/views/` | Pages: Home, Map, Statistics (figures), Assistant, NotFound |
| `src/components/SwipeMap.vue` | The C-band vs NISAR swipe map |
| `src/data/concept.js` | Illustrative upazila figures and generated flood shapes |
| `src/data/assistant.js` | Rule-based stand-in for the grounded AI assistant; no network calls |
| `src/messages.js` | All interface text, in English and Bangla |
| `src/i18n.js` | Language switch and Bangla number and date formatting |
| `tests/` | Playwright end-to-end tests |
| `vercel.json` | Sends every path to `index.html`, so links like `/map?u=fatikchhari` work on reload |

## Swapping in real data

At the hackathon, replace `src/data/concept.js` with data loaded from the pipeline's `stats.json` and GeoJSON, keeping the same field names (`hidden`, `both`, `people`, `agree`, `hill`). Then remove the "illustrative" and "concept" labels: search `src/messages.js` for `illustrative` and `concept`, and remove the on-map label in `SwipeMap.vue`.
