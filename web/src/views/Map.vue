<template>
  <div class="relative flex h-[calc(100dvh-65px)] w-full overflow-hidden">
    <!-- Control panel -->
    <aside
      class="absolute inset-x-0 bottom-0 z-30 flex max-h-[72%] flex-col rounded-t-lg border-t border-ink/30 bg-paper shadow-[0_-8px_24px_rgb(15_28_46/0.18)] transition-transform duration-300 lg:static lg:max-h-none lg:w-[380px] lg:shrink-0 lg:translate-y-0 lg:rounded-none lg:border-r lg:border-t-0 lg:shadow-none"
      :class="panelOpen ? 'translate-y-0' : 'translate-y-[calc(100%-3.25rem)]'"
      :aria-label="t('map.controls')"
    >
      <button type="button" class="flex h-[3.25rem] shrink-0 items-center justify-between px-4 lg:hidden" :aria-expanded="panelOpen" @click="panelOpen = !panelOpen">
        <span class="text-sm font-semibold text-ink">{{ t('map.panelToggle') }}</span>
        <ChevronUp class="h-5 w-5 text-ink-2 transition-transform" :class="panelOpen ? 'rotate-180' : ''" />
      </button>

      <div class="thin-scroll flex-1 overflow-y-auto px-5 pb-6 lg:pt-6" data-lenis-prevent>
        <h1 class="hidden font-display text-2xl font-bold tracking-tight text-ink lg:block">{{ t('map.title') }}</h1>
        <p class="mt-1 text-[13px] leading-relaxed text-ink-2">
          {{ intro[0] }}<span class="font-medium text-hill">{{ t('map.introHl') }}</span>{{ intro[1] }}
        </p>

        <!-- View mode -->
        <fieldset class="mt-6">
          <legend class="label mb-2">{{ t('map.view') }}</legend>
          <div class="relative grid grid-cols-2 rounded-md border border-rule bg-card p-0.5 text-sm">
            <span class="absolute inset-y-0.5 left-0.5 w-[calc(50%-2px)] rounded-[5px] bg-ink transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]" :class="compare ? 'translate-x-0' : 'translate-x-full'" aria-hidden="true"></span>
            <button v-for="m in modes" :key="m.id" type="button" class="relative rounded-[5px] py-1.5 font-medium transition-colors duration-300" :class="compare === m.compare ? 'text-paper' : 'text-ink-2 hover:text-ink'" :aria-pressed="compare === m.compare" @click="compare = m.compare">
              {{ t(m.label) }}
            </button>
          </div>
        </fieldset>

        <!-- Scene -->
        <fieldset class="mt-6">
          <legend class="label mb-2">{{ t('map.acquisition') }}</legend>
          <div class="divide-y divide-rule overflow-hidden rounded-md border border-rule bg-card">
            <label v-for="s in scenes" :key="s.id" class="flex cursor-pointer items-center gap-3 px-3 py-2.5 transition-colors hover:bg-paper-2" :class="scene === s.id ? 'bg-paper-2' : ''">
              <input v-model="scene" type="radio" name="scene" :value="s.id" class="h-4 w-4 accent-ink" />
              <span class="flex-1">
                <span class="flex items-baseline justify-between">
                  <span class="num font-mono text-[13px] font-semibold text-ink">{{ date(s.iso) }}</span>
                  <span class="font-mono text-[11px] text-ink-3">{{ t('map.track', { n: n(s.track) }) }}</span>
                </span>
                <span class="block text-xs text-ink-2">{{ loc(s, 'label') }} · {{ loc(s, 'note') }}</span>
              </span>
            </label>
          </div>
        </fieldset>

        <!-- Layers -->
        <fieldset class="mt-6">
          <legend class="label mb-2">{{ t('map.layers') }}</legend>
          <div class="space-y-1">
            <label class="flex cursor-pointer items-center gap-3 rounded-md px-1 py-1.5 hover:bg-paper-2">
              <input v-model="layers.water" type="checkbox" class="h-4 w-4 accent-ink" />
              <span class="h-3.5 w-5 rounded-[2px] bg-water"></span>
              <span class="text-sm text-ink">{{ t('common.openWater') }} <span class="text-ink-3">· {{ t('common.bothSensors') }}</span></span>
            </label>
            <label class="flex cursor-pointer items-center gap-3 rounded-md px-1 py-1.5 hover:bg-paper-2">
              <input v-model="layers.hidden" type="checkbox" class="h-4 w-4 accent-ink" />
              <span class="hatch-missed h-3.5 w-5 rounded-[2px] border border-missed"></span>
              <span class="text-sm text-ink">{{ t('common.underTrees') }} <span class="text-ink-3">· {{ t('common.nisarOnly') }}</span></span>
            </label>
            <label class="flex cursor-pointer items-center gap-3 rounded-md px-1 py-1.5 hover:bg-paper-2">
              <input v-model="layers.hill" type="checkbox" class="h-4 w-4 accent-ink" />
              <span class="flex h-3.5 w-5 items-center justify-center"><span class="h-3 w-3 rounded-full border-2 border-card bg-hill ring-1 ring-hill"></span></span>
              <span class="text-sm text-ink">{{ t('map.hillRisk') }} <span class="text-ink-3">· {{ t('map.checkGround') }}</span></span>
            </label>
          </div>
        </fieldset>

        <!-- Basemap -->
        <fieldset class="mt-6">
          <legend class="label mb-2">{{ t('map.basemap') }}</legend>
          <div class="grid grid-cols-2 gap-2">
            <button v-for="b in basemaps" :key="b.id" type="button" class="flex items-center gap-2 rounded-md border px-3 py-2 text-sm transition-colors" :class="basemap === b.id ? 'border-ink bg-card font-medium text-ink' : 'border-rule text-ink-2 hover:border-ink/50'" :aria-pressed="basemap === b.id" @click="basemap = b.id">
              <component :is="b.icon" class="h-4 w-4" :stroke-width="1.75" />
              {{ t(b.label) }}
            </button>
          </div>
        </fieldset>

        <!-- Upazilas -->
        <div class="mt-7">
          <div class="mb-2 flex items-baseline justify-between">
            <h2 class="label">{{ t('map.listTitle') }}</h2>
            <button v-if="selected" type="button" class="text-xs text-ink-2 underline underline-offset-2 hover:text-ink" @click="clearSelection">{{ t('map.showAll') }}</button>
          </div>
          <ul class="divide-y divide-rule border-y border-rule">
            <li v-for="u in sortedUpazilas" :key="u.id">
              <button type="button" class="group flex w-full items-center gap-3 py-2.5 text-left" @click="select(u.id)">
                <span class="w-[7.5rem] shrink-0">
                  <span class="block text-sm font-medium transition-colors" :class="selected === u.id ? 'text-missed' : 'text-ink group-hover:text-missed'">{{ loc(u) }}</span>
                  <span class="block text-[11px] text-ink-3">{{ loc(u, 'district') }}</span>
                </span>
                <span class="h-1.5 flex-1">
                  <span class="block h-full rounded-full bg-missed" :style="{ width: `${(u.people / maxPeople) * 100}%` }"></span>
                </span>
                <span class="num w-14 text-right font-mono text-xs text-ink">{{ n(u.people) }}</span>
              </button>

              <transition name="expand">
              <div v-if="selected === u.id" class="mb-3 rounded-lg border border-rule bg-card p-3 shadow-[0_4px_16px_rgb(15_28_46/0.08)]">
                <dl class="grid grid-cols-2 gap-3">
                  <div><dt class="label !text-[10px]">{{ t('common.underTrees') }}</dt><dd class="num mt-0.5 font-mono text-base font-semibold text-ink">{{ fixed(u.hidden) }} {{ t('common.km2') }}</dd></div>
                  <div><dt class="label !text-[10px]">{{ t('common.openWater') }}</dt><dd class="num mt-0.5 font-mono text-base font-semibold text-ink">{{ fixed(u.both) }} {{ t('common.km2') }}</dd></div>
                  <div><dt class="label !text-[10px]">{{ t('common.people') }}</dt><dd class="num mt-0.5 font-mono text-base font-semibold text-ink">{{ n(u.people) }}</dd></div>
                  <div><dt class="label !text-[10px]">{{ t('map.hillSites') }}</dt><dd class="num mt-0.5 font-mono text-base font-semibold text-ink">{{ n(u.hill) }}</dd></div>
                </dl>
                <p class="mt-3 flex items-start gap-1.5 text-xs" :class="u.agree === 'both-dates' ? 'text-missed' : 'text-ink-2'">
                  <component :is="u.agree === 'both-dates' ? CircleCheck : CircleDashed" class="mt-px h-3.5 w-3.5 shrink-0" />
                  <span><span class="font-medium">{{ t('common.agree')[u.agree] }}</span><span class="block text-ink-3">{{ u.agree === 'both-dates' ? t('map.bothDates') : t('map.oneDate') }}</span></span>
                </p>
              </div>
              </transition>
            </li>
          </ul>
          <router-link to="/statistics" class="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-ink underline decoration-rule decoration-2 underline-offset-[6px] hover:decoration-ink">
            {{ t('map.allFigures') }} <ArrowRight class="h-4 w-4" />
          </router-link>
        </div>
      </div>
    </aside>

    <!-- Map -->
    <section class="relative flex-1" :aria-label="t('map.region')">
      <SwipeMap
        ref="mapRef"
        :scene="scene"
        :basemap="basemap"
        :compare="compare"
        :show-water="layers.water"
        :show-hidden="layers.hidden"
        :show-hill="layers.hill"
        :selected="selected"
        @select="select"
        @pointer="(p) => (pointer = p)"
        @view="(v) => (zoom = v.zoom)"
      />

      <div class="absolute right-3 top-1/2 z-20 flex -translate-y-1/2 flex-col overflow-hidden rounded-md border border-rule bg-card shadow-sm">
        <button type="button" class="flex h-9 w-9 items-center justify-center text-ink hover:bg-paper-2" :aria-label="t('map.zoomIn')" @click="mapRef?.zoomIn()"><Plus class="h-4 w-4" /></button>
        <button type="button" class="flex h-9 w-9 items-center justify-center border-t border-rule text-ink hover:bg-paper-2" :aria-label="t('map.zoomOut')" @click="mapRef?.zoomOut()"><Minus class="h-4 w-4" /></button>
        <button type="button" class="flex h-9 w-9 items-center justify-center border-t border-rule text-ink hover:bg-paper-2" :aria-label="t('map.reset')" @click="clearSelection"><Maximize class="h-4 w-4" /></button>
      </div>

      <p class="num pointer-events-none absolute bottom-16 left-1/2 z-20 -translate-x-1/2 whitespace-nowrap rounded-sm bg-card/90 px-2 py-0.5 font-mono text-[10px] text-ink-2 shadow-sm lg:bottom-2">
        <template v-if="pointer">{{ pointer.lat.toFixed(4) }}°N {{ pointer.lng.toFixed(4) }}°E · </template>z{{ zoom.toFixed(1) }}
      </p>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ChevronUp, Plus, Minus, Maximize, ArrowRight, Map as MapGlyph, Satellite, CircleCheck, CircleDashed } from 'lucide-vue-next'
import SwipeMap from '../components/SwipeMap.vue'
import { scenes, upazilas, viewport } from '../data/concept'
import { t, n, fixed, date, loc } from '../i18n'

const route = useRoute()
const mapRef = ref(null)
const panelOpen = ref(false)
const compare = ref(true)
const scene = ref('during1')
const basemap = ref('light')
const layers = reactive({ water: true, hidden: true, hill: false })
const selected = ref(null)
const pointer = ref(null)
const zoom = ref(viewport.zoom)

const modes = [
  { id: 'compare', label: 'map.compare', compare: true },
  { id: 'nisar', label: 'map.nisarOnly', compare: false },
]
const basemaps = [
  { id: 'light', label: 'map.basemapMap', icon: MapGlyph },
  { id: 'satellite', label: 'map.basemapSat', icon: Satellite },
]

const intro = computed(() => t('map.intro').split('{hl}'))
const sortedUpazilas = computed(() => [...upazilas].sort((a, b) => b.people - a.people))
const maxPeople = Math.max(...upazilas.map((u) => u.people))

function focus(id) {
  const u = upazilas.find((x) => x.id === id)
  if (!u) return
  selected.value = id
  mapRef.value?.flyTo(u.center, 11.2)
}

function select(id) {
  if (selected.value === id) clearSelection()
  else focus(id)
}

function clearSelection() {
  selected.value = null
  mapRef.value?.reset()
}

// Deep link from the figures table: /map?u=fatikchhari
onMounted(() => {
  if (typeof route.query.u === 'string') focus(route.query.u)
})
</script>

<style scoped>
.expand-enter-active,
.expand-leave-active {
  transition: opacity 0.3s ease, transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}
.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.98);
}
</style>
