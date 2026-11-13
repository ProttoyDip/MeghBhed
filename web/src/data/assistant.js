// Rule-based stand-in for the planned grounded assistant. It answers only from
// the pipeline's figures in stats.json (loaded by results.js). No network calls.
import { upazilas, totals, agreeLabel, agreeLabelBn, formatInt, toBanglaDigits, modelComparison, risk } from './results'

const SOURCE = 'stats.json (provisional) · NISAR GCOV 12 & 19 Jul · DSWx-S1 16 Jul · WorldPop'

const isBangla = (s) => /[ঀ-৿]/.test(s)

function findUpazila(q) {
  const lower = q.toLowerCase()
  return upazilas.find((u) => lower.includes(u.name.toLowerCase()) || q.includes(u.bn) || q.includes(u.bn.slice(0, 3)))
}

const num = (n, bn) => (bn ? toBanglaDigits(formatInt(n)) : formatInt(n))
const km = (n, bn) => (bn ? `${toBanglaDigits(n.toFixed(1))} বর্গকিমি` : `${n.toFixed(1)} km²`)
const pc = (v, bn) => (bn ? `${toBanglaDigits((v * 100).toFixed(1))}%` : `${(v * 100).toFixed(1)}%`)
const MODEL_NAMES = { 'rule (HH drop and HH level)': ['Threshold rule', 'থ্রেশহোল্ড নিয়ম'], logistic_regression: ['Logistic regression', 'লজিস্টিক রিগ্রেশন'], random_forest: ['Random Forest', 'Random Forest'], lightgbm: ['LightGBM', 'LightGBM'] }

// Model comparison: numbers come only from model_comparison.json
function modelAnswer(bn) {
  const rows = modelComparison.tuned ?? []
  if (!rows.length) return null
  const rule = rows.find((m) => m.model === modelComparison.pipeline_uses) ?? rows[0]
  const best = [...rows].filter((m) => m !== rule).sort((a, b) => b.f1 - a.f1)[0]
  const name = (m) => MODEL_NAMES[m.model]?.[bn ? 1 : 0] ?? m.model
  return {
    text: bn
      ? `যাচাইয়ে সবচেয়ে ভালো নম্বর পেয়েছে ${name(best)} (F1 ${pc(best.f1, bn)}, নির্ভুলতা ${pc(best.accuracy, bn)}), কিন্তু মানচিত্রে থ্রেশহোল্ড নিয়মটিই ব্যবহৃত হয়েছে। কারণ, বন্যার খবর নেই এমন জায়গার কাছে নিয়মটি খোলা জমির মাত্র ${toBanglaDigits(rule.test_flagged_pct_near_dry_points.toFixed(1))}% চিহ্নিত করে, আর ${name(best)} করে ${toBanglaDigits(best.test_flagged_pct_near_dry_points.toFixed(1))}%।`
      : `${name(best)} scores highest in validation (F1 ${pc(best.f1)}, accuracy ${pc(best.accuracy)}), but the map uses the threshold rule. Near places with no flood report the rule flags only ${rule.test_flagged_pct_near_dry_points.toFixed(1)}% of open ground, against ${best.test_flagged_pct_near_dry_points.toFixed(1)}% for ${name(best)}.`,
    facts: rows.map((m) => [name(m), `F1 ${pc(m.f1, bn)} · ${bn ? 'নির্ভুলতা' : 'accuracy'} ${pc(m.accuracy, bn)}`]),
    link: { to: '/validation', label: bn ? 'কতটা ভালো কাজ করে' : 'How well it works' },
    source: 'model_comparison.json · 5 km spatial cross-validation',
  }
}

// Risk maps: numbers come only from risk.json
function riskAnswer(bn) {
  const f = risk.flood?.totals
  const s = risk.landslide?.totals
  if (!f && !s) return null
  const facts = []
  if (f) facts.push([bn ? 'বন্যার ঝুঁকি: বেশি বা খুব বেশি' : 'Flood risk: high or very high', `${km(f.high_or_very_high_km2, bn)} · ${num(f.high_or_very_high_people, bn)} ${bn ? 'জন' : 'people'}`])
  if (s) facts.push([bn ? 'ভূমিধসের ঝুঁকি: বেশি বা খুব বেশি' : 'Landslide risk: high or very high', `${km(s.high_or_very_high_km2, bn)} · ${num(s.people_within_100m_high_or_very_high, bn)} ${bn ? 'জন ১০০ মিটারের মধ্যে' : 'people within 100 m'}`])
  return {
    text: bn
      ? 'ঝুঁকির মানচিত্র দুটি সম্ভাবনা দেখায়, পূর্বাভাস নয়। বন্যার ঝুঁকির মডেলটি একটি মাত্র বন্যা (জুলাই ২০২৬) থেকে শেখানো এবং শুধু খোলা জমির জন্য, তাই এর মানুষের সংখ্যা সর্বনিম্ন সীমা। ভূমিধসের ঝুঁকি একটি ভারযুক্ত সূচক, প্রশিক্ষিত মডেল নয়।'
      : 'The two risk maps show likelihood, not a forecast. The flood-risk model was trained on a single flood (July 2026) and covers open land only, so its people figure is a lower bound. Landslide risk is a weighted index, not a trained model.',
    facts,
    link: { to: '/map', label: bn ? 'ম্যাপে ঝুঁকির স্তর চালু করুন' : 'Turn on the risk layers on the map' },
    source: 'risk.json · pipeline/11_flood_risk.py, 12_landslide_risk.py',
  }
}

function upazilaAnswer(u, bn) {
  const facts = bn
    ? [['১৬ জুলাইয়ের C-band মানচিত্রে নেই', km(u.hidden, bn)], ['দুই সেন্সরেই দেখা', km(u.both, bn)], ['১০০ মিটারের মধ্যে মানুষ (সর্বোচ্চ সীমা)', num(u.people, bn)], ['অবস্থা', agreeLabelBn[u.agree]]]
    : [['Missed by the 16 Jul C-band map', km(u.hidden)], ['Seen by both', km(u.both)], ['People within 100 m (upper bound)', num(u.people)], ['Status', agreeLabel[u.agree]]]
  const text = bn
    ? `${u.bn} (${u.districtBn}) উপজেলায় NISAR ১২ জুলাই ${km(u.hidden, bn)} বন্যা দেখেছে, যা ১৬ জুলাইয়ের C-band মানচিত্রে নেই। এর ১০০ মিটারের মধ্যে আনুমানিক ${num(u.people, bn)} জন মানুষ থাকেন (সর্বোচ্চ সীমা)।`
    : `In ${u.name} (${u.district}), NISAR saw ${km(u.hidden)} of flood on 12 July that the 16 July C-band map does not show. About ${num(u.people)} people live within 100 m of it (an upper bound).`
  return { text, facts, link: { to: `/map?u=${u.id}`, label: bn ? 'ম্যাপে দেখুন' : `Show ${u.name} on the map` } }
}

// Greetings, thanks and goodbyes get a friendly reply, not "I can't help with that"
const GREETING = /^(hi+|hello+|hey+|hiya|yo|good (morning|afternoon|evening)|salam|assalamu? ?alaikum|as-?salamu alaykum|namaskar|nomoskar|হাই|হ্যালো|হেলো|সালাম|আসসালামু ?আলাইকুম|নমস্কার|শুভ (সকাল|সন্ধ্যা|বিকাল))[\s!.,।?]*$/i
const THANKS = /^(thanks?( you)?|thank u|thx|ty|ok(ay)?( thanks?)?|great|nice|cool|ধন্যবাদ|থ্যাংক(স| ইউ)|আচ্ছা|ঠিক আছে)[\s!.,।?]*$/i
const BYE = /^(bye|goodbye|see you|good night|বিদায়|আল্লাহ হাফেজ|খোদা হাফেজ|শুভ রাত্রি)[\s!.,।?]*$/i

function smallTalk(q, bn) {
  const s = q.trim()
  if (GREETING.test(s)) {
    return bn
      ? 'হ্যালো! আমি মেঘভেদ। চট্টগ্রামের জুলাই ২০২৬-এর বন্যা নিয়ে প্রশ্ন করতে পারেন: কোন উপজেলায় কত এলাকা আর কত মানুষ, মোট হিসাব, মডেলগুলো কতটা ভালো কাজ করে, অথবা বন্যা ও ভূমিধসের ঝুঁকির মানচিত্র।'
      : "Hello! I'm MeghBhed. Ask me about the July 2026 floods in Chattogram: flood area and people in any upazila, the totals, how well the models work, or the flood and landslide risk maps."
  }
  if (THANKS.test(s)) return bn ? 'আপনাকেও ধন্যবাদ! আর কিছু জানতে চাইলে জিজ্ঞেস করুন।' : "You're welcome! Ask me anything else about the floods."
  if (BYE.test(s)) return bn ? 'বিদায়! আবার আসবেন।' : 'Goodbye, and stay safe.'
  return null
}

export function answer(q) {
  const bn = isBangla(q)
  const lower = q.toLowerCase()
  const hello = smallTalk(q, bn)
  if (hello) return { text: hello, facts: [], source: null }
  const u = findUpazila(q)
  if (u) return { ...upazilaAnswer(u, bn), source: SOURCE }

  if (/highest|most|largest|worst|top|সবচেয়ে|বেশি/.test(lower)) {
    const ranked = [...upazilas].sort((a, b) => b.people - a.people).slice(0, 3)
    const top = ranked[0]
    return {
      text: bn
        ? `${top.bn} উপজেলায় সবচেয়ে বেশি মানুষ এমন বন্যার ১০০ মিটারের মধ্যে থাকেন, যা ১৬ জুলাইয়ের C-band মানচিত্রে নেই। প্রথম তিনটি:`
        : `${top.name} has the most people living within 100 m of flood the 16 July C-band map missed. The top three:`,
      facts: ranked.map((r, i) => [`${bn ? toBanglaDigits(i + 1) : i + 1}. ${bn ? r.bn : r.name}`, `${num(r.people, bn)} ${bn ? 'জন' : 'people'}`]),
      source: SOURCE,
    }
  }

  if (/total|all|overall|how many|মোট|সব|কত/.test(lower)) {
    const count = upazilas.filter((x) => x.hidden > 0).length
    return {
      text: bn
        ? `${num(count, bn)}টি উপজেলা মিলিয়ে আনুমানিক ${num(totals.people, bn)} জন মানুষ এমন বন্যার ১০০ মিটারের মধ্যে থাকেন, যা NISAR ১২ জুলাই দেখেছে কিন্তু ১৬ জুলাইয়ের C-band মানচিত্রে নেই। এটি সর্বোচ্চ সীমা; শুধু ৫ হেক্টর বা বড় অংশ ধরলে ${num(totals.people_conservative, bn)} জন।`
        : `Across ${count} upazilas, about ${num(totals.people)} people live within 100 m of flood that NISAR saw on 12 July and the 16 July C-band map missed. That is an upper bound; counting only patches of 5 ha or more gives ${num(totals.people_conservative)}.`,
      facts: bn
        ? [['১৬ জুলাইয়ের C-band মানচিত্রে নেই', km(totals.hidden, bn)], ['দুই সেন্সরেই দেখা', km(totals.both, bn)], ['পাহাড় ঝুঁকি স্থান', num(totals.hill, bn)]]
        : [['Missed by the 16 Jul C-band map', km(totals.hidden)], ['Seen by both', km(totals.both)], ['Hill Risk sites', num(totals.hill)]],
      source: SOURCE,
    }
  }

  if (/model|accura|precision|recall|\bf1\b|classifier|how well|validat|random forest|lightgbm|মডেল|নির্ভুল|কতটা ভালো/.test(lower)) {
    const a = modelAnswer(bn)
    if (a) return a
  }

  if (!/hill risk|পাহাড় ঝুঁকি/.test(lower) && /risk|susceptib|likel|ঝুঁকি|সম্ভাবনা/.test(lower)) {
    const a = riskAnswer(bn)
    if (a) return a
  }

  if (/landslide|hill|slope|ভূমিধস|পাহাড়/.test(lower)) {
    const ranked = [...upazilas].filter((x) => x.hill > 0).sort((a, b) => b.hill - a.hill)
    return {
      text: bn
        ? `${num(totals.hill, bn)}টি ঢাল সরেজমিনে দেখা দরকার। এগুলো সম্ভাব্য ঝুঁকি, ভূমিধস হয়েছে এমন দাবি নয়।`
        : `${totals.hill} slopes are flagged to check on the ground. These are possible sites, not confirmed landslides.`,
      facts: ranked.slice(0, 4).map((r) => [bn ? r.bn : r.name, `${num(r.hill, bn)} ${bn ? 'স্থান' : r.hill === 1 ? 'site' : 'sites'}`]),
      source: 'Slope (Copernicus DEM) · IMERG July rainfall · NISAR HV drop on slopes',
    }
  }

  if (/why|how|c-band|l-band|nisar|double|under tree|কেন|কিভাবে|কীভাবে|গাছ/.test(lower)) {
    return {
      text: bn
        ? 'খোলা বন্যার পানি রাডারে অন্ধকার দেখায়। NISAR ১২ জুলাই বন্যার চূড়ার কাছাকাছি সময়ে ছবি নিয়েছে; C-band মানচিত্রটি চার দিন পরের, ১৬ জুলাইয়ের, তখন অনেক পানি নেমে গেছে। গাছের নিচের বন্যা আমরা যাচাই করতে পারিনি, তাই সেটি কোনো মোট সংখ্যায় নেই।'
        : 'Open floodwater looks dark to radar. NISAR passed on 12 July, close to the flood peak; the C-band map is from 16 July, four days later, when much of the water had gone. Flood under trees could not be verified, so it is not in any total.',
      facts: bn ? [['HH কমেছে', '≥ ৩ dB'], ['১২ জুলাই HH', '≤ −১৪ dB']] : [['HH dropped by', '≥ 3 dB'], ['HH on 12 Jul', '≤ −14 dB']],
      source: 'docs/METHOD.md',
    }
  }

  return {
    text: bn
      ? 'আমি শুধু MeghBhed-এর হিসাব করা তথ্য থেকে উত্তর দিই। কোনো উপজেলার নাম লিখুন, অথবা মোট সংখ্যা বা পাহাড় ঝুঁকি সম্পর্কে জিজ্ঞেস করুন।'
      : 'I only answer from MeghBhed’s computed figures, so I can’t help with that. Try an upazila name, the totals, the most affected area, or Hill Risk.',
    facts: [],
    source: null,
    miss: true,
  }
}
