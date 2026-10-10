// Rule-based stand-in for the planned grounded assistant. It answers only from
// the concept figures in concept.js, the same way the real one will answer only
// from stats.json. No network calls.
import { upazilas, totals, agreeLabel, formatInt, toBanglaDigits } from './concept'

const SOURCE = 'stats.json (concept) · NISAR GCOV 12 & 19 Jul · DSWx-S1 16 Jul · WorldPop'

const isBangla = (s) => /[ঀ-৿]/.test(s)

function findUpazila(q) {
  const lower = q.toLowerCase()
  return upazilas.find((u) => lower.includes(u.name.toLowerCase()) || q.includes(u.bn) || q.includes(u.bn.slice(0, 3)))
}

const num = (n, bn) => (bn ? toBanglaDigits(formatInt(n)) : formatInt(n))
const km = (n, bn) => (bn ? `${toBanglaDigits(n.toFixed(1))} বর্গকিমি` : `${n.toFixed(1)} km²`)

function upazilaAnswer(u, bn) {
  const facts = bn
    ? [['গাছের নিচে বন্যা', km(u.hidden, bn)], ['খোলা পানি', km(u.both, bn)], ['মানুষ', num(u.people, bn)], ['অবস্থা', u.agree === 'both-dates' ? 'সম্ভবত C-band মিস করেছে' : 'সম্ভবত প্লাবিত']]
    : [['Under trees', km(u.hidden)], ['Open water', km(u.both)], ['People', num(u.people)], ['Status', agreeLabel[u.agree]]]
  const text = bn
    ? `${u.bn} (${u.district === 'Feni' ? 'ফেনী' : 'চট্টগ্রাম'}) উপজেলায় আনুমানিক ${num(u.people, bn)} জন মানুষ এমন জায়গায় থাকেন যেখানে NISAR গাছের নিচে পানি পেয়েছে, কিন্তু C-band ম্যাপে সেটা শুকনো দেখায়।`
    : `In ${u.name} (${u.district}), about ${num(u.people)} people live where NISAR found water under the trees but the C-band map shows dry land.`
  return { text, facts, link: { to: `/map?u=${u.id}`, label: bn ? 'ম্যাপে দেখুন' : `Show ${u.name} on the map` } }
}

export function answer(q) {
  const bn = isBangla(q)
  const lower = q.toLowerCase()
  const u = findUpazila(q)
  if (u) return { ...upazilaAnswer(u, bn), source: SOURCE }

  if (/highest|most|largest|worst|top|সবচেয়ে|বেশি/.test(lower)) {
    const ranked = [...upazilas].sort((a, b) => b.people - a.people).slice(0, 3)
    const top = ranked[0]
    return {
      text: bn
        ? `${top.bn} উপজেলায় সবচেয়ে বেশি মানুষ C-band ম্যাপের বাইরে রয়ে গেছেন। প্রথম তিনটি:`
        : `${top.name} has the most people outside the C-band flood map. The top three:`,
      facts: ranked.map((r, i) => [`${bn ? toBanglaDigits(i + 1) : i + 1}. ${bn ? r.bn : r.name}`, `${num(r.people, bn)} ${bn ? 'জন' : 'people'}`]),
      source: SOURCE,
    }
  }

  if (/total|all|overall|how many|মোট|সব|কত/.test(lower)) {
    return {
      text: bn
        ? `৮টি উপজেলা মিলিয়ে আনুমানিক ${num(totals.people, bn)} জন মানুষ গাছের নিচের বন্যায় আছেন, যা C-band ম্যাপে দেখা যায় না।`
        : `Across 8 upazilas, about ${num(totals.people)} people are in flood under tree cover that the C-band map doesn't show.`,
      facts: bn
        ? [['গাছের নিচে বন্যা', km(totals.hidden, bn)], ['খোলা পানি', km(totals.both, bn)], ['পাহাড় ঝুঁকি স্থান', num(totals.hill, bn)]]
        : [['Under trees', km(totals.hidden)], ['Open water', km(totals.both)], ['Hill Risk sites', num(totals.hill)]],
      source: SOURCE,
    }
  }

  if (/landslide|hill|slope|ভূমিধস|পাহাড়/.test(lower)) {
    const ranked = [...upazilas].filter((x) => x.hill > 0).sort((a, b) => b.hill - a.hill)
    return {
      text: bn
        ? `${num(totals.hill, bn)}টি ঢাল সরেজমিনে দেখা দরকার। এগুলো সম্ভাব্য ঝুঁকি, ভূমিধস হয়েছে এমন দাবি নয়।`
        : `${totals.hill} slopes are flagged to check on the ground. These are possible sites, not confirmed landslides.`,
      facts: ranked.slice(0, 4).map((r) => [bn ? r.bn : r.name, `${num(r.hill, bn)} ${bn ? 'স্থান' : r.hill === 1 ? 'site' : 'sites'}`]),
      source: 'Slope (Copernicus DEM) · IMERG July rainfall · LHASA nowcast · NISAR slope change',
    }
  }

  if (/why|how|c-band|l-band|nisar|double|কেন|কিভাবে|কীভাবে/.test(lower)) {
    return {
      text: bn
        ? 'C-band (৫.৬ সেমি) তরঙ্গ পাতায় ছড়িয়ে যায়, তাই গাছের নিচের পানি দেখা যায় না। NISAR-এর L-band (২৪ সেমি) পাতা ভেদ করে পানিতে পড়ে, গাছের কাণ্ডে প্রতিফলিত হয়ে ফিরে আসে। একে বলে ডাবল বাউন্স।'
        : 'C-band waves (5.6 cm) scatter off leaves, so water under trees stays hidden. NISAR’s L-band (24 cm) passes the canopy, reflects off the water and bounces off trunks back to the satellite. That double bounce shows up as a strong HH increase.',
      facts: bn ? [['ΔHH সীমা', '≥ +৩ dB'], ['ΔHV সীমা', '≤ +১ dB']] : [['ΔHH threshold', '≥ +3 dB (starting value)'], ['ΔHV threshold', '≤ +1 dB (starting value)']],
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
