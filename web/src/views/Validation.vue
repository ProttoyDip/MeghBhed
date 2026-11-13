<template>
  <div class="w-full">
    <!-- Header band -->
    <section class="relative overflow-hidden">
      <GradientBackdrop fade="side" /><!-- SOFFIT GRADIENT (trial) -->
      <div class="relative mx-auto max-w-[88rem] px-4 pt-10 sm:px-6 lg:pt-14">
        <header v-reveal class="border-b-2 border-ink pb-8">
          <div class="max-w-3xl">
            <p class="label">{{ t('validation.label') }}</p>
            <h1 class="mt-3 font-display text-4xl font-bold tracking-tight text-ink sm:text-5xl">{{ t('validation.title') }}</h1>
            <p v-if="ready" class="mt-4 text-lg leading-relaxed text-ink-2 pretty" data-testid="verdict">{{ verdict }}</p>
            <p v-else class="mt-4 text-ink-2">{{ t('validation.missing') }}</p>
          </div>
        </header>
      </div>
    </section>

    <div v-if="ready" class="mx-auto w-full max-w-[88rem] px-4 pb-10 sm:px-6 lg:pb-14">
      <!-- One card per model -->
      <section class="mt-10" aria-labelledby="cards-title">
        <h2 id="cards-title" v-reveal class="font-display text-2xl font-bold tracking-tight text-ink">{{ t('validation.cardsTitle') }}</h2>
        <p class="mt-1 max-w-3xl text-sm text-ink-2">{{ t('validation.cardsLead') }}</p>
        <ul v-reveal.stagger="80" class="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <li v-for="m in models" :key="m.key" class="rounded-lg border bg-card p-5" :class="m.used ? 'border-ink shadow-[0_4px_16px_rgb(15_28_46/0.10)]' : 'border-rule'" :data-model="m.key">
            <div class="flex items-start justify-between gap-2">
              <h3 class="text-lg font-semibold text-ink">{{ m.name }}</h3>
              <span v-if="m.used" class="shrink-0 rounded-sm border border-ok/60 px-1.5 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-[0.08em] text-ok">{{ t('validation.used') }}</span>
            </div>
            <p class="mt-0.5 font-mono text-[11px] text-ink-3">{{ m.cutoffNote }}</p>
            <dl class="mt-4 space-y-3">
              <div v-for="k in METRICS" :key="k">
                <dt class="text-sm text-ink">{{ t(`validation.metrics.${k}.plain`) }}</dt>
                <dd class="flex items-baseline justify-between gap-3">
                  <span class="font-mono text-[11px] uppercase tracking-[0.08em] text-ink-3">{{ t(`validation.metrics.${k}.term`) }}</span>
                  <span class="num font-display text-2xl font-bold text-ink">{{ pct(m[k]) }}</span>
                </dd>
              </div>
            </dl>
          </li>
        </ul>
      </section>

      <!-- Bar chart of the metrics -->
      <section class="mt-14" aria-labelledby="chart-title">
        <div v-reveal class="flex flex-wrap items-end justify-between gap-4">
          <h2 id="chart-title" class="font-display text-2xl font-bold tracking-tight text-ink">{{ t('validation.chartTitle') }}</h2>
          <ul class="flex flex-wrap gap-x-5 gap-y-2 text-sm text-ink-2" :aria-label="t('stats.legend')">
            <li v-for="(k, i) in METRICS" :key="k" class="inline-flex items-center gap-2"><span class="h-3 w-4 rounded-[2px]" :class="BAR_CLASS[i]"></span>{{ t(`validation.metrics.${k}.term`) }}</li>
          </ul>
        </div>
        <div class="mt-6 space-y-5" role="img" :aria-label="t('validation.chartAria')">
          <div v-for="m in models" :key="m.key" class="grid grid-cols-[7.5rem_1fr] items-center gap-3 sm:grid-cols-[11rem_1fr]">
            <span class="text-right text-sm text-ink">{{ m.name }}</span>
            <div class="space-y-1">
              <div v-for="(k, i) in METRICS" :key="k" class="flex items-center gap-2">
                <span class="h-3 rounded-r-[3px]" :class="BAR_CLASS[i]" :style="{ width: `${m[k] * 88}%` }"></span>
                <span class="num font-mono text-[11px] text-ink-2">{{ pct(m[k]) }}</span>
              </div>
            </div>
          </div>
        </div>
        <p class="mt-4 max-w-3xl text-xs text-ink-3">{{ targetsNote }}</p>
      </section>

      <!-- Every cut-off: three rows per trained model -->
      <section class="mt-14" aria-labelledby="cutoffs-title">
        <h2 id="cutoffs-title" v-reveal class="font-display text-2xl font-bold tracking-tight text-ink">{{ t('validation.cutoffsTitle') }}</h2>
        <p class="mt-1 max-w-3xl text-sm text-ink-2">{{ t('validation.cutoffsLead') }}</p>
        <div class="thin-scroll relative mt-5 overflow-x-auto">
          <table class="w-full min-w-[46rem] border-collapse text-left text-sm" data-table="cutoffs">
            <thead>
              <tr class="border-b-2 border-ink">
                <th v-for="(c, i) in t('validation.cutoffsCols')" :key="c" scope="col" class="py-2.5 pr-4 font-mono text-[11px] font-medium uppercase tracking-[0.1em] text-ink-3 last:pr-0" :class="i > 1 ? 'text-right' : ''">{{ c }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(r, i) in cutoffRows" :key="i" class="border-b border-rule" :class="r.breakEven ? 'bg-hill-soft/40' : ''" :data-cutoff="r.kind">
                <td class="py-2.5 pr-4 font-medium text-ink">{{ r.name }}</td>
                <td class="py-2.5 pr-4 text-ink-2">{{ r.label }}<span v-if="r.breakEven" class="text-hill"> *</span></td>
                <td class="num py-2.5 pr-4 text-right font-mono text-ink">{{ pct(r.precision) }}</td>
                <td class="num py-2.5 pr-4 text-right font-mono text-ink">{{ pct(r.recall) }}</td>
                <td class="num py-2.5 pr-4 text-right font-mono text-ink">{{ pct(r.f1) }}</td>
                <td class="num py-2.5 text-right font-mono text-ink-2">{{ pct(r.accuracy) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="mt-3 max-w-3xl text-xs text-ink-3"><span class="text-hill">*</span> {{ t('validation.breakEvenNote') }}</p>
      </section>

      <!-- Independent tests -->
      <section class="mt-14" aria-labelledby="tests-title">
        <h2 id="tests-title" v-reveal class="font-display text-2xl font-bold tracking-tight text-ink">{{ t('validation.testsTitle') }}</h2>
        <p class="mt-1 max-w-3xl text-sm text-ink-2">{{ testsLead }}</p>
        <div class="thin-scroll relative mt-5 overflow-x-auto">
          <table class="w-full min-w-[40rem] border-collapse text-left text-sm" data-table="independent">
            <thead>
              <tr class="border-b-2 border-ink">
                <th v-for="(c, i) in t('validation.testsCols')" :key="c" scope="col" class="py-2.5 pr-4 font-mono text-[11px] font-medium uppercase tracking-[0.1em] text-ink-3 last:pr-0" :class="i ? 'text-right' : ''">{{ c }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in models" :key="m.key" class="border-b border-rule">
                <td class="py-3 pr-4">
                  <span class="font-medium text-ink">{{ m.name }}</span>
                  <span v-if="m.used" class="ml-2 rounded-sm border border-ok/60 px-1.5 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-[0.08em] text-ok">{{ t('validation.used') }}</span>
                </td>
                <td class="num py-3 pr-4 text-right font-mono text-ink">{{ fixed(m.nearFlooded) }}%</td>
                <td class="num py-3 pr-4 text-right font-mono text-ink">{{ fixed(m.nearDry) }}%</td>
                <td class="num py-3 pr-4 text-right font-mono text-ink-2">{{ fixed(m.nearFlooded / Math.max(m.nearDry, 0.01), 1) }}×</td>
                <td class="num py-3 text-right font-mono text-ink-2">{{ n(Math.round(m.km2)) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="mt-3 max-w-3xl text-xs text-ink-3">{{ t('validation.testsNote') }}</p>
      </section>

      <!-- SHAP -->
      <section class="mt-14" aria-labelledby="shap-title">
        <h2 id="shap-title" v-reveal class="font-display text-2xl font-bold tracking-tight text-ink">{{ t('validation.shapTitle') }}</h2>
        <p class="mt-1 max-w-3xl text-sm text-ink-2">{{ t('validation.shapLead') }}</p>
        <div class="mt-6 grid gap-8 lg:grid-cols-2">
          <div v-for="g in shapGroups" :key="g.model" :data-shap="g.model">
            <h3 class="font-mono text-xs font-semibold uppercase tracking-[0.12em] text-ink">{{ g.name }}</h3>
            <ul class="mt-3 space-y-2">
              <li v-for="f in g.rows" :key="f.feature" class="grid grid-cols-[9.5rem_1fr] items-center gap-3 text-sm">
                <span class="truncate text-right text-ink-2">{{ featureName(f) }}</span>
                <span class="flex items-center gap-2">
                  <span class="h-3 rounded-r-[3px] bg-water" :style="{ width: `${(f.mean_abs_shap / g.max) * 85}%` }"></span>
                  <span class="num font-mono text-[11px] text-ink-3">{{ fixed((f.mean_abs_shap / g.max) * 100, 0) }}</span>
                </span>
              </li>
            </ul>
          </div>
        </div>
        <p class="mt-4 max-w-3xl text-xs text-ink-3">{{ t('validation.shapNote') }}</p>
      </section>

      <!-- How to read this / under-tree test -->
      <section class="mt-14 grid gap-6 lg:grid-cols-2">
        <div v-reveal class="rounded-lg border border-rule bg-card p-5">
          <h2 class="font-display text-xl font-bold tracking-tight text-ink">{{ t('validation.readTitle') }}</h2>
          <dl class="mt-3 space-y-3 text-sm leading-relaxed">
            <div v-for="item in t('validation.readItems')" :key="item[0]">
              <dt class="font-semibold text-ink">{{ item[0] }}</dt>
              <dd class="text-ink-2">{{ item[1] }}</dd>
            </div>
          </dl>
        </div>
        <div v-reveal="80" class="rounded-lg border border-hill/50 bg-hill-soft/50 p-5">
          <h2 class="font-display text-xl font-bold tracking-tight text-ink">{{ t('validation.treesTitle') }}</h2>
          <p class="mt-3 text-sm leading-relaxed text-ink">{{ t('validation.treesBody') }}</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import GradientBackdrop from '../components/GradientBackdrop.vue' // SOFFIT GRADIENT (trial)
import { modelComparison as mc } from '../data/results'
import { t, n, fixed, lang } from '../i18n'

const METRICS = ['precision', 'recall', 'f1', 'accuracy']
const BAR_CLASS = ['bg-water', 'bg-missed', 'bg-ink', 'bg-ok']
const MODEL_KEYS = { 'rule (HH drop and HH level)': 'rule', logistic_regression: 'lr', random_forest: 'rf', lightgbm: 'lgbm' }

const pct = (v) => `${fixed(v * 100)}%`
const ready = computed(() => (mc.tuned?.length ?? 0) > 0)

// The rule as it stands, and each classifier at its tuned (nested break-even) cut-off
const models = computed(() =>
  (mc.tuned ?? []).map((m) => ({
    key: MODEL_KEYS[m.model] ?? m.model,
    name: t(`validation.models.${MODEL_KEYS[m.model] ?? 'rule'}`),
    used: m.model === mc.pipeline_uses,
    cutoffNote: m.cutoff == null ? t('validation.cutoffRule') : t('validation.cutoffTuned', { v: fixed(m.cutoff, 2) }),
    precision: m.precision,
    recall: m.recall,
    f1: m.f1,
    accuracy: m.accuracy,
    gap: m.max_gap_precision_recall_f1,
    nearFlooded: m.test_flagged_pct_near_flooded_points,
    nearDry: m.test_flagged_pct_near_dry_points,
    km2: m.flagged_km2,
  })),
)

// Every result: the rule, and three cut-offs per trained model. The break-even row is marked, because
// precision, recall and F1 are equal there by definition and it was not tested on unseen data.
const CUTOFF_KINDS = [
  ['as it stands', 'rule'],
  ['default cut-off', 'default'],
  ['fold-tuned', 'fold'],
  ['precision-recall break-even', 'breakEven'],
]
const cutoffRows = computed(() =>
  (mc.all_results ?? []).map((m) => {
    const kind = CUTOFF_KINDS.find(([start]) => m.cutoff_type.startsWith(start))?.[1] ?? 'default'
    return {
      kind,
      breakEven: kind === 'breakEven',
      name: t(`validation.models.${MODEL_KEYS[m.model] ?? 'rule'}`),
      label: t(`validation.cutoffKinds.${kind}`) + (m.cutoff == null ? '' : ` (${fixed(m.cutoff, 2)})`),
      precision: m.precision,
      recall: m.recall,
      f1: m.f1,
      accuracy: m.accuracy,
    }
  }),
)

const rule = computed(() => models.value.find((m) => m.used) ?? models.value[0])
const best = computed(() => [...models.value].filter((m) => !m.used).sort((a, b) => b.f1 - a.f1)[0])
const verdict = computed(() =>
  t('validation.verdict', {
    best: best.value.name,
    f1: pct(best.value.f1),
    bestDry: fixed(best.value.nearDry),
    ruleFlooded: fixed(rule.value.nearFlooded),
    ruleDry: fixed(rule.value.nearDry),
  }),
)
const targetsNote = computed(() =>
  t('validation.targetsNote', {
    gap: fixed(Math.min(...models.value.filter((m) => !m.used).map((m) => m.gap)), 3),
    target: fixed(mc.targets?.max_gap_precision_recall_f1 ?? 0.001, 3),
    acc: fixed((mc.targets?.min_accuracy ?? 0.9) * 100, 0),
  }),
)
const testsLead = computed(() => t('validation.testsLead', { flooded: n(mc.test?.flooded_points ?? 0), dry: n(mc.test?.dry_points ?? 0) }))

const shapGroups = computed(() =>
  ['lightgbm', 'random_forest']
    .map((model) => {
      const rows = (mc.shap ?? []).filter((s) => s.model === model).sort((a, b) => b.mean_abs_shap - a.mean_abs_shap)
      return { model, name: t(`validation.models.${MODEL_KEYS[model]}`), rows, max: Math.max(...rows.map((r) => r.mean_abs_shap), 1e-9) }
    })
    .filter((g) => g.rows.length),
)
const featureName = (f) => (lang.value === 'bn' ? (t('validation.features')[f.feature] ?? f.label) : f.label)
</script>
