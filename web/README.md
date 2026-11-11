# MeghBhed web

The MeghBhed website: a swipe flood map, upazila figures with CSV/KML export, and a Bangla/English assistant.

> [!IMPORTANT]
> The figures and flood polygons are **provisional results** from the offline pipeline (`pipeline/`), read from [`public/data/`](public/data/): `stats.json`, `flood.geojson`, `hill_risk.geojson` and `model_comparison.json`. They are loaded by [`src/data/results.js`](src/data/results.js).

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
| `src/data/results.js` | Loads the pipeline's `stats.json` and `model_comparison.json` before the app mounts; adds Bangla names |
| `src/data/assistant.js` | Rule-based stand-in for the grounded AI assistant; no network calls |
| `src/messages.js` | All interface text, in English and Bangla |
| `src/i18n.js` | Language switch and Bangla number and date formatting |
| `tests/` | Playwright end-to-end tests |
| `vercel.json` | Sends every path to `index.html`, so links like `/map?u=fatikchhari` work on reload |

## Swapping in real data

To refresh the data, re-run the pipeline (`python pipeline/run_all.py --from 3`, then `python pipeline/10_flood_models.py`); it rewrites the files in `public/data/`. The end-to-end tests assert the current figures, so update them after a new run.
