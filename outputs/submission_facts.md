# MeghBhed: facts for the submission form (Use of AI, References)

Collected 13 Nov 2026 from the working tree on branch `feat/open-flood-results` (including uncommitted changes). Read only: no file other than this one was changed. No key, password or token value appears here; for keys, only variable names are given.

---

# PART A. USE OF AI

## A1. AI inside the product

### "Ask MeghBhed" assistant (language models)

- **Does it call external language models?** Yes. The browser posts the question to `/api/ask`, a Vercel serverless function, which calls an external model and checks the answer. verified in: `web/api/ask.js` (lines 1–5), `web/server/ask-core.js` (lines 1–3)
- **Providers and default models coded:** verified in: `web/server/ask-core.js` lines 18–34
  - NVIDIA (`integrate.api.nvidia.com/v1`): a chain of free hosted models tried in turn: `minimaxai/minimax-m3.1-flash`, `nvidia/nemotron-3.5-bolt-e4b`, `nvidia/nemotron-3.5-lightning-30b-a3b`. Single-model default: `nvidia/nemotron-3.5-lightning-30b-a3b`. NVIDIA's "thinking" mode is switched off (`chat_template_kwargs.enable_thinking = false`).
  - Groq: `openai/gpt-oss-20b`
  - Google Gemini: `gemini-3.1-flash-lite`
  - OpenAI: `gpt-5-nano`
  - Anthropic: `claude-haiku-5-5`
  - OpenRouter: `openai/gpt-oss-20b`
  - Perplexity: `sonar`
  - Up to three "custom" OpenAI-compatible routers (`CUSTOM1_` to `CUSTOM3_`), with no default model.
- **LLM_ORDER default (in code):** `nvidia, groq, gemini, openai, anthropic, openrouter, perplexity, custom1, custom2, custom3`. verified in: `web/server/ask-core.js` line 27; the same in `web/.env.example` line 6
- **LLM_ORDER set locally:** `nvidia, openrouter, custom1, custom2, custom3, groq, gemini, openai, anthropic, perplexity`. verified in: `web/.env.local` (this line only)
- **Key variable names in `web/.env.local`** (names only):
  - Set (non-empty): `NVIDIA_API_KEY`, `OPENROUTER_API_KEY`, `PERPLEXITY_API_KEY`, `CUSTOM1_API_KEY`, `CUSTOM2_API_KEY`, `CUSTOM3_API_KEY`. Also `LLM_ORDER` and `CUSTOM1_NAME` to `CUSTOM3_NAME`, which are not keys.
  - Empty: `GROQ_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`; also `OPENROUTER_MODEL`, `PERPLEXITY_MODEL`, `CUSTOM1_BASE_URL` to `CUSTOM3_BASE_URL`, and `CUSTOM1_MODEL` to `CUSTOM3_MODEL`.
  - Effect: the three custom routers are not active, because a custom provider needs `_API_KEY`, `_BASE_URL` and `_MODEL` all set (`ask-core.js` lines 40–44). Locally the active chain is the three NVIDIA models, then OpenRouter, then Perplexity.
  - verified in: `web/.env.local`, values not read out
  - The repo-root `.env.local` holds only `VERCEL_OIDC_TOKEN` (a Vercel CLI token, not an LLM key). verified in: `.env.local`
- **Does the deployed site have keys?** Can't tell. The Vercel project is `meghbhed-prototype` (`.vercel/project.json`). Listing its environment variables failed: the Vercel connector returned "403 forbidden, not authorized for this team scope", and the Vercel CLI is not installed here.
- **Fallback behaviour:** verified in: `web/server/ask-core.js` lines 13–14, 77–119 and 153–165; `web/src/data/assistant.js` lines 1–2
  1. Providers are tried in order.
  2. Each provider gets 8 s. The whole chain stops after 17 s, and a provider is skipped when less than 1.5 s is left.
  3. A provider's answer is rejected if it is empty, an error (including HTTP 429), or "ungrounded". Ungrounded means it contains a number of two or more digits, or a day-and-month date, that is not in the facts block (`web/server/facts.js` lines 108–121).
  4. If no provider gives a grounded answer, or no key is set, the server returns `fallback: true`. The page then answers with its built-in, rule-based keyword helper (`web/src/data/assistant.js`). That helper makes no network calls and answers only from the pipeline's figures.
  5. Other limits: same-origin requests only; 20 requests per 5 minutes per IP; questions of at most 500 characters; answers of about 300 tokens; temperature 0.2.
- **Exactly what the model is given:** a system prompt with fixed rules and a "facts block". The facts block is built only from three files in `web/public/data/`. verified in: `web/server/facts.js` lines 18–80; rules in `web/server/ask-core.js` lines 66–80
  - `stats.json`:
    - `method.dates.nisar_flood_pass`, `method.dates.cband_map` and `method.rule`.
    - `totals.hidden`, `both`, `people`, `people_conservative`, `people_within_100m_all_flood`, `drained_pct`, `under_trees_unverified_km2` and `hill`.
    - Per upazila: `name`, `hidden`, `both`, `people`, `people_conservative`, `drained_pct`, `agree` (shown as a status) and `hill`; also the count of upazilas with `hidden > 0`.
  - `model_comparison.json`:
    - `tuned[]`, per model: `model`, `precision`, `recall`, `f1`, `accuracy`, `test_flagged_pct_near_flooded_points`, `test_flagged_pct_near_dry_points` and `flagged_km2`.
    - `pipeline_uses`, which marks the model used on the map.
  - `risk.json`:
    - Flood: `flood.chosen_model`, `flood.totals.high_or_very_high_km2` and `high_or_very_high_people`; per upazila (up to 15, those with people above 0) `name`, `high_or_very_high_people` and `high_or_very_high_km2`.
    - Landslide: `landslide.totals.high_or_very_high_km2` and `people_within_100m_high_or_very_high`; per upazila (up to 15) `name`, `people_within_100m_high_or_very_high`, `high_km2` and `very_high_km2`.
  - Fixed caveats written into the block: provisional results, the 12 Jul vs 16 Jul four-day gap, people figures as an upper bound, under-tree flooding unverified, risk maps are likelihood maps and not forecasts, and Hill Risk points are not confirmed landslides.
  - The model also gets the user's question and the UI language. Nothing else is sent: no raw rasters, no coordinates, no other user data.

### Speech-to-text for the microphone (also an AI model)

- When `NVIDIA_API_KEY` (or `NVIDIA_ASR_API_KEY`) is set, recorded audio (16 kHz mono PCM, at most 30 s) is sent to `/api/transcribe`. That function calls NVIDIA's hosted **Whisper Large V3** (OpenAI's model, hosted on build.nvidia.com) over gRPC (Riva API).
  - Endpoint: `grpc.nvcf.nvidia.com:443`.
  - Default function id: `b702f636-f60c-4a3d-a6f4-f3568c13bd7d`, which can be changed with `NVIDIA_ASR_FUNCTION_ID`.
  - Language is `en` or `bn`.
- Without a key, the browser's own `SpeechRecognition` is used instead.
- verified in: `web/server/transcribe-core.js` lines 1–58; `web/README.md` lines 81–85; `web/src/components/PromptInput.vue`

### Machine-learning models in the pipeline

None of the trained models is used for the live flood map. The live map uses the threshold rule (`DETECTOR = "threshold"` in `pipeline/config.py` line 96). The only trained model whose output is on the live site is the flood-risk Random Forest. verified in: `pipeline/config.py`; `web/public/data/` (holds `flood_risk.png` and `risk.json` with `"chosen_model": "random_forest"`)

| Script | Model types | Library | Input data | Predicts | On the live site? |
| --- | --- | --- | --- | --- | --- |
| `05_classify.py` | Random Forest (300 trees), LightGBM (300 rounds); baseline = HH-rise rule | scikit-learn, lightgbm | 10 m NISAR GCOV features: `hh_b, hv_b, hh_d, hv_d, dhh, dhv, ratio_d, tex_hh` plus `slope` and `hand` (`config.FEATURES`), at pixels within 30 m of `labels/sites.csv` train sites, plus automatic dry pixels on tree cover with HAND > 20 m | Flooded under trees (1) or dry (0) per pixel | **No.** Optional step, run only with `run_all.py --ml`. Results only in `outputs/model_comparison.csv` and `feature_importance.csv`. `work/flood_ml_*.tif` exist from an earlier run but are not used (`DETECTOR = "threshold"`) |
| `10_flood_models.py` | Threshold rule, logistic regression (standardised, balanced), Random Forest (200 trees), LightGBM (300 rounds) | scikit-learn, lightgbm, shap | 30 m cells, NISAR radar only: `hh_b, hv_b, hh_d, hv_d, dhh, dhv, ratio_d`. 95,091 training cells. Positives: new open water on DSWx-S1 16 Jul. Negatives: high flat ground, permanent June water, and the no-flood pair 18 Jun → 30 Jun | Open flood on 12 Jul (yes/no) | **Comparison only.** Shown on the Validation page (`web/public/data/model_comparison.json`); the map keeps the rule |
| `11_flood_risk.py` | Logistic regression, Random Forest (200 trees, chosen), LightGBM (400 rounds); isotonic calibration | scikit-learn, lightgbm, shap | 30 m terrain only: `hand, hand_min90, elev, elev_min90, slope, relief_1km, dist_june_water, dist_coast` (Copernicus DEM, GLO-30 HAND, DSWx June water) | Probability that a cell flooded on 12 Jul (labels 1 and 2 of the comparison map), i.e. flood susceptibility on open land | **Yes:** the Random Forest output is the "Flood risk on open land" layer (`flood_risk.png`, `risk.json`). The other two models are comparison only |
| `12_landslide_risk.py` | **No trained model.** A judgement-weighted index (slope 0.40, relief 0.20, rain 0.20, land cover 0.10, nearness to built-up land 0.10) | numpy, scipy | Copernicus DEM slope and relief, IMERG 5–18 Jul total, WorldCover. Checked against GLC points, LHASA and the NASA susceptibility map | Landslide susceptibility class (rank-based) | **Yes** (landslide risk layer), but it is not ML |
| `13_tree_flood.py` | Threshold on coherence loss; logistic regression, Random Forest (300 trees), LightGBM (200 rounds) | scikit-learn, lightgbm, h5py | NISAR GUNW HH coherence (18→30 Jun, 30 Jun→12 Jul) plus backscatter change: `coh_before, coh_flood, coh_change, dhh, dhv, dratio`; train/test sites from `labels/sites.csv` | Flooded under trees (yes/no) per 30 m tree cell | **No.** Failed two of four pre-set criteria (`outputs/tree_flood_validation.json`: `"accepted": false`), so nothing is written for the app |

verified in: the docstrings and `make_models()` of each script (`05_classify.py` lines 1–16 and 114–121; `10_flood_models.py` lines 1–32 and 57, 130–137; `11_flood_risk.py` lines 1–24, 48 and 64–71; `12_landslide_risk.py` lines 1–25; `13_tree_flood.py` lines 1–22, 61 and 170–176); `docs/METHOD.md` sections 3.2, 10, 11 and 12; `pipeline/run_all.py` lines 16–27

### SHAP (explainable AI)

- `10_flood_models.py`: `shap.TreeExplainer` on the **LightGBM** (5,000 cells) and **Random Forest** (500 cells) benchmark models for the 12 Jul open flood. The cells are a random sample of that script's training cells (NISAR radar features). Outputs: `outputs/flood_shap_importance.csv`, beeswarm and bar plots, and two waterfall examples (an agreed flood cell and a false alarm) in `outputs/xai/`. The logistic regression is explained by its standardised coefficients instead (`outputs/flood_logistic_coefficients.csv`). verified in: `pipeline/10_flood_models.py` lines 63 and 322–378; `docs/METHOD.md` section 11
- `11_flood_risk.py`: `shap.TreeExplainer` on the **LightGBM** (5,000 cells) and **Random Forest** (1,000 cells) flood-risk models. The cells are a random sample of the open-land training cells (terrain features). Outputs: `outputs/xai/flood_shap_*.png` and `flood_shap_mean_abs.csv`. verified in: `pipeline/11_flood_risk.py` lines 56–57 and 251–276; `docs/METHOD.md` section 10.1
- `12_landslide_risk.py` writes "index contributions" (`outputs/xai/landslide_index_contributions.*`). These are the weighted factor shares, not SHAP. verified in: `pipeline/12_landslide_risk.py` docstring

## A2. AI used to build the project

- **README "Use of AI" table.** verified in: `README.md` lines 316–324
  - "Claude (Anthropic): research, proposal and script drafting; prescreening-video animation and soundtrack generated as code."
  - "ChatGPT / Codex, GitHub Copilot: coding assistance during the hackathon (planned)."
  - "In-app LLM: answers user questions using only MeghBhed's computed `stats.json`."
  - "All voices in the video are real team members."
- **Git history:** 17 commits.
  - Authors: Prottoy Saha Dip (15) and shuvosinghpartho (2).
  - **No `Co-Authored-By` lines, and no commit message mentions any AI tool.**
  - The only AI-tool-related trace is commit `522beb0` ("chore: add markdownlint configuration"), whose message says "Ignore the local .kilo/ folder". `.markdownlint-cli2.jsonc` line 9 ignores `.kilo/**`.
  - `.kilo/` is the working folder of the Kilo Code AI coding extension. It holds only a `.gitignore` (listing `agent-manager.json`, among others), so it shows the tool was installed, not what it produced.
  - verified in: `git log --all`; `.kilo/.gitignore`; `.markdownlint-cli2.jsonc`
- **Not recorded in the repo, but true of this work:** much of the current pipeline (steps 10–13, risk maps, label-build scripts), the web app's assistant, speech-to-text, tests and docs were written or edited with **Claude Code (Anthropic)** in this working session. The resulting commits were deliberately made without AI co-author trailers, at the user's request. verified in: this Claude Code session (not a repo file). The README "Use of AI" table does not mention Claude Code for coding.
- **Code comments, docs, labels:** no comment, doc or label file says text, labels or images were AI-generated. verified in: `git grep` over all tracked files and `grep` over untracked files (excluding `data/`, `work/`, `node_modules/`)
- **How `labels/sites.csv` was built:** five scripts in `labels/build/`, run in this order. verified in: `labels/README.md` lines 97–105 and the scripts' docstrings
  1. `build_reference.py`: the new-floodwater layer, from OPERA DSWx-S1 only. Water on 16 Jul, but not on 7, 9, 19 or 21 Jun; WorldCover classes 80, 90 and 95 excluded.
  2. `train_sites.py`: 319 train sites (74 flooded, 245 dry), from WorldCover tree cover, GLO-30 HAND ≤ 5 m and the new-floodwater layer. Random sampling with a fixed seed (42). **No NISAR data was read.**
  3. `geocode.py`: geocodes the report places listed in `places.py` with **Nominatim (OpenStreetMap)** (`nominatim.openstreetmap.org/search`, 1 request per second, user agent `flood-label-geocoder/1.0`). A place is kept only if it falls inside the expected upazila (geoBoundaries ADM3). Result: 28 places geocoded (14 flooded, 14 dry).
  4. `test_points.py`: up to 3 tree points (HAND ≤ 5 m) within 500 m of each place, giving 84 test points (42 flooded, 42 dry).
  5. `write_sites.py`: merges both sets and drops train sites within 1 km of a test point.
  - **Web search:** the places and URLs in `labels/build/places.py` came from reports found by searching news and UN/NGO sites. `labels/README.md` lines 91–95 lists the sources searched. No script performs a web search; the search was done by hand or with an assistant, and the repo doesn't record which tool was used.
  - **Geocoding:** yes, Nominatim (OSM), as above.
  - **Reference flood products:** the UNOSAT flood extent of 22 Jul 2026 (Charter activation 1042) was looked for and not found as a downloadable vector, so it is not used (`labels/README.md` line 33).

## A3. Other AI-related items in the repo

- **rembg, ONNX, U²-Net, background removal:** not found, in the working tree, git history (`git log -S rembg`) or image metadata (team photos `web/public/*.jpg`, `docs/assets/banner.jpg`).
- **Generated images (Midjourney, DALL·E, Stable Diffusion, Firefly, Imagen):** not found. No C2PA or AI-tool tags in the JPEG headers.
- **Package names:**
  - `transformers`, `torch`, `onnx`, `onnxruntime`: not found in `environment.yml`, the venv, or `web/package.json`.
  - SDKs for `openai`, `@google/genai`, `@anthropic-ai/sdk` and `groq-sdk`: not installed. The app calls the providers' HTTP APIs directly with `fetch`.
  - Provider names (`openai`, `gemini`, `groq`, `anthropic`, `nvidia`, `perplexity`, `openrouter`) appear only in the assistant code, its tests, `web/README.md` and `web/.env.example`.
- **gRPC protocol files from NVIDIA Riva** (`web/server/riva/riva/proto/*.proto`): used to call the hosted Whisper model; not AI-generated.
- **AI-written text:** the README says Claude drafted research, proposal and script text (above). No file is marked as AI-written.

---

# PART B. REFERENCES

## B1. Datasets

### NISAR L2 GCOV (provisional)

- **Product:** `NISAR_L2_GCOV_PROVISIONAL_V1`, product version 1.0.11, specification 1.5.0 (JPL D-102274), DOI 10.5067/NIL2GCOV-P1.
- **Provider:** NASA/ISRO, NASA JPL; distributed by ASF DAAC.
- **Download base:** `https://nisar.asf.earthdatacloud.nasa.gov/NISAR/NISAR_L2_GCOV_PROVISIONAL_V1/<granule>/<granule>.h5` (Earthdata login).
- **Licence:** "Open, EOSDIS data use policy" (as stated in `docs/DATA.md`; no licence tag in the file).
- **Granules used** (all 8 in `data/nisar/`):
  - `NISAR_L2_PR_GCOV_023_069_A_013_4005_DHDH_A_20260618T232102_20260618T232136_P05023_N_F_J_001`: pair A, second "before" (18 Jun)
  - `NISAR_L2_PR_GCOV_024_069_A_013_4005_DHDH_A_20260630T232101_20260630T232135_P05023_N_F_J_001`: pair A before (30 Jun)
  - `NISAR_L2_PR_GCOV_025_069_A_013_4005_DHDH_A_20260712T232100_20260712T232135_P05023_N_F_J_001`: pair A during, the flood pass (12 Jul)
  - `NISAR_L2_PR_GCOV_028_069_A_013_4005_DHDH_A_20260817T232058_20260817T232133_P05023_N_F_J_001`: pair A "after" (17 Aug)
  - `NISAR_L2_PR_GCOV_023_163_D_077_4005_DHDH_A_20260625T122638_20260625T122713_P05023_N_F_J_001`: pair B before (25 Jun)
  - `NISAR_L2_PR_GCOV_025_163_D_077_4005_DHDH_A_20260719T122637_20260719T122711_P05023_N_F_J_001`: pair B during (19 Jul, the "drained" check)
  - `NISAR_L2_PR_GCOV_024_091_D_077_2005_DHDH_M_20260702T123457_20260702T123531_P05023_N_F_J_001`: pair C before (2 Jul, Feni track)
  - `NISAR_L2_PR_GCOV_025_091_D_077_2005_QPDH_A_20260714T123456_20260714T123512_P05023_F_P_J_001`: pair C during (14 Jul)
- verified in: `pipeline/config.py` lines 27–43; `download_meghbhed_data.sh` lines 38–49; `docs/DATA.md` line 18; HDF5 `identification` metadata; `outputs/stats.json` `method.pairs`

### NISAR L2 GUNW (provisional)

- **Product:** `NISAR_L2_GUNW_PROVISIONAL_V1`, product version 1.0.11, DOI 10.5067/NIL2GUNW-P1 (from the file metadata).
- **Provider:** NASA/ISRO, NASA JPL; distributed by ASF.
- **Download URL:** not found. Only the collection name is recorded, and the download script does not fetch GUNW.
- **Licence:** "Open, EOSDIS data use policy" per `docs/DATA.md`.
- **Granules:**
  - `NISAR_L2_PR_GUNW_023_069_A_013_024_4000_SH_20260618T232102_20260618T232136_20260630T232101_20260630T232135_P05023_N_F_J_001` (18 Jun → 30 Jun)
  - `NISAR_L2_PR_GUNW_024_069_A_013_025_4000_SH_20260630T232101_20260630T232135_20260712T232100_20260712T232135_P05023_N_F_J_001` (30 Jun → 12 Jul)
- Used only by `13_tree_flood.py`.
- verified in: `data/nisar_gunw/`; `pipeline/README.md` line 199; HDF5 metadata

### OPERA DSWx-S1 (C-band comparison), 16 Jul 2026

- **Product:** `OPERA_L3_DSWX-S1_V1`, product version 1.0, software 1.2, DOI 10.5067/OPDSWS1-L3V1.
- **Provider:** NASA JPL OPERA; distributed by PO.DAAC.
- **Licence:** "PO.DAAC data use policy; contains modified Copernicus Sentinel data" (from `docs/DATA.md`; no licence tag in the file).
- **URL:** `https://archive.podaac.earthdata.nasa.gov/podaac-ops-cumulus-protected/OPERA_L3_DSWX-S1_V1/`
- **Files:** tiles T46QCK, T46QCL, T46QDK and T46QDL, stamp `20260716T234703Z_20260725T000947Z_S1C_30_v1.0` (Sentinel-1C), bands B01_WTR, B02_BWTR and B03_CONF (12 files), for example `OPERA_L3_DSWx-S1_T46QCK_20260716T234703Z_20260725T000947Z_S1C_30_v1.0_B01_WTR.tif`. Only B01_WTR is read by the pipeline.
- **Inputs listed in the file metadata:** Copernicus DEM GLO-30 2021, ASF HAND GLO30, ESA WorldCover 2020 v1.0, JRC Global Surface Water 1984–2021, GLAD Global Land Cover 2020.
- verified in: `download_meghbhed_data.sh` lines 51–56; `data/dswx_s1/`; GeoTIFF tags; `docs/DATA.md` line 20

### OPERA DSWx-S1, pre-flood (June water)

- **Product:** same collection, B01_WTR only, Sentinel-1A.
- **Files:** tiles T46QCK, T46QCL, T46QDK and T46QDL, 16 files, on these dates:
  - 7 Jun: `20260607T115550Z_20260826T210530Z_S1A_30_v1.0`
  - 9 Jun: `20260609T234756Z_20260614T065324Z_S1A_30_v1.0`
  - 19 Jun: `20260619T115549Z_20260826T210532Z_S1A_30_v1.0`
  - 21 Jun: `20260621T234756Z_20260828T024807Z_S1A_30_v1.0`
- **Source:** "PO.DAAC, collection `OPERA_L3_DSWX-S1_V1`, found through NASA CMR". The exact download URLs are not recorded, and the download script does not fetch them.
- verified in: `data/dswx_s1_pre/`; `pipeline/README.md` line 196; `labels/README.md` line 28

### GPM IMERG Late, daily (V07)

- **Product:** `GPM_3IMERGDL` V07 (files V07C), DOI 10.5067/GPM/IMERGDL/DAY/07 (also in the file metadata).
- **Provider:** NASA GES DISC.
- **Licence:** "Open, EOSDIS data use policy" (`docs/DATA.md`).
- **Files:** `3B-DAY-L.MS.MRG.3IMERG.20260705-S000000-E235959.V07C.nc4` to `…20260718…`, 14 days (5–18 Jul 2026).
- **URL:** `https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDL.07/2026/07/`
- verified in: `download_meghbhed_data.sh` lines 58–59 and 71–74; `data/imerg/`; netCDF attributes

### LHASA near-real-time nowcast

- **Product:** LHASA 2 NRT hazard. No version tag in the files.
- **Provider:** NASA GSFC.
- **Licence:** "Open" (`docs/DATA.md`).
- **Files:** 11 GeoTIFFs: `20260705T0000.tif` to `20260709T0000.tif` and `20260713T0000.tif` to `20260718T0000.tif`. 10–12 Jul is missing.
- **Source page:** `https://portal.nccs.nasa.gov/datashare/landslides/nrt/hazard/tif/`, downloaded by hand (not scripted).
- **Use:** recorded but not required (`USE_LHASA = False`); used as a comparison check in step 12.
- verified in: `data/lhasa/`; `download_meghbhed_data.sh` lines 84–85; `pipeline/config.py` line 111

### NASA Global Landslide Catalog (GLC)

- **File:** `data/landslide/glc_export.csv`, 11,033 events dated 1988-11-07 to 2017-09-28. Of these, 38 fall in the analysis grid (2007-06-11 to 2017-07-02, saved as `glc_in_grid.csv`), and 19 are in the district.
- **Source used:** `https://data.nasa.gov/docs/legacy/Global_Landslide_Catalog_Export/Global_Landslide_Catalog_Export_rows.csv`. Landing page given in the docs: `https://catalog.data.gov/dataset/global-landslide-catalog-export`.
- **Bounding box used:** 91.2018–92.2566° E, 21.8139–23.3298° N (`data/landslide/bbox.txt`).
- **Provider:** NASA GSFC.
- **Licence:** "NASA terms (accept on export)" (`docs/DATA.md`).
- **Citation requested:** Kirschbaum et al. (2010); Kirschbaum, Stanley and Zhou (2015).
- **Not used:** the newer COOLR catalogue, which could not be fetched.
- verified in: `pipeline/README.md` lines 197 and 201; the CSV itself; `docs/DATA.md` lines 24 and 74; `docs/METHOD.md` section 10.2

### NASA global landslide susceptibility map (2023 update, about 1 km)

- **File:** `data/landslide/susceptibility_2023.tif`, renamed from `global-landslide-susceptibility-map-2-27-23.tif`.
- **URL:** `https://gpm.nasa.gov/sites/default/files/downloads/global-landslide-susceptibility-map-2-27-23.tif`
- **Provider:** NASA (GPM landslides). Licence: not found.
- **Use:** comparison only.
- verified in: `pipeline/README.md` line 198; `pipeline/12_landslide_risk.py` line 55

### ESA WorldCover

- **Product:** 2021 v200 (algorithm V2.0.0).
- **Provider:** ESA.
- **File:** `ESA_WorldCover_10m_2021_v200_N21E090_Map.tif`
- **URL:** `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N21E090_Map.tif`
- **Licence:** CC BY 4.0 (file tag). Required credit (file tag): "ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium".
- **DOI in the docs:** 10.5281/zenodo.7254221.
- verified in: GeoTIFF tags; `download_meghbhed_data.sh` line 62; `docs/DATA.md` lines 25 and 72

### WorldPop

- **Product:** Bangladesh 2020 population counts, unconstrained, UN-adjusted, 100 m.
- **Provider:** WorldPop, University of Southampton.
- **File:** `bgd_ppp_2020_UNadj.tif`
- **URL:** `https://data.worldpop.org/GIS/Population/Global_2000_2020/2020/BGD/bgd_ppp_2020_UNadj.tif`
- **Landing page:** `https://hub.worldpop.org/geodata/summary?id=25280`. DOI 10.5258/SOTON/WP00660.
- **Licence:** CC BY 4.0 (`docs/DATA.md`; no tag in the file).
- verified in: `download_meghbhed_data.sh` line 63; `docs/DATA.md` lines 26 and 62

### Copernicus DEM GLO-30

- **Provider:** ESA / Copernicus.
- **Files:** `Copernicus_DSM_COG_10_<tile>_DEM.tif` for tiles N21_00_E091_00, N21_00_E092_00, N22_00_E091_00, N22_00_E092_00 and N23_00_E091_00.
- **URL used:** `https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_<tile>_DEM/Copernicus_DSM_COG_10_<tile>_DEM.tif` (AWS open data).
- **Landing page in the docs:** OpenTopography, `https://portal.opentopography.org/datasetMetadata?otCollectionID=OT.032021.4326.1`.
- **Licence:** "Copernicus DEM licence (free, registration)" (`docs/DATA.md`).
- verified in: `download_meghbhed_data.sh` lines 64 and 78; `data/dem/`

### GLO-30 HAND (height above nearest drainage)

- **Provider:** ASF (HAND from Copernicus GLO-30), version path `v1/2021`.
- **Files:** `Copernicus_DSM_COG_10_<tile>_HAND.tif`, the same 5 tiles as the DEM.
- **URL:** `https://glo-30-hand.s3.amazonaws.com/v1/2021/Copernicus_DSM_COG_10_<tile>_HAND.tif`
- **Licence:** not found. Not listed in `docs/DATA.md`.
- verified in: `download_meghbhed_data.sh` line 79; `data/hand/`

### Administrative boundaries (actually used)

- **Dataset:** geoBoundaries gbOpen, Bangladesh ADM2 (districts) and ADM3 (upazilas), pinned to commit `9469f09`.
- **Files:** `geoBoundaries-BGD-ADM2.geojson` and `geoBoundaries-BGD-ADM3.geojson`.
- **URL:** `https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/BGD/ADM2/…` (and `/ADM3/…`).
- **Licence:** not found in the repo or the files.
- verified in: `download_meghbhed_data.sh` lines 65 and 81–82; `pipeline/01_grid.py` lines 27–28
- The docs and app name **HDX COD-AB** (BBS via OCHA, CC BY-IGO, `https://data.humdata.org/dataset/cod-ab-bgd`) instead; see the inconsistencies section.

### Listed in the docs but not read by the pipeline

- GPM IMERG Final half-hourly (`GPM_3IMERGHH`, DOI 10.5067/GPM/IMERG/3B-HH/07).
- NASA SRTM `SRTMGL1` V003 (fallback DEM).
- HDX COD-AB.
- verified in: `docs/DATA.md` lines 22, 28 and 29; no reference in `pipeline/*.py`

## B2. Papers and documents

### Papers

1. Tsyganskaya, V., Martinis, S., Marzahn, P. and Ludwig, R. (2018). "SAR-based detection of flooded vegetation – a review of characteristics and approaches." *International Journal of Remote Sensing* 39(8), 2255–2293. https://doi.org/10.1080/01431161.2017.1420938. verified in: `README.md` line 332; `docs/METHOD.md` line 98
2. Refice, A., Zingaro, M., D'Addabbo, A. and Chini, M. (2020). "Integrating C- and L-band SAR imagery for detailed flood monitoring of remote vegetated areas." *Water* 12(10), 2745. https://doi.org/10.3390/w12102745. verified in: `README.md` line 333; `docs/METHOD.md` line 98
3. Wagner, W., Bauer-Marschallinger, B., Roth, F. et al. (2026). "The fully-automatic Sentinel-1 Global Flood Monitoring service: scientific challenges and future directions." *Remote Sensing of Environment* 333, 115108. https://doi.org/10.1016/j.rse.2025.115108. verified in: `README.md` line 334
4. Kirschbaum et al. (2010) and Kirschbaum, Stanley and Zhou (2015): the GLC citations. No titles or URLs are given in the repo. verified in: `docs/DATA.md` line 74

### Product specifications and algorithm documents

- JPL D-102274, "NISAR NASA SDS Product Specification Level-2 Geocoded Polarimetric Covariance L2 GCOV". Cited in the file metadata, not in the docs. verified in: GCOV HDF5 attribute `reference_document`
- JPL D-102272, "NISAR NASA SDS Product Specification L2 Geocoded Unwrapped Interferogram". verified in: GUNW HDF5 attribute
- ASF NISAR documentation: https://nisar-docs.asf.alaska.edu/ (also `/gcov/`, `/products-overview/`, `/availability-overview/`). verified in: `README.md`, `docs/DATA.md`, `docs/METHOD.md` line 53, `web/src/App.vue` line 122
- No OPERA DSWx-S1 ATBD is cited: not found.

### Agency pages and announcements

- NASA Earthdata, "NISAR L-band data now publicly available": https://www.earthdata.nasa.gov/data/alerts-outages/nisar-l-band-data-now-publicly-available. verified in: `README.md`, `docs/DATA.md` line 36
- NASA JPL, NISAR press kit: https://www.jpl.nasa.gov/press-kits/nisar/. verified in: `README.md` line 60
- NASA landslides page: https://gpm.nasa.gov/applications/landslides. verified in: `docs/DATA.md` line 54
- EOSDIS data use guidance: https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance. PO.DAAC citation policy: https://podaac.jpl.nasa.gov/CitingPODAAC. verified in: `docs/DATA.md` lines 70–71
- NASA Space Apps 2026 challenge, "Dancing with the SARs": https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/. verified in: `README.md`, `web/src/App.vue` line 121

### UN and humanitarian reports

- Inter-Cluster Coordination Group (UN Bangladesh), *Bangladesh: Flash Flood and Landslides, Situation Report #2*, 23 July 2026: https://bangladesh.un.org/en/319868-bangladesh-situation-report-2-flash-flood-and-landslides-23-july-2026. verified in: `README.md` line 335; `docs/METHOD.md` line 25; `docs/DATA.md` line 30; `web/src/views/Home.vue` line 75
- Named as searched, with no URL in the repo: UN Situation Report #1 (13 Jul 2026), NAWG flash updates (9 and 11 Jul 2026), BDRCS Sitrep 1 (7 Jul 2026). URLs: not found. verified in: `labels/README.md` line 93
- UNOSAT flood extent, 22 Jul 2026 (Charter activation 1042): searched for, not used, no URL. verified in: `labels/README.md` line 33

### News articles

Used for the test sites. `labels/sites.csv` has 84 test rows, with these distinct `source` values:

| Outlet | Date | URL | Test rows | Places |
| --- | --- | --- | --- | --- |
| The Business Standard (TBS) | 10 Jul 2026 | https://www.tbsnews.net/bangladesh/floods-leave-over-75-lakh-people-marooned-ctg-1484941 | 27 (flooded) | Bajalia, Keochia, Chadaha, Kaliaish, Dharmapur, Nalua (Satkania); Baharchhara, Saral, Gunagari (Banshkhali) |
| bdnews24 | 10 Jul 2026 | https://bdnews24.com/bangladesh/eda23461240f | 15 (flooded) | Napora (Banshkhali); Amirabad, Adhunagar, Padua, Lohagara (Lohagara) |
| (none) | — | "no place-level flood report found (searched UN SitRep #1, NAWG 9 and 11 Jul, BDRCS 7 Jul, TBS, BSS, bdnews24, Prothom Alo, Daily Observer, Financial Express)" | 42 (dry) | 14 places in Mirsharai, Sitakunda, Raozan and Sandwip |

verified in: `labels/sites.csv`; `labels/build/places.py` lines 1–4; `labels/README.md` lines 71–84

Other news cited, not as a `sites.csv` source:

- BSS, 12 Jul 2026: https://www.bssnews.net/others/404930. Cited as confirming the TBS report. verified in: `labels/README.md` line 75; `labels/build/places.py` line 3
- Prothom Alo, 12/13 Jul 2026: https://en.prothomalo.com/amp/story/bangladesh/7jbpk0qmji. Listed for Hasan Balipara (Satkania), but that place was not geocoded inside Satkania, so it is not in `sites.csv`. verified in: `labels/build/places.py` lines 4 and 16; `labels/build/places_geocoded.json`
- The Daily Star, 12 Jul 2026, FFWC forecast for Feni: https://www.thedailystar.net/news/environment/weather/news/10-districts-risk-fresh-flood-next-24-72-hours-ffwc-4221406. verified in: `docs/METHOD.md` line 28
- Named as searched, with no URL: Daily Observer (11 and 12 Jul), The Financial Express (19 Jul), The Daily Star via Asia News Network (15 Jul). verified in: `labels/README.md` line 94

## B3. Software libraries

### Python pipeline

Python 3.11.18, venv `~/.venvs/meghbhed`. These are the packages imported by `pipeline/*.py` and `labels/build/*.py`, with installed versions. verified in: `pip freeze` of that venv; `environment.yml`; the import lines.

- numpy 2.4.6
- scipy 1.17.1
- pandas 3.1.1
- h5py 3.16.0 (NISAR HDF5)
- rasterio 1.4.4
- geopandas 1.2.0
- shapely 2.2.0
- pyproj 3.7.2
- xarray 2026.9.0 and netCDF4 1.7.5.1.post1 (IMERG)
- scikit-learn 1.9.1 (Random Forest, logistic regression, isotonic regression, GroupKFold, metrics)
- lightgbm 4.7.0
- shap 0.51.0
- matplotlib 3.11.2 (plots)
- Also in `environment.yml` but not imported by the pipeline: joblib (installed 1.6.0, used internally by scikit-learn) and jupyterlab (not installed in the venv).
- Standard library only for Nominatim calls: `urllib`.

### Web app

`web/package.json` versions, as locked in `package-lock.json`:

- vue 3.5.43, vue-router 5.4.0
- maplibre-gl 6.13.0 (maps)
- lucide-vue-next 1.0.0 (icons)
- lenis 1.3.26 (smooth scrolling)
- @grpc/grpc-js 1.14.7 and @grpc/proto-loader 0.8.1 (server: NVIDIA speech-to-text)
- Fonts: @fontsource-variable/geist 5.3.0, @fontsource-variable/geist-mono 5.3.0, @fontsource/noto-sans-bengali 5.3.0, @fontsource/noto-serif-bengali 5.3.0
- Build: vite 8.3.3, @vitejs/plugin-vue 6.0.9, tailwindcss 4.3.3, @tailwindcss/postcss 4.3.3, postcss 8.5.29, autoprefixer 10.6.1
- Hosting: Vercel serverless functions (`web/api/`)

### Testing

- @playwright/test 1.64.0 (browser tests; runs in the installed Chrome)
- @axe-core/playwright 4.13.0 (accessibility checks)
- Node's built-in test runner (`node --test`) for unit tests
- verified in: `web/package.json`; `web/package-lock.json`; `web/playwright.config.js`

## B4. Assets

- **Basemap tiles:** Esri ArcGIS Online. verified in: `web/src/components/SwipeMap.vue` lines 128–168
  - Light and dark grey canvas, base and reference layers: `server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base`, `World_Dark_Gray_Base`, `World_Light_Gray_Reference` and `World_Dark_Gray_Reference`. Attribution: "Basemap © Esri, HERE, Garmin, © OpenStreetMap contributors".
  - Satellite: `World_Imagery`, plus labels from `Reference/World_Boundaries_and_Places`. Attribution: "Imagery © Esri, Maxar, Earthstar Geographics".
  - Figure caption on the home page: "Basemap © Esri, OpenStreetMap" (`web/src/messages.js` line 63, Bangla at line 397).
- **Map library:** MapLibre GL JS 6.13.0. Its attribution control is compact and starts collapsed (`SwipeMap.vue` lines 361 and 374).
- **Fonts:** Geist and Geist Mono (Vercel), Noto Sans Bengali and Noto Serif Bengali (Google), all self-hosted through Fontsource. verified in: `web/src/main.js` lines 3–6; `web/src/style.css` lines 32–35
- **Icons:** Lucide (lucide-vue-next). verified in: `web/src/App.vue` script imports
- **Images:**
  - Team photos `web/public/{dip,apurbo,eva,partho,sakin,suchi}.jpg`.
  - Banner `docs/assets/banner.jpg`, also used as the social preview image via raw.githubusercontent.com (`web/index.html` line 13).
  - Logo/favicon `web/public/favicon.svg`.
  - Source or credit for these: not found.
- **Footer credits:** links to the method, data and code on GitHub, the Space Apps challenge page, the NISAR docs (ASF) and the MIT licence, plus a disclaimer. No separate data or asset credits. verified in: `web/src/App.vue` lines 112–135
- **Home page data credits:** NISAR L2 GCOV (NASA/ISRO, ASF DAAC), OPERA DSWx-S1 (NASA JPL, PO.DAAC), ESA WorldCover 2021, WorldPop (University of Southampton), GPM IMERG V07 (NASA GES DISC), LHASA (NASA GSFC), Copernicus DEM GLO-30 and "Admin boundaries (COD-AB), BBS via OCHA HDX". verified in: `web/src/views/Home.vue` lines 309–318
- **README acknowledgements:** NASA, ISRO, NASA JPL, ASF DAAC, PO.DAAC, NASA GSFC, GES DISC, ESA, WorldPop, OCHA/HDX and the NASA Space Apps Bangladesh organisers. verified in: `README.md` line 328
- **Third-party code in the repo:** NVIDIA Riva protocol files `web/server/riva/riva/proto/riva_asr.proto`, `riva_audio.proto` and `riva_common.proto`. Headers: "Copyright (c) 2022 NVIDIA CORPORATION & AFFILIATES, SPDX MIT". `riva_asr.proto` also carries "Copyright 2019 Google LLC, Apache License 2.0". verified in: the file headers
- **Project licence:** MIT. verified in: `LICENSE`; `README.md` line 357

## B5. Methods borrowed from others (`docs/METHOD.md`)

- **HH rise without HV rise means water under trees (double bounce):** the under-tree rule, ΔHH ≥ +3 dB and ΔHV ≤ +1 dB. Source: Tsyganskaya et al. (2018); Refice et al. (2020). verified in: `docs/METHOD.md` line 98. The thresholds themselves are labelled "starting values", with no source.
- **Speckle filter, "a small-window filter such as refined Lee":** no source is cited. The code uses a classic Lee filter (`pipeline/02_nisar.py` line 23). verified in: `docs/METHOD.md` line 49
- **GCOV posting (10 m for frequency A, 40 MHz) and mask values:** source is the ASF GCOV guide, https://nisar-docs.asf.alaska.edu/gcov/. verified in: `docs/METHOD.md` lines 50–53
- **DSWx-S1 class codes** (1 open water, 3 inundated vegetation, 250–255 masked or fill): no citation in METHOD.md; stated in `pipeline/config.py` lines 101–105.
- **The 5–18 Jul rain window:** taken from UN Sit Rep #2. verified in: `docs/METHOD.md` line 169
- **Thresholds chosen from the team's own data, not borrowed:**
  - −14 dB and −3 dB: from `outputs/openwater_rule_sweep.csv`.
  - HAND limits, risk-map classes and landslide index weights: described as "a judgement".
  - Coherence threshold: from the train sites.
  - verified in: `docs/METHOD.md` lines 74, 240–247 and 279–280, and section 12
- **SHAP TreeExplainer and the precision–recall break-even point:** named as methods, with no paper cited (Lundberg and Lee are not cited). verified in: `docs/METHOD.md` sections 10.1 and 11

---

# Inconsistencies found

1. **Boundaries.**
   - The pipeline reads **geoBoundaries gbOpen** (`pipeline/01_grid.py` lines 27–28; `download_meghbhed_data.sh` line 65).
   - `docs/DATA.md` line 29, `docs/METHOD.md` (sections 2 and 5), the README data table and acknowledgements, and the app's home page all name **HDX COD-AB (BBS/OCHA, CC BY-IGO)**, which is never downloaded or read.
2. **Landslide catalogue dates and source.**
   - `docs/DATA.md` line 24 says "2007 – Mar 2016" and links data.gov.
   - `pipeline/README.md` line 197 says "1988–2017" and gives a data.nasa.gov legacy CSV URL.
   - `docs/METHOD.md` line 270 says "(2007–2017)".
   - The actual file runs from 1988-11-07 to 2017-09-28; the points in the grid run from 2007-06-11 to 2017-07-02.
3. **DSWx-S1 tiles.** `docs/DATA.md` line 44 and `docs/METHOD.md` line 38 list only T46QCK and T46QCL. The pipeline uses four tiles (CK, CL, DK, DL).
4. **NISAR dates.** `docs/DATA.md` line 18 gives the coverage as "25 Jun – 19 Jul 2026". The files used run from 18 Jun to 17 Aug (A_before2 and A_after), and the METHOD.md scene table lists only 4 of the 8 GCOV granules.
5. **Feni pair C.** It is downloaded and processed (`work/flood_C.tif`, `stats.json` `pairs.C`), but Feni is excluded from the reported study area. Pair C feeds only the unverified under-tree label (5).
6. **GUNW.** `docs/DATA.md` line 19 and `README.md` line 184 say "coherence on slopes", 80 m, "to be confirmed". It is actually used for the under-tree coherence test (step 13), from the 20 m layer. `pipeline/README.md` line 199 also says "no pipeline step reads it", although step 13 does.
7. **Download script coverage.** `download_meghbhed_data.sh` does not fetch:
   - the 18 Jun and 17 Aug GCOV granules;
   - the GUNW files;
   - the June DSWx files;
   - the landslide catalogue;
   - the susceptibility map;
   - LHASA (manual by design).
   So the data cannot be fully re-downloaded with it.
8. **HAND.** GLO-30 HAND is a core input (the flood rule, risk maps and labels) but is missing from the `docs/DATA.md` table, the README data table and the app's dataset list. No licence is recorded.
9. **Copernicus DEM link.** The docs and app link OpenTopography; the script downloads from the AWS `copernicus-dem-30m` bucket.
10. **LHASA.**
    - `docs/DATA.md` line 54 says NetCDF4; the files used are GeoTIFFs from `nrt/hazard/tif/`.
    - The files miss 10–12 Jul.
    - The app's home page lists LHASA as the "Landslide hazard" input, but it is not required (`USE_LHASA = False`) and is used only as a check.
11. **Listed but unused datasets.** `docs/DATA.md` lists IMERG Final half-hourly and SRTM; neither is used.
12. **WorldPop year.** `docs/DATA.md` line 26 still says "year to be fixed" (with a TODO); the file used is 2020 UN-adjusted.
13. **Assistant data source.** `docs/METHOD.md` line 183, `pipeline/README.md` line 96 and the README "Use of AI" table say the assistant gets `stats.json` as its only source. The facts block also includes `model_comparison.json` and `risk.json` (`web/server/facts.js` lines 18–21).
14. **Use-of-AI table incomplete.**
    - The README lists ChatGPT/Codex/Copilot as "planned".
    - It does not mention Claude Code, which wrote much of the current code in this session.
    - It does not mention the NVIDIA Whisper speech-to-text model inside the product, or the Kilo Code extension whose folder `.kilo/` is ignored in commit `522beb0`.
15. **Labels comment.** `pipeline/config.py` line 13 describes `labels/sites.csv` as "Eva's flooded / dry sites". The file was built by scripts: train sites from satellite data, test sites from geocoded news reports.
16. **BSS and Prothom Alo.** `labels/README.md` lists BSS as confirming the TBS places and Prothom Alo among sources searched, but neither URL appears in `sites.csv`. The Prothom Alo place (Hasan Balipara) was dropped at geocoding.
17. **Riva proto licence.** `web/README.md` line 85 says the files in `web/server/riva/` are MIT. `riva_asr.proto` also carries a Google LLC Apache-2.0 notice.
18. **Project title.** `CITATION.cff` and the README's BibTeX title is "Mapping flooding under tree cover with NISAR L-band radar". The method now says under-tree flooding could not be verified, and the headline map is open flood.
19. **Stale API comment.** The `web/api/ask.js` header (lines 1–3) still documents a `provider` choice in the POST body and a provider list on GET for the UI. The UI no longer uses either; the server still supports them.
