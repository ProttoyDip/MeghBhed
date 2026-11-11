// Rule-based stand-in for the planned grounded assistant. It answers only from
// the pipeline's figures in stats.json (loaded by results.js). No network calls.
import { upazilas, totals, agreeLabel, agreeLabelBn, formatInt, toBanglaDigits } from './results'

const SOURCE = 'stats.json (provisional) · NISAR GCOV 12 & 19 Jul · DSWx-S1 16 Jul · WorldPop'

const isBangla = (s) => /[ঀ-৿]/.test(s)

function findUpazila(q) {
  const lower = q.toLowerCase()
  return upazilas.find((u) => lower.includes(u.name.toLowerCase()) || q.includes(u.bn) || q.includes(u.bn.slice(0, 3)))
}

const num = (n, bn) => (bn ? toBanglaDigits(formatInt(n)) : formatInt(n))
const km = (n, bn) => (bn ? `${toBanglaDigits(n.toFixed(1))} বর্গকিমি` : `${n.toFixed(1)} km²`)

function upazilaAnswer(u, bn) {
  const facts = bn
    ? [['১৬ জুলাইয়ের C-band মানচিত্রে নেই', km(u.hidden, bn)], ['দুই সেন্সরেই দেখা', km(u.both, bn)], ['১০০ মিটারের মধ্যে মানুষ (সর্বোচ্চ সীমা)', num(u.people, bn)], ['অবস্থা', agreeLabelBn[u.agree]]]
    : [['Missed by the 16 Jul C-band map', km(u.hidden)], ['Seen by both', km(u.both)], ['People within 100 m (upper bound)', num(u.people)], ['Status', agreeLabel[u.agree]]]
  const text = bn
    ? `${u.bn} (${u.districtBn}) উপজেলায় NISAR ১২ জুলাই ${km(u.hidden, bn)} বন্যা দেখেছে, যা ১৬ জুলাইয়ের C-band মানচিত্রে নেই। এর ১০০ মিটারের মধ্যে আনুমানিক ${num(u.people, bn)} জন মানুষ থাকেন (সর্বোচ্চ সীমা)।`
    : `In ${u.name} (${u.district}), NISAR saw ${km(u.hidden)} of flood on 12 July that the 16 July C-band map does not show. About ${num(u.people)} people live within 100 m of it (an upper bound).`
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
