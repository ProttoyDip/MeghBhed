<template>
  <div class="w-full">
    <!-- Header band -->
    <section class="relative overflow-hidden">
      <GradientBackdrop fade="side" /><!-- SOFFIT GRADIENT (trial) -->
      <div class="relative mx-auto max-w-[88rem] px-4 pt-10 sm:px-6 lg:pt-14">
        <header v-reveal class="flex flex-col gap-6 border-b-2 border-ink pb-8 lg:flex-row lg:items-end lg:justify-between">
          <div class="max-w-2xl">
            <p class="label">{{ t('stats.label') }}</p>
            <h1 class="mt-3 font-display text-4xl font-bold tracking-tight text-ink sm:text-5xl">{{ t('stats.title') }}</h1>
            <p class="mt-3 text-ink-2 pretty">{{ t('stats.lead') }}</p>
          </div>
          <div class="flex gap-2">
            <button type="button" class="btn btn-line group" @click="exportCsv"><FileSpreadsheet class="h-4 w-4 transition-transform group-hover:-translate-y-0.5" :stroke-width="1.75" /> CSV</button>
            <button type="button" class="btn btn-line group" @click="exportKml"><MapPinned class="h-4 w-4 transition-transform group-hover:-translate-y-0.5" :stroke-width="1.75" /> KML</button>
          </div>
        </header>
      </div>
    </section>

    <div class="mx-auto w-full max-w-[88rem] px-4 pb-10 sm:px-6 lg:pb-14">
      <p v-reveal="80" class="mt-5 flex items-start gap-2.5 border-l-2 border-hill bg-hill-soft/60 px-3 py-2.5 text-[13px] leading-relaxed text-ink">
        <Info class="mt-0.5 h-4 w-4 shrink-0 text-hill" />
        <span><strong class="font-semibold">{{ t('stats.noticeBold') }}</strong> {{ t('stats.notice') }}</span>
      </p>

      <!-- Headline numbers -->
      <dl v-reveal.stagger="100" class="mt-10 grid grid-cols-2 border-y border-ink/80 lg:grid-cols-4">
        <div v-for="(k, i) in kpis" :key="i" class="py-6 pr-4" :class="[i % 2 === 1 ? 'border-l border-rule pl-4 sm:pl-6' : '', i === 2 ? 'lg:border-l lg:border-rule lg:pl-6' : '', i > 1 ? 'border-t border-rule lg:border-t-0' : '']">
          <dt class="label !text-[10px] sm:!text-[11px]">{{ t('stats.kpi')[i].label }}</dt>
          <dd class="mt-2 font-display text-3xl font-bold tracking-tight text-ink sm:text-[2.6rem]">
            <CountUp :value="k.value" :decimals="k.decimals" /><span v-if="k.unit" class="ml-1 font-sans text-base font-medium text-ink-3">{{ k.unit === 'km2' ? t('common.km2') : k.unit }}</span>
          </dd>
          <dd class="mt-1 text-xs text-ink-2">{{ t('stats.kpi')[i].note }}</dd>
        </div>
      </dl>

      <!-- Chart -->
      <section class="mt-14" aria-labelledby="chart-title">
        <div v-reveal class="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 id="chart-title" class="font-display text-2xl font-bold tracking-tight text-ink">{{ t('stats.chartTitle') }}</h2>
            <p class="mt-1 text-sm text-ink-2">{{ t('stats.chartSub') }}</p>
          </div>
          <ul class="flex flex-wrap gap-x-5 gap-y-2 text-sm text-ink-2" :aria-label="t('stats.legend')">
            <li class="inline-flex items-center gap-2"><span class="h-3 w-4 rounded-[2px] bg-water"></span>{{ t('common.openWater') }} · {{ t('common.bothSensors') }}</li>
            <li class="inline-flex items-center gap-2"><span class="hatch-missed h-3 w-4 rounded-[2px] border border-missed"></span>{{ t('common.underTrees') }} · {{ t('common.nisarOnly') }}</li>
          </ul>
        </div>

        <div ref="chartRef" class="relative mt-6" @mouseleave="hover = null">
          <div class="space-y-2.5">
            <div
              v-for="(u, i) in chartRows"
              :key="u.id"
              class="grid grid-cols-[6.5rem_1fr] items-center gap-3 sm:grid-cols-[9rem_1fr]"
              @mousemove="onHover($event, u)"
            >
              <span class="truncate text-right text-sm text-ink">{{ loc(u) }}</span>
              <!-- Bars grow from the axis the first time the chart scrolls into view -->
              <div
                class="flex h-7 origin-left items-center gap-[2px] transition-transform duration-[900ms] ease-[cubic-bezier(0.16,1,0.3,1)]"
                :class="grown ? 'scale-x-100' : 'scale-x-0'"
                :style="{ transitionDelay: `${i * 60}ms` }"
              >
                <span class="h-full rounded-l-[4px] bg-water transition-opacity" :class="hover && hover.u.id !== u.id ? 'opacity-40' : ''" :style="{ width: `${(u.both / maxTotal) * 88}%` }"></span>
                <span class="hatch-missed h-full rounded-r-[4px] border border-missed transition-opacity" :class="hover && hover.u.id !== u.id ? 'opacity-40' : ''" :style="{ width: `${(u.hidden / maxTotal) * 88}%` }"></span>
                <span class="num ml-2 font-mono text-xs text-ink-2">{{ fixed(u.both + u.hidden) }}</span>
              </div>
            </div>
          </div>
          <!-- axis -->
          <div class="mt-3 grid grid-cols-[6.5rem_1fr] gap-3 sm:grid-cols-[9rem_1fr]">
            <span></span>
            <div class="relative h-4 border-t border-rule">
              <span v-for="tick in ticks" :key="tick" class="num absolute top-1 -translate-x-1/2 font-mono text-[10px] text-ink-3" :style="{ left: `${(tick / maxTotal) * 88}%` }">{{ n(tick) }}</span>
            </div>
          </div>

          <!-- Tooltip -->
          <transition name="tip">
            <div v-if="hover" class="pointer-events-none absolute z-10 w-60 rounded-lg border border-rule bg-card p-3 text-sm shadow-[0_8px_24px_rgb(15_28_46/0.14)] transition-[left,top] duration-150 ease-out" :style="{ left: `${hover.x}px`, top: `${hover.y}px` }">
              <p class="font-semibold text-ink">{{ loc(hover.u) }} <span class="font-normal text-ink-3">· {{ loc(hover.u, 'district') }}</span></p>
              <dl class="mt-2 space-y-1 text-[13px]">
                <div class="flex justify-between gap-3"><dt class="flex items-center gap-1.5 text-ink-2"><span class="h-2.5 w-2.5 rounded-[2px] bg-water"></span>{{ t('common.openWater') }}</dt><dd class="num font-mono text-ink">{{ fixed(hover.u.both) }} {{ t('common.km2') }}</dd></div>
                <div class="flex justify-between gap-3"><dt class="flex items-center gap-1.5 text-ink-2"><span class="hatch-missed h-2.5 w-2.5 rounded-[2px]"></span>{{ t('common.underTrees') }}</dt><dd class="num font-mono text-ink">{{ fixed(hover.u.hidden) }} {{ t('common.km2') }}</dd></div>
                <div class="flex justify-between gap-3 border-t border-rule pt-1"><dt class="text-ink-2">{{ t('stats.cbandMissed') }}</dt><dd class="num font-mono font-semibold text-missed">{{ n(share(hover.u)) }}%</dd></div>
              </dl>
            </div>
          </transition>
        </div>
      </section>

      <!-- Table -->
      <section class="mt-16" aria-labelledby="table-title">
        <div v-reveal class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <h2 id="table-title" class="font-display text-2xl font-bold tracking-tight text-ink">{{ t('stats.tableTitle') }}</h2>
          <div class="flex gap-2">
            <label class="relative flex-1 sm:w-64 sm:flex-none">
              <span class="sr-only">{{ t('stats.filterLabel') }}</span>
              <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-3" />
              <input v-model="query" type="search" :placeholder="t('stats.filter')" class="w-full rounded-md border border-rule bg-card py-2 pl-9 pr-3 text-sm text-ink transition-colors placeholder:text-ink-3 focus:border-ink focus:outline-none" />
            </label>
            <label>
              <span class="sr-only">{{ t('stats.district') }}</span>
              <select v-model="district" class="h-full rounded-md border border-rule bg-card px-3 text-sm text-ink focus:border-ink focus:outline-none">
                <option value="">{{ t('stats.allDistricts') }}</option>
                <option value="Chattogram">{{ lang === 'bn' ? 'চট্টগ্রাম' : 'Chattogram' }}</option>
                <option value="Feni">{{ lang === 'bn' ? 'ফেনী' : 'Feni' }}</option>
              </select>
            </label>
          </div>
        </div>

        <div class="thin-scroll mt-5 overflow-x-auto">
          <table class="w-full min-w-[46rem] border-collapse text-left text-sm">
            <thead>
              <tr class="border-b-2 border-ink">
                <th v-for="c in columns" :key="c.key" scope="col" class="py-2.5 pr-4 last:pr-0" :class="c.num ? 'text-right' : ''" :aria-sort="sortKey === c.key ? (sortDir === 1 ? 'ascending' : 'descending') : 'none'">
                  <button type="button" class="inline-flex items-center gap-1 font-mono text-[11px] font-medium uppercase tracking-[0.1em] text-ink-3 transition-colors hover:text-ink" :class="sortKey === c.key ? '!text-ink' : ''" @click="sortBy(c.key)">
                    {{ t('stats.cols')[c.key] }}
                    <ArrowDown v-if="sortKey === c.key" class="h-3 w-3 transition-transform duration-300" :class="sortDir === 1 ? 'rotate-180' : ''" />
                  </button>
                </th>
                <th class="w-8"><span class="sr-only">{{ t('stats.openOnMap') }}</span></th>
              </tr>
            </thead>
            <TransitionGroup tag="tbody" name="row">
              <tr v-for="u in rows" :key="u.id" class="group cursor-pointer border-b border-rule transition-colors hover:bg-card" @click="$router.push({ path: '/map', query: { u: u.id } })">
                <td class="py-3.5 pr-4">
                  <span class="font-medium text-ink">{{ loc(u) }}</span>
                  <span class="ml-2 text-xs text-ink-3">{{ lang === 'en' ? u.bn : u.name }}</span>
                </td>
                <td class="py-3.5 pr-4 text-ink-2">{{ loc(u, 'district') }}</td>
                <td class="num py-3.5 pr-4 text-right font-mono text-ink">{{ fixed(u.hidden) }}</td>
                <td class="num py-3.5 pr-4 text-right font-mono text-ink-2">{{ fixed(u.both) }}</td>
                <td class="num py-3.5 pr-4 text-right font-mono text-ink-2">{{ n(u.share) }}%</td>
                <td class="num py-3.5 pr-4 text-right font-mono font-semibold text-ink">{{ n(u.people) }}</td>
                <td class="py-3.5 pr-4">
                  <span class="inline-flex items-center gap-1.5 text-xs" :class="u.agree === 'both-dates' ? 'text-missed' : 'text-ink-2'">
                    <component :is="u.agree === 'both-dates' ? CircleCheck : CircleDashed" class="h-3.5 w-3.5" />
                    {{ t('common.agree')[u.agree] }}
                  </span>
                </td>
                <td class="py-3.5 text-ink-3 transition-colors group-hover:text-ink"><ArrowUpRight class="h-4 w-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" /></td>
              </tr>
              <tr v-if="!rows.length" key="empty">
                <td colspan="8" class="py-12 text-center">
                  <p class="font-medium text-ink">{{ t('stats.empty', { q: query }) }}</p>
                  <button type="button" class="mt-2 text-sm text-ink-2 underline underline-offset-2 hover:text-ink" @click="query = ''; district = ''">{{ t('stats.clear') }}</button>
                </td>
              </tr>
            </TransitionGroup>
            <tfoot v-if="rows.length > 1">
              <tr class="border-t-2 border-ink font-semibold">
                <td class="py-3 pr-4 text-ink" colspan="2">{{ t('stats.total', { n: n(rows.length) }) }}</td>
                <td class="num py-3 pr-4 text-right font-mono text-ink">{{ fixed(sum('hidden')) }}</td>
                <td class="num py-3 pr-4 text-right font-mono text-ink-2">{{ fixed(sum('both')) }}</td>
                <td class="num py-3 pr-4 text-right font-mono text-ink-2">{{ n(Math.round((sum('hidden') / (sum('hidden') + sum('both'))) * 100)) }}%</td>
                <td class="num py-3 pr-4 text-right font-mono text-ink">{{ n(sum('people')) }}</td>
                <td colspan="2"></td>
              </tr>
            </tfoot>
          </table>
        </div>
        <p class="mt-3 text-xs text-ink-3">{{ t('stats.footnote') }}</p>
      </section>

      <div role="status" aria-live="polite" class="fixed bottom-5 left-1/2 z-50 -translate-x-1/2">
        <transition name="page">
          <p v-if="toast" class="flex items-center gap-2 rounded-md bg-ink px-4 py-2.5 text-sm text-paper shadow-lg">
            <Check class="h-4 w-4" /> {{ toast }}
          </p>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { FileSpreadsheet, MapPinned, Info, Search, ArrowDown, ArrowUpRight, CircleCheck, CircleDashed, Check } from 'lucide-vue-next'
import CountUp from '../components/CountUp.vue'
import GradientBackdrop from '../components/GradientBackdrop.vue' // SOFFIT GRADIENT (trial)
import { upazilas, totals, agreeLabel } from '../data/concept'
import { t, n, fixed, loc, lang } from '../i18n'
import { onVisible, reducedMotion } from '../motion'

const share = (u) => Math.round((u.hidden / (u.hidden + u.both)) * 100)

const kpis = [
  { value: totals.people, decimals: 0 },
  { value: totals.hidden, decimals: 1, unit: 'km2' },
  { value: Math.round((totals.hidden / (totals.hidden + totals.both)) * 100), decimals: 0, unit: '%' },
  { value: totals.hill, decimals: 0 },
]

// Chart
const chartRef = ref(null)
const hover = ref(null)
const grown = ref(reducedMotion)
const chartRows = [...upazilas].sort((a, b) => b.hidden - a.hidden)
const maxTotal = Math.ceil(Math.max(...upazilas.map((u) => u.hidden + u.both)) / 2) * 2
const ticks = Array.from({ length: maxTotal / 2 + 1 }, (_, i) => i * 2).filter((v) => v % 4 === 0 || maxTotal <= 8)

let stopGrow = () => {}
onMounted(() => {
  stopGrow = onVisible(chartRef.value, () => (grown.value = true), 0.2)
})
onBeforeUnmount(() => stopGrow())

function onHover(e, u) {
  const r = chartRef.value.getBoundingClientRect()
  const x = e.clientX - r.left + 16
  hover.value = { u, x: Math.min(x, r.width - 248), y: e.clientY - r.top + 12 }
}

// Table
const query = ref('')
const district = ref('')
const sortKey = ref('people')
const sortDir = ref(-1)

const columns = [
  { key: 'name' },
  { key: 'district' },
  { key: 'hidden', num: true },
  { key: 'both', num: true },
  { key: 'share', num: true },
  { key: 'people', num: true },
  { key: 'agree' },
]

function sortBy(key) {
  if (sortKey.value === key) sortDir.value *= -1
  else {
    sortKey.value = key
    sortDir.value = ['name', 'district', 'agree'].includes(key) ? 1 : -1
  }
}

const rows = computed(() => {
  const q = query.value.trim().toLowerCase()
  const bn = lang.value === 'bn'
  return upazilas
    .filter((u) => (!district.value || u.district === district.value) && (!q || u.name.toLowerCase().includes(q) || u.bn.includes(q)))
    .map((u) => ({ ...u, share: share(u) }))
    .sort((a, b) => {
      const key = sortKey.value
      // Text columns sort by the name shown in the current language
      const va = key === 'name' && bn ? a.bn : key === 'district' && bn ? a.districtBn : a[key]
      const vb = key === 'name' && bn ? b.bn : key === 'district' && bn ? b.districtBn : b[key]
      return (typeof va === 'string' ? va.localeCompare(vb, bn ? 'bn' : 'en') : va - vb) * sortDir.value
    })
})

const sum = (k) => rows.value.reduce((s, u) => s + u[k], 0)

// Exports (file contents stay English + Bangla names, for any GIS tool)
const toast = ref('')
function download(name, type, text) {
  const url = URL.createObjectURL(new Blob([text], { type }))
  const a = document.createElement('a')
  a.href = url
  a.download = name
  a.click()
  URL.revokeObjectURL(url)
  toast.value = t('stats.downloaded', { name })
  setTimeout(() => (toast.value = ''), 2600)
}

function exportCsv() {
  const head = 'upazila,upazila_bn,district,hidden_flood_km2,open_water_km2,missed_share_pct,people,status,lon,lat,note'
  const lines = rows.value.map((u) =>
    [u.name, u.bn, u.district, u.hidden, u.both, u.share, u.people, agreeLabel[u.agree], u.center[0], u.center[1], 'ILLUSTRATIVE concept data'].join(','),
  )
  download('meghbhed_upazilas_concept.csv', 'text/csv;charset=utf-8', '﻿' + [head, ...lines].join('\n'))
}

function exportKml() {
  const marks = rows.value
    .map(
      (u) => `  <Placemark>
    <name>${u.name} (${u.district})</name>
    <description>${agreeLabel[u.agree]}. Under trees: ${u.hidden} km². People: ${u.people}. ILLUSTRATIVE concept data.</description>
    <ExtendedData>
      <Data name="hidden_flood_km2"><value>${u.hidden}</value></Data>
      <Data name="people"><value>${u.people}</value></Data>
    </ExtendedData>
    <Point><coordinates>${u.center[0]},${u.center[1]},0</coordinates></Point>
  </Placemark>`,
    )
    .join('\n')
  download(
    'meghbhed_upazilas_concept.kml',
    'application/vnd.google-earth.kml+xml',
    `<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2">\n<Document>\n  <name>MeghBhed: likely-missed upazilas (concept)</name>\n${marks}\n</Document>\n</kml>\n`,
  )
}
</script>

<style scoped>
.tip-enter-active,
.tip-leave-active {
  transition: opacity 0.15s ease;
}
.tip-enter-from,
.tip-leave-to {
  opacity: 0;
}
/* Rows slide into their new place when sorting or filtering */
.row-move {
  transition: transform 0.45s cubic-bezier(0.16, 1, 0.3, 1);
}
.row-enter-active,
.row-leave-active {
  transition: opacity 0.25s ease;
}
.row-enter-from,
.row-leave-to {
  opacity: 0;
}
</style>
