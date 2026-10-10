import { ref, watch } from 'vue'
import { messages } from './messages'

const KEY = 'meghbhed-lang'

function stored() {
  try {
    const v = localStorage.getItem(KEY)
    return v === 'en' || v === 'bn' ? v : null
  } catch {
    return null
  }
}

export const lang = ref(stored() ?? (navigator.language?.startsWith('bn') ? 'bn' : 'en'))

function apply(l) {
  document.documentElement.lang = l
}
apply(lang.value)

watch(lang, (l) => {
  apply(l)
  try {
    localStorage.setItem(KEY, l)
  } catch {
    // storage blocked: the choice still applies for this visit
  }
})

export const toggleLang = () => {
  lang.value = lang.value === 'en' ? 'bn' : 'en'
}

const lookup = (dict, key) => key.split('.').reduce((o, k) => (o == null ? undefined : o[k]), dict)

// t('home.title') → string in the current language, falling back to English.
// t('stats.count', { n: 8 }) replaces {n}. Arrays/objects are returned as-is.
export function t(key, vars) {
  let v = lookup(messages[lang.value], key) ?? lookup(messages.en, key) ?? key
  if (vars && typeof v === 'string') v = v.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? `{${k}}`)
  return v
}

const locale = () => (lang.value === 'bn' ? 'bn-BD' : 'en-US')

// Numbers in Bengali digits when the page is in Bangla
export function n(value, options) {
  return new Intl.NumberFormat(locale(), options).format(value)
}

export const fixed = (value, digits = 1) => n(value, { minimumFractionDigits: digits, maximumFractionDigits: digits })

// '2026-07-12' → 12 Jul 2026 / ১২ জুল, ২০২৬ (day-month order in both languages)
export function date(iso) {
  return new Intl.DateTimeFormat(lang.value === 'bn' ? 'bn-BD' : 'en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${iso}T00:00:00Z`))
}

// Pick the localized field of a data record: loc(u, 'name') → u.bn when Bangla
export function loc(record, field = 'name') {
  if (lang.value === 'bn') return record[`${field}Bn`] ?? (field === 'name' ? record.bn : undefined) ?? record[field]
  return record[field]
}
