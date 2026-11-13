# MeghBhed web

The MeghBhed website: a swipe flood map, upazila figures with CSV/KML export, and a Bangla/English assistant.

> [!IMPORTANT]
> The figures and flood polygons are **provisional results** from the offline pipeline (`pipeline/`), read from [`public/data/`](public/data/): `stats.json`, `flood.geojson`, `flood_preview.geojson` (a light copy for the landing page), `hill_risk.geojson` and `model_comparison.json`. They are loaded by [`src/data/results.js`](src/data/results.js).

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
| `src/data/results.js` | Loads the pipeline's `stats.json`, `model_comparison.json` and `risk.json` before the app mounts; adds Bangla names |
| `src/views/Validation.vue` | "How well it works" (`/validation`): model scores, independent tests and SHAP rankings from `model_comparison.json` |
| `src/data/assistant.js` | Rule-based stand-in for the grounded AI assistant; no network calls |
| `src/messages.js` | All interface text, in English and Bangla |
| `src/i18n.js` | Language switch and Bangla number and date formatting |
| `tests/` | Playwright end-to-end tests |
| `vercel.json` | Sends every path to `index.html`, so links like `/map?u=fatikchhari` work on reload |

## Swapping in real data

To refresh the data, re-run the pipeline (`python pipeline/run_all.py --from 3`, then `python pipeline/10_flood_models.py`); it rewrites the files in `public/data/`. The end-to-end tests assert the current figures, so update them after a new run.

## The assistant and external AI services

"Ask MeghBhed" sends each question to `/api/ask`, a serverless function ([`api/ask.js`](api/ask.js), logic in [`server/`](server/)). It asks an external language model, checks the answer, and falls back to the built-in keyword helper when no service is configured or every service fails. With no keys set, the app works exactly as before.

### How an answer is kept honest

- The model is given only a compact facts block built from `public/data/stats.json`, `risk.json` and `model_comparison.json`, and told to answer from nothing else.
- **Grounding check:** the server extracts every number of two or more digits from the answer and confirms each appears in the facts block (thousands separators, Bangla digits and rounding to fewer decimals are allowed). If any number is not found, the answer is thrown away and the next service is tried.
- The check covers numbers, not wording. A small model can still phrase something wrongly; a larger model gives better wording, especially in Bangla.

### Environment variables

Copy [`.env.example`](.env.example) to `.env.local` and fill in the keys you have. A service is used only when its key is set.

| Service | Key | Model variable | Default model |
| --- | --- | --- | --- |
| Groq | `GROQ_API_KEY` | `GROQ_MODEL` | `openai/gpt-oss-20b` |
| Google Gemini | `GEMINI_API_KEY` | `GEMINI_MODEL` | `gemini-3.1-flash-lite` |
| OpenAI | `OPENAI_API_KEY` | `OPENAI_MODEL` | `gpt-5-nano` |
| NVIDIA (free models) | `NVIDIA_API_KEY` | `NVIDIA_MODELS` (comma-separated) | `minimaxai/minimax-m3.1-flash`, then `nvidia/nemotron-3.5-bolt-e4b`, then `nvidia/nemotron-3.5-lightning-30b-a3b` |
| Anthropic | `ANTHROPIC_API_KEY` | `ANTHROPIC_MODEL` | `claude-haiku-5-5` |
| OpenRouter | `OPENROUTER_API_KEY` | `OPENROUTER_MODEL` | `openai/gpt-oss-20b` |
| Perplexity | `PERPLEXITY_API_KEY` | `PERPLEXITY_MODEL` | `sonar` |
| Any OpenAI-compatible router | `CUSTOM1_API_KEY` (also `CUSTOM2_`, `CUSTOM3_`) | `CUSTOM1_MODEL` | none: set `CUSTOM1_BASE_URL` (ending in `/v1`), `CUSTOM1_MODEL` and, if you like, `CUSTOM1_NAME` |

`LLM_ORDER` sets the order to try; the default starts with `nvidia`. Services without a key are skipped.

**NVIDIA's free models.** One NVIDIA key gives a chain of free models, each tried in turn: if one is rate-limited (NVIDIA's free tier answers HTTP 429 when busy), times out or gives an ungrounded answer, the next is tried. Set `NVIDIA_MODELS` to change the list. Of the 83 models the key could list in November 2026, these three answered reliably in English and Bangla; most others returned 404 or timed out. NVIDIA models are asked to skip their hidden "thinking" step, which otherwise used up the answer's token budget.

Keys are read only on the server. None has the `VITE_` prefix, so Vite never puts one in the browser bundle. `.env`, `.env.local` and `.env.*.local` are git-ignored; only `.env.example` (names, no values) is tracked.

### Fallback

Each service gets 8 seconds, and the whole chain stops after 17 seconds so the page (which waits 20) always gets a reply. On a timeout, a network error, a 4xx or 5xx reply (including "out of credit" and "rate limited"), an empty answer, or an answer that fails the grounding check, the next service in the order is tried. So when one key runs out, the next one takes over without any change. If all fail, the page answers with the built-in helper. The visitor never sees a raw error.

The page shows only the answer: no source line, no model name and no model picker. Greetings, thanks and goodbyes get a short friendly reply, in English or Bangla, from the AI service or from the built-in helper.

Limits: questions over 500 characters are rejected; answers are capped at about 300 tokens; temperature 0.2 where the model accepts it; 20 requests per 5 minutes per IP (in memory, per server instance); same-origin requests only.

### Voice input (NVIDIA speech-to-text)

When `NVIDIA_API_KEY` (or a separate `NVIDIA_ASR_API_KEY`) is set, the microphone records clean 16 kHz mono audio in the browser (with echo cancellation and noise suppression), stops by itself 1.6 seconds after you stop speaking (or after 30 seconds, or when you press stop), and sends it to `/api/transcribe` ([`api/transcribe.js`](api/transcribe.js), logic in [`server/transcribe-core.js`](server/transcribe-core.js)). That calls NVIDIA's hosted Whisper Large V3 over gRPC, in English or Bangla depending on the voice-language switch. The text appears in the input box to check before sending. Without a key, the browser's own speech recognition is used as before.

`NVIDIA_ASR_FUNCTION_ID` selects a different hosted speech model; the default is Whisper Large V3's (`b702f636-f60c-4a3d-a6f4-f3568c13bd7d`). The protocol files in `server/riva/` are NVIDIA's own (MIT licence). Limits: 30 seconds per recording, same-origin only, the same per-IP rate limit as the assistant.

### Switching a model

Set the service's model variable, for example `GROQ_MODEL=...`, in `.env.local` or in Vercel, and restart or redeploy. No code change is needed. Models that reason before answering (`gpt-oss-*`, `gpt-5*`) are given extra tokens for that reasoning.

### Running locally

```
npm run dev
```

The dev server runs the same handler as the Vercel function and reads `web/.env.local`, so the Vercel CLI is not needed. It restarts by itself when `.env.local` changes.

### Adding the keys in Vercel

Project → Settings → Environment Variables. Add each key name from the table (and `LLM_ORDER` if you want a different order), for the Production and Preview environments, then redeploy. The project root in Vercel must be `web/`.

### Tests

```
npm run test:unit    # server logic with fetch mocked: fallback order, grounding check, limits
npm run test:e2e     # browser tests; /api/ask is stubbed, so no real service is ever called
```
