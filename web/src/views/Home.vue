<template>
  <div class="w-full">
    <!-- Hero -->
    <section class="contours relative overflow-hidden border-b border-rule">
      <GradientBackdrop fade="side" /><!-- SOFFIT GRADIENT (trial) -->
      <div class="relative mx-auto grid max-w-[88rem] gap-10 px-4 pb-14 pt-10 sm:px-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-14 lg:pb-20 lg:pt-16">
        <div v-reveal.stagger class="flex flex-col justify-center">
          <p class="inline-flex w-fit border border-ink/70 px-2 py-1 font-mono text-[11px] font-medium uppercase tracking-[0.14em] text-ink">
            {{ t('home.badge') }}
          </p>
          <h1 class="mt-6 font-display text-[2.6rem] font-bold leading-[1.02] tracking-[-0.035em] text-ink sm:text-5xl xl:text-6xl balance" :class="lang === 'bn' ? '!leading-[1.22] !tracking-normal' : ''">
            {{ t('home.titleA') }}<span class="text-missed">{{ t('home.titleAccent') }}</span>{{ t('home.titleB') }}
          </h1>
          <p class="mt-6 max-w-[32rem] text-lg leading-relaxed text-ink-2 pretty">{{ t('home.lead') }}</p>

          <div class="mt-8 flex flex-wrap items-center gap-x-6 gap-y-3">
            <router-link to="/map" class="btn btn-ink group px-5 py-3">
              {{ t('home.ctaMap') }}
              <ArrowRight class="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
            </router-link>
            <a href="#method" class="inline-flex items-center gap-1.5 text-sm font-medium text-ink underline decoration-rule decoration-2 underline-offset-[6px] transition-colors hover:decoration-ink">
              {{ t('home.ctaMethod') }}
            </a>
          </div>
        </div>

        <!-- Map plate -->
        <figure v-reveal="150">
          <div class="overflow-hidden rounded-lg border border-rule bg-card shadow-[0_1px_2px_rgb(15_28_46/0.06),0_12px_32px_rgb(15_28_46/0.10)]">
            <div class="flex items-center justify-between border-b border-rule px-3 py-2">
              <span class="font-mono text-[11px] font-semibold uppercase tracking-[0.12em] text-ink">{{ t('home.plate') }}</span>
              <span class="font-mono text-[11px] text-ink-3">22.9°N 91.6°E</span>
            </div>
            <div class="h-[360px] sm:h-[460px] lg:h-[520px]">
              <SwipeMap :interactive="false" :show-dates="false" :initial-split="46" :initial-view="{ center: [91.62, 22.84], zoom: 8.55 }" />
            </div>
            <div class="flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-rule px-3 py-2.5 text-xs text-ink-2">
              <span class="inline-flex items-center gap-2"><span class="h-3 w-4 rounded-[2px] bg-water"></span> {{ t('home.legendOpen') }}</span>
              <span class="inline-flex items-center gap-2"><span class="hatch-missed h-3 w-4 rounded-[2px] border border-missed"></span> {{ t('home.legendHidden') }}</span>
            </div>
          </div>
          <figcaption class="mt-3 w-fit rounded-sm bg-paper/85 px-1.5 py-0.5 font-mono text-[11px] text-ink-3">{{ t('home.figCaption') }}</figcaption>
        </figure>
      </div>
    </section>

    <!-- The problem -->
    <section class="mx-auto max-w-[88rem] px-4 py-20 sm:px-6 lg:py-28">
      <div class="grid gap-12 lg:grid-cols-12">
        <div v-reveal class="lg:col-span-4">
          <h2 class="font-display text-4xl font-bold leading-tight tracking-tight text-ink balance">{{ t('home.problem.title') }}</h2>
        </div>
        <div class="lg:col-span-7 lg:col-start-6">
          <p v-reveal="80" class="text-lg leading-relaxed text-ink-2 pretty">{{ t('home.problem.body') }}</p>

          <dl v-reveal.stagger="120" class="mt-10 grid grid-cols-3 border-y border-ink/80">
            <div v-for="(s, i) in stats" :key="s.key" class="py-5" :class="i > 0 ? 'border-l border-rule pl-4 sm:pl-6' : ''">
              <dt class="label !text-[10px] sm:!text-[11px]">{{ t(s.key) }}</dt>
              <dd class="mt-2 font-display text-3xl font-bold tracking-tight text-ink sm:text-5xl">
                <CountUp :value="s.value" :decimals="s.decimals" />{{ s.suffix }}
              </dd>
            </div>
          </dl>
          <p class="mt-3 font-mono text-[11px] text-ink-3">
            {{ t('common.source') }}: <a class="underline underline-offset-2 hover:text-ink" href="https://bangladesh.un.org/en/319868-bangladesh-situation-report-2-flash-flood-and-landslides-23-july-2026" target="_blank" rel="noopener">{{ sitrep.source }}</a>{{ t('home.problem.sourceTail') }}
          </p>

          <blockquote v-reveal class="mt-12 border-l-[3px] border-missed pl-6">
            <p class="font-display text-2xl font-medium leading-snug text-ink sm:text-[1.7rem] balance">{{ t('home.problem.quote') }}</p>
          </blockquote>
        </div>
      </div>
    </section>

    <!-- Why L-band -->
    <section class="border-y border-rule bg-card">
      <div class="mx-auto max-w-[88rem] px-4 py-20 sm:px-6 lg:py-28">
        <div v-reveal class="max-w-2xl">
          <h2 class="font-display text-4xl font-bold leading-tight tracking-tight text-ink balance">{{ t('home.why.title') }}</h2>
          <p class="mt-5 text-lg leading-relaxed text-ink-2 pretty">
            {{ whyBody[0] }}<em class="font-medium text-ink">{{ t('home.why.em') }}</em>{{ whyBody[1] }}
          </p>
        </div>

        <div v-reveal.stagger class="mt-12 grid gap-6 lg:grid-cols-2">
          <figure v-for="panel in panels" :key="panel.id" class="rounded-lg border border-rule bg-paper p-4 transition-[transform,box-shadow] duration-500 hover:-translate-y-1 hover:shadow-[0_12px_32px_rgb(15_28_46/0.10)] sm:p-5">
            <div class="flex items-baseline justify-between">
              <p class="font-mono text-xs font-semibold uppercase tracking-[0.12em]" :class="panel.id === 'c' ? 'text-ink-2' : 'text-missed'">{{ panel.title }}</p>
              <p class="font-mono text-xs text-ink-3">λ ≈ {{ fixed(panel.wave, panel.wave % 1 ? 1 : 0) }} {{ t('home.why.cm') }}</p>
            </div>
            <ScatterDiagram :band="panel.id" class="mt-3 w-full" />
            <figcaption class="mt-3 text-sm text-ink-2">{{ t(panel.caption) }}</figcaption>
          </figure>
        </div>

        <div v-reveal class="thin-scroll mt-10 overflow-x-auto">
          <table class="w-full min-w-[34rem] border-collapse text-left text-sm">
            <thead>
              <tr class="border-b-2 border-ink">
                <th class="py-2.5 pr-4 font-medium text-ink-3"></th>
                <th class="py-2.5 pr-4 font-mono text-xs font-semibold uppercase tracking-[0.1em] text-ink">C-band · Sentinel-1</th>
                <th class="py-2.5 font-mono text-xs font-semibold uppercase tracking-[0.1em] text-missed">L-band · NISAR</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in t('home.why.rows')" :key="row[0]" class="border-b border-rule">
                <th scope="row" class="py-3 pr-4 font-medium text-ink">{{ row[0] }}</th>
                <td class="py-3 pr-4 text-ink-2">{{ row[1] }}</td>
                <td class="py-3 text-ink-2">{{ row[2] }}</td>
              </tr>
            </tbody>
          </table>
          <p class="mt-3 text-sm text-ink-2">{{ t('home.why.note') }}</p>
        </div>
      </div>
    </section>

    <!-- Method -->
    <section id="method" class="mx-auto max-w-[88rem] scroll-mt-20 px-4 py-20 sm:px-6 lg:py-28">
      <div class="grid gap-12 lg:grid-cols-12">
        <div class="lg:col-span-4">
          <div v-reveal class="lg:sticky lg:top-28">
            <h2 class="font-display text-4xl font-bold leading-tight tracking-tight text-ink balance">{{ t('home.method.title') }}</h2>
            <p class="mt-4 text-ink-2 pretty">{{ t('home.method.body') }}</p>
            <a href="https://github.com/ProttoyDip/MeghBhed/blob/main/docs/METHOD.md" target="_blank" rel="noopener" class="group mt-6 inline-flex items-center gap-1.5 text-sm font-medium text-ink underline decoration-rule decoration-2 underline-offset-[6px] hover:decoration-ink">
              {{ t('home.method.link') }} <ArrowUpRight class="h-4 w-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
            </a>
          </div>
        </div>

        <ol v-reveal.stagger class="lg:col-span-7 lg:col-start-6">
          <li v-for="(step, i) in t('home.method.steps')" :key="i" class="grid grid-cols-[3rem_1fr] gap-4 border-t border-rule py-7 first:border-t-2 first:border-ink">
            <span class="num font-display text-3xl font-bold text-missed">{{ n(i + 1) }}</span>
            <div>
              <h3 class="text-lg font-semibold text-ink">{{ step.title }}</h3>
              <p class="mt-1.5 leading-relaxed text-ink-2 pretty">{{ step.desc }}</p>
              <p class="mt-2 font-mono text-xs text-ink-3">{{ stepData[i] }}</p>
            </div>
          </li>
          <li class="border-t border-rule pt-7">
            <div class="rounded-lg border border-rule bg-card p-5 shadow-[0_1px_2px_rgb(15_28_46/0.05)]">
              <p class="label !text-ink">{{ t('home.method.ruleTitle') }}</p>
              <p class="mt-2 text-sm leading-relaxed text-ink-2">
                {{ ruleText[0] }}<strong class="font-semibold text-missed">{{ t('home.method.ruleHl') }}</strong>{{ ruleText[1] }}
              </p>
              <table class="mt-4 w-full text-left text-sm">
                <tbody class="font-mono text-xs">
                  <tr v-for="row in t('home.method.thresholds')" :key="row[0]" class="border-t border-rule">
                    <td class="py-2 pr-3 text-ink-3">{{ row[0] }}</td>
                    <td class="py-2 text-ink">{{ row[1] }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </li>
        </ol>
      </div>
    </section>

    <!-- Hill risk -->
    <section class="border-y border-rule bg-hill-soft/50">
      <div class="mx-auto max-w-[88rem] px-4 py-16 sm:px-6 lg:py-20">
        <div v-reveal class="max-w-[65ch]">
          <p class="label !text-hill">{{ t('home.hill.label') }}</p>
          <h2 class="mt-4 font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">{{ t('home.hill.title') }}</h2>
        </div>
        <div v-reveal="100" class="mt-6 max-w-[65ch]">
          <p class="leading-relaxed text-ink-2 pretty">{{ t('home.hill.body') }}</p>
          <p class="mt-4 flex gap-3 leading-relaxed text-ink">
            <TriangleAlert class="mt-0.5 h-5 w-5 shrink-0 text-hill" />
            <span>{{ t('home.hill.warn') }}</span>
          </p>
        </div>
      </div>
    </section>

    <!-- Data -->
    <section class="mx-auto max-w-[88rem] px-4 py-20 sm:px-6 lg:py-28">
      <div v-reveal class="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 class="font-display text-4xl font-bold tracking-tight text-ink">{{ t('home.data.title') }}</h2>
        </div>
        <a href="https://github.com/ProttoyDip/MeghBhed/blob/main/docs/DATA.md" target="_blank" rel="noopener" class="group inline-flex items-center gap-1.5 text-sm font-medium text-ink underline decoration-rule decoration-2 underline-offset-[6px] hover:decoration-ink">
          {{ t('home.data.link') }} <ArrowUpRight class="h-4 w-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
        </a>
      </div>
      <ul v-reveal.stagger class="mt-10 grid gap-x-8 gap-y-8 border-t-2 border-ink pt-8 sm:grid-cols-2 lg:grid-cols-4">
        <li v-for="d in datasets" :key="d.name">
          <a :href="d.url" target="_blank" rel="noopener" class="group block">
            <span class="flex items-baseline justify-between gap-3">
              <span class="font-semibold text-ink underline decoration-rule decoration-2 underline-offset-4 transition-colors group-hover:decoration-ink">{{ d.name }}</span>
              <span class="num shrink-0 font-mono text-xs text-ink-3">{{ d.res }}</span>
            </span>
            <span class="mt-1.5 block text-sm text-ink-2">{{ lang === 'bn' ? d.useBn : d.use }}</span>
            <span class="mt-0.5 block text-xs text-ink-3">{{ d.provider }}</span>
          </a>
        </li>
      </ul>
    </section>

    <!-- Team -->
    <section class="border-t border-rule bg-card">
      <div class="mx-auto max-w-[88rem] px-4 py-20 sm:px-6 lg:py-24">
        <div v-reveal>
          <h2 class="font-display text-4xl font-bold tracking-tight text-ink">{{ t('home.team.title') }}</h2>
          <p class="mt-3 text-ink-2">{{ t('home.team.body') }}</p>
        </div>
        <ul v-reveal.stagger class="mt-12 grid grid-cols-2 gap-x-6 gap-y-10 sm:grid-cols-3 lg:grid-cols-6">
          <li v-for="m in team" :key="m.name" class="group">
            <div class="aspect-[4/5] overflow-hidden rounded-lg border border-rule bg-paper-2">
              <img :src="m.image" :alt="t('home.team.portrait', { name: m.name })" loading="lazy" class="h-full w-full object-cover grayscale-[35%] transition duration-700 group-hover:scale-[1.04] group-hover:grayscale-0" />
            </div>
            <p class="mt-3 font-medium leading-snug text-ink">{{ m.name }}</p>
            <p class="mt-0.5 font-mono text-[11px] uppercase tracking-[0.1em] text-ink-3">{{ lang === 'bn' ? m.roleBn : m.role }}</p>
          </li>
        </ul>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, defineAsyncComponent } from 'vue'
import { ArrowRight, ArrowUpRight, TriangleAlert } from 'lucide-vue-next'
import ScatterDiagram from '../components/ScatterDiagram.vue'
import CountUp from '../components/CountUp.vue'
import GradientBackdrop from '../components/GradientBackdrop.vue' // SOFFIT GRADIENT (trial)
import { sitrep } from '../data/concept'
import { t, n, fixed, lang } from '../i18n'

const SwipeMap = defineAsyncComponent(() => import('../components/SwipeMap.vue'))

// 1.28 M people = 12.8 lakh in Bangla
const stats = computed(() => [
  { key: 'home.problem.affected', value: lang.value === 'bn' ? 12.8 : 1.28, decimals: lang.value === 'bn' ? 1 : 2, suffix: t('home.problem.million') },
  { key: 'home.problem.deaths', value: sitrep.deaths, decimals: 0, suffix: '' },
  { key: 'home.problem.districts', value: sitrep.districts, decimals: 0, suffix: '' },
])

const whyBody = computed(() => t('home.why.body').split('{em}'))
const ruleText = computed(() => t('home.method.rule').split('{hl}'))

const panels = [
  { id: 'c', title: 'C-band · Sentinel-1', wave: 5.6, caption: 'home.why.captionC' },
  { id: 'l', title: 'L-band · NISAR', wave: 24, caption: 'home.why.captionL' },
]

const stepData = [
  'NISAR L2 GCOV · Provisional V1 · 10 m',
  'ESA WorldCover 2021 · 10 m',
  'OPERA DSWx-S1 V1 · 30 m',
  'WorldPop · 100 m · HDX COD-AB',
]

const datasets = [
  { name: 'NISAR L2 GCOV', provider: 'NASA / ISRO, ASF DAAC', use: 'Hidden-flood detection', useBn: 'লুকানো বন্যা শনাক্তকরণ', res: '10 m', url: 'https://nisar-docs.asf.alaska.edu/' },
  { name: 'OPERA DSWx-S1', provider: 'NASA JPL, PO.DAAC', use: 'C-band comparison', useBn: 'C-band তুলনা', res: '30 m', url: 'https://doi.org/10.5067/OPDSWS1-L3V1' },
  { name: 'ESA WorldCover 2021', provider: 'ESA', use: 'Tree and built-up masks', useBn: 'গাছ ও বসতির মাস্ক', res: '10 m', url: 'https://esa-worldcover.org/' },
  { name: 'WorldPop counts', provider: 'Univ. of Southampton', use: 'People per upazila', useBn: 'উপজেলাপ্রতি জনসংখ্যা', res: '100 m', url: 'https://hub.worldpop.org/' },
  { name: 'GPM IMERG V07', provider: 'NASA GES DISC', use: 'July rainfall', useBn: 'জুলাইয়ের বৃষ্টিপাত', res: '0.1°', url: 'https://doi.org/10.5067/GPM/IMERGDL/DAY/07' },
  { name: 'LHASA nowcast', provider: 'NASA GSFC', use: 'Landslide hazard', useBn: 'ভূমিধস ঝুঁকি', res: '~1 km', url: 'https://portal.nccs.nasa.gov/datashare/landslides/nrt/' },
  { name: 'Copernicus DEM GLO-30', provider: 'ESA / Copernicus', use: 'Slope', useBn: 'ঢাল', res: '30 m', url: 'https://portal.opentopography.org/datasetMetadata?otCollectionID=OT.032021.4326.1' },
  { name: 'Admin boundaries (COD-AB)', provider: 'BBS via OCHA HDX', use: 'Upazila polygons', useBn: 'উপজেলার সীমানা', res: 'Vector', url: 'https://data.humdata.org/dataset/cod-ab-bgd' },
]

const team = [
  { name: 'Prottoy Saha Dip', role: 'GIS & radar', roleBn: 'জিআইএস ও রাডার', image: '/dip.jpg' },
  { name: 'Md. Thouhidul Islam', role: 'Data analytics', roleBn: 'ডেটা বিশ্লেষণ', image: '/apurbo.jpg' },
  { name: 'S.M. Sao.Mio Rashid Sakin', role: 'Backend & AI', roleBn: 'ব্যাকএন্ড ও এআই', image: '/sakin.jpg' },
  { name: 'Shuvo Singh Partho', role: 'ML & full stack', roleBn: 'এমএল ও ফুল স্ট্যাক', image: '/partho.jpg' },
  { name: 'Eva Jahan', role: 'Data collection', roleBn: 'ডেটা সংগ্রহ', image: '/eva.jpg' },
  { name: 'Suchismita Sarker', role: 'Design & pitch', roleBn: 'ডিজাইন ও উপস্থাপনা', image: '/suchi.jpg' },
]
</script>
