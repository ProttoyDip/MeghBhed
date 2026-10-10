<template>
  <div ref="rootRef" class="relative h-full w-full overflow-hidden bg-paper-2" :data-lenis-prevent="interactive || undefined">
    <!-- NISAR L-band (full, receives interaction) -->
    <!-- (MapLibre forces position: relative on its container, so position a wrapper instead) -->
    <div class="absolute inset-0">
      <div ref="lbandRef" class="h-full w-full"></div>
    </div>

    <!-- C-band (clipped to the left of the handle, follows the L-band camera) -->
    <div
      v-show="compare"
      class="pointer-events-none absolute inset-0"
      :style="{ clipPath: `inset(0 ${100 - split}% 0 0)` }"
    >
      <div ref="cbandRef" class="h-full w-full"></div>
    </div>

    <!-- Side captions -->
    <template v-if="compare">
      <div class="pointer-events-none absolute left-3 top-3 z-10 max-w-[45%]">
        <p class="rounded-md border border-water/40 bg-card/95 px-2 py-1 font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-water shadow-sm">
          C-band · OPERA DSWx-S1
        </p>
        <p v-if="showDates" class="mt-1 hidden font-mono text-[10px] text-ink-2 sm:block">Sentinel-1 · {{ date('2026-07-16') }}</p>
      </div>
      <div class="pointer-events-none absolute right-3 top-3 z-10 max-w-[45%] text-right">
        <p class="rounded-md border border-missed/40 bg-card/95 px-2 py-1 font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-missed shadow-sm">
          NISAR L-band · GCOV
        </p>
        <p v-if="showDates" class="mt-1 hidden font-mono text-[10px] text-ink-2 sm:block">{{ t('map.track', { n: n(sceneInfo.track) }) }} · {{ date(sceneInfo.iso) }}</p>
      </div>

      <!-- Swipe handle -->
      <div
        class="absolute inset-y-0 z-20 w-0"
        :style="{ left: `${split}%` }"
      >
        <div class="absolute inset-y-0 -left-px w-0.5 bg-ink"></div>
        <button
          type="button"
          role="slider"
          :aria-label="t('map.swipe')"
          :aria-valuenow="Math.round(split)"
          aria-valuemin="0"
          aria-valuemax="100"
          class="absolute top-1/2 -left-5 flex h-10 w-10 -translate-y-1/2 cursor-ew-resize touch-none items-center justify-center rounded-full border-2 border-ink bg-card text-ink shadow-md transition-transform hover:scale-105 active:scale-95"
          @pointerdown="startDrag"
          @keydown.left.prevent="split = Math.max(0, split - 4)"
          @keydown.right.prevent="split = Math.min(100, split + 4)"
        >
          <ArrowLeftRight class="h-4 w-4" :stroke-width="2.25" />
        </button>
      </div>
    </template>

    <!-- Tile failure notice -->
    <div v-if="tileError" class="absolute inset-x-3 bottom-10 z-10 rounded-md border border-hill/40 bg-hill-soft px-3 py-2 text-xs text-ink">
      {{ t('map.tileError') }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { Map as MlMap, Marker, AttributionControl, ScaleControl, setWorkerUrl } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
// MapLibre v6 looks for its worker next to its own module, which Vite moves
// when bundling. Point it at the worker file explicitly.
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import { ArrowLeftRight } from 'lucide-vue-next'
import { buildLayers, scenes, upazilas, viewport } from '../data/concept'
import { t, n, date, loc, lang } from '../i18n'
import { theme } from '../theme'

setWorkerUrl(workerUrl)

const props = defineProps({
  scene: { type: String, default: 'during1' },
  basemap: { type: String, default: 'light' }, // 'light' | 'satellite'
  compare: { type: Boolean, default: true },
  showWater: { type: Boolean, default: true },
  showHidden: { type: Boolean, default: true },
  showHill: { type: Boolean, default: false },
  selected: { type: String, default: null },
  interactive: { type: Boolean, default: true },
  showDates: { type: Boolean, default: true },
  showMarkers: { type: Boolean, default: true },
  initialSplit: { type: Number, default: 50 },
  initialView: { type: Object, default: () => viewport },
})
const emit = defineEmits(['select', 'pointer', 'view'])

const rootRef = ref(null)
const lbandRef = ref(null)
const cbandRef = ref(null)
const split = ref(props.initialSplit)
const tileError = ref(false)

const sceneInfo = computed(() => scenes.find((s) => s.id === props.scene) ?? scenes[1])

let lband = null
let cband = null
let resizeObs = null
const markers = []

// Overlay colours per theme (same values as the CSS tokens; MapLibre paints can't read CSS vars)
const PALETTES = {
  light: { bg: '#eef1f5', water: '#1f6fb2', waterLine: '#154e80', missed: '#c62f3b', hatchFill: 'rgba(198, 47, 59, 0.28)', hill: '#b45309', ring: '#fcfdfe' },
  dark: { bg: '#131d2a', water: '#4b97da', waterLine: '#9cc8ef', missed: '#e5545f', hatchFill: 'rgba(229, 84, 95, 0.30)', hill: '#e0913a', ring: '#0d1520' },
}
const colors = () => PALETTES[theme.value] ?? PALETTES.light

function baseStyle() {
  return {
    version: 8,
    sources: {
      light: {
        type: 'raster',
        tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}'],
        tileSize: 256,
        maxzoom: 16,
        attribution: 'Basemap © Esri, HERE, Garmin, © OpenStreetMap contributors',
      },
      dark: {
        type: 'raster',
        tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}'],
        tileSize: 256,
        maxzoom: 16,
        attribution: 'Basemap © Esri, HERE, Garmin, © OpenStreetMap contributors',
      },
      darkLabels: {
        type: 'raster',
        tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}'],
        tileSize: 256,
        maxzoom: 16,
      },
      lightLabels: {
        type: 'raster',
        tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}'],
        tileSize: 256,
        maxzoom: 16,
      },
      satellite: {
        type: 'raster',
        tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
        tileSize: 256,
        maxzoom: 18,
        attribution: 'Imagery © Esri, Maxar, Earthstar Geographics',
      },
      satelliteLabels: {
        type: 'raster',
        tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}'],
        tileSize: 256,
        maxzoom: 18,
      },
    },
    layers: [
      { id: 'bg', type: 'background', paint: { 'background-color': colors().bg } },
      { id: 'light', type: 'raster', source: 'light' },
      { id: 'dark', type: 'raster', source: 'dark', layout: { visibility: 'none' } },
      { id: 'satellite', type: 'raster', source: 'satellite', layout: { visibility: 'none' }, paint: { 'raster-saturation': -0.15 } },
    ],
  }
}

function hatchImage() {
  const size = 16
  const c = document.createElement('canvas')
  c.width = c.height = size
  const g = c.getContext('2d')
  g.fillStyle = colors().hatchFill
  g.fillRect(0, 0, size, size)
  g.strokeStyle = colors().missed
  g.lineWidth = 2.5
  g.beginPath()
  for (let o = -size; o <= size * 2; o += 6) {
    g.moveTo(o, 0)
    g.lineTo(o - size, size)
  }
  g.stroke()
  return g.getImageData(0, 0, size, size)
}

function addOverlay(map, { withHidden }) {
  const data = buildLayers(props.scene)
  map.addSource('water', { type: 'geojson', data: data.openWater })
  map.addSource('hill', { type: 'geojson', data: data.hill })
  const c = colors()
  map.addLayer({ id: 'water-fill', type: 'fill', source: 'water', paint: { 'fill-color': c.water, 'fill-opacity': 0.72 } })
  map.addLayer({ id: 'water-line', type: 'line', source: 'water', paint: { 'line-color': c.waterLine, 'line-width': 0.8, 'line-opacity': 0.8 } })

  if (withHidden) {
    map.addImage('hatch', hatchImage(), { pixelRatio: 2 })
    map.addSource('hidden', { type: 'geojson', data: data.hidden })
    map.addLayer({ id: 'hidden-fill', type: 'fill', source: 'hidden', paint: { 'fill-pattern': 'hatch' } })
    map.addLayer({ id: 'hidden-line', type: 'line', source: 'hidden', paint: { 'line-color': c.missed, 'line-width': 1.2 } })
  }

  map.addLayer({ id: 'lightLabels', type: 'raster', source: 'lightLabels', paint: { 'raster-opacity': 0.9 } })
  map.addLayer({ id: 'darkLabels', type: 'raster', source: 'darkLabels', layout: { visibility: 'none' }, paint: { 'raster-opacity': 0.9 } })
  map.addLayer({ id: 'satelliteLabels', type: 'raster', source: 'satelliteLabels', layout: { visibility: 'none' } })

  map.addLayer({
    id: 'hill',
    type: 'circle',
    source: 'hill',
    paint: {
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 7, 4, 12, 9],
      'circle-color': c.hill,
      'circle-stroke-color': c.ring,
      'circle-stroke-width': 2,
    },
  })
}

function setVis(map, id, on) {
  if (map?.getLayer(id)) map.setLayoutProperty(id, 'visibility', on ? 'visible' : 'none')
}

function applyVisibility() {
  // "Map" basemap follows the site theme; satellite is the same in both
  const base = props.basemap === 'satellite' ? 'satellite' : theme.value === 'dark' ? 'dark' : 'light'
  for (const map of [lband, cband]) {
    if (!map) continue
    for (const id of ['light', 'dark', 'satellite']) {
      setVis(map, id, base === id)
      setVis(map, `${id}Labels`, base === id)
    }
    setVis(map, 'water-fill', props.showWater)
    setVis(map, 'water-line', props.showWater)
    setVis(map, 'hill', props.showHill)
  }
  setVis(lband, 'hidden-fill', props.showHidden)
  setVis(lband, 'hidden-line', props.showHidden)
}

function applyColors() {
  const c = colors()
  for (const map of [lband, cband]) {
    if (!map?.getLayer('water-fill')) continue
    map.setPaintProperty('bg', 'background-color', c.bg)
    map.setPaintProperty('water-fill', 'fill-color', c.water)
    map.setPaintProperty('water-line', 'line-color', c.waterLine)
    map.setPaintProperty('hill', 'circle-color', c.hill)
    map.setPaintProperty('hill', 'circle-stroke-color', c.ring)
  }
  if (lband?.hasImage('hatch')) {
    lband.updateImage('hatch', hatchImage())
    lband.setPaintProperty('hidden-line', 'line-color', c.missed)
  }
}

function refreshData() {
  const data = buildLayers(props.scene)
  for (const map of [lband, cband]) {
    map?.getSource('water')?.setData(data.openWater)
    map?.getSource('hill')?.setData(data.hill)
  }
  lband?.getSource('hidden')?.setData(data.hidden)
}

function makeMarkerEl(u) {
  const el = document.createElement('button')
  el.type = 'button'
  el.className = 'mb-marker'
  el.dataset.id = u.id
  el.innerHTML = '<span class="mb-marker-dot"></span><span class="mb-marker-name"></span>'
  labelMarker(el, u)
  return el
}

function labelMarker(el, u) {
  el.setAttribute('aria-label', loc(u))
  el.querySelector('.mb-marker-name').textContent = loc(u)
}

function relabelMarkers() {
  for (const m of markers) {
    const el = m.getElement()
    const u = upazilas.find((x) => x.id === el.dataset.id)
    if (u) labelMarker(el, u)
  }
}

function addMarkers(map, clickable) {
  if (!props.showMarkers) return
  for (const u of upazilas) {
    const el = makeMarkerEl(u)
    if (clickable) el.addEventListener('click', (e) => { e.stopPropagation(); emit('select', u.id) })
    else el.tabIndex = -1
    markers.push(new Marker({ element: el, anchor: 'left', offset: [-6, 0] }).setLngLat(u.center).addTo(map))
  }
  highlightMarkers()
}

function highlightMarkers() {
  for (const m of markers) {
    m.getElement().classList.toggle('is-selected', m.getElement().dataset.id === props.selected)
  }
}

function startDrag(e) {
  const rect = rootRef.value.getBoundingClientRect()
  const move = (ev) => {
    split.value = Math.max(0, Math.min(100, ((ev.clientX - rect.left) / rect.width) * 100))
  }
  const up = () => {
    window.removeEventListener('pointermove', move)
    window.removeEventListener('pointerup', up)
  }
  window.addEventListener('pointermove', move)
  window.addEventListener('pointerup', up)
  move(e)
}

onMounted(() => {
  const common = {
    style: baseStyle(),
    center: props.initialView.center,
    zoom: props.initialView.zoom,
    attributionControl: false,
    maxZoom: 15,
    minZoom: 6,
  }

  lband = new MlMap({ ...common, container: lbandRef.value, scrollZoom: props.interactive, dragRotate: false, pitchWithRotate: false })
  lband.touchZoomRotate.disableRotation()
  lband.addControl(new AttributionControl({ compact: true, customAttribution: 'Flood overlay: illustrative concept data' }), 'bottom-right')
  if (props.interactive) lband.addControl(new ScaleControl({ unit: 'metric' }), 'bottom-left')

  cband = new MlMap({ ...common, container: cbandRef.value, interactive: false })

  lband.on('load', () => {
    // Start the compact attribution collapsed; the ⓘ button still opens it
    lband.getContainer().querySelector('.maplibregl-ctrl-attrib')?.classList.remove('maplibregl-compact-show')
    addOverlay(lband, { withHidden: true })
    addMarkers(lband, true)
    applyVisibility()
  })
  cband.on('load', () => {
    addOverlay(cband, { withHidden: false })
    addMarkers(cband, false)
    applyVisibility()
  })

  const sync = () => {
    cband.jumpTo({ center: lband.getCenter(), zoom: lband.getZoom(), bearing: lband.getBearing(), pitch: lband.getPitch() })
  }
  lband.on('move', sync)
  lband.on('moveend', () => emit('view', { zoom: lband.getZoom(), center: lband.getCenter() }))
  lband.on('mousemove', (e) => emit('pointer', e.lngLat))
  lband.on('error', (e) => {
    if (e?.sourceId === 'light' || e?.sourceId === 'satellite') tileError.value = true
  })

  resizeObs = new ResizeObserver(() => {
    lband?.resize()
    cband?.resize()
  })
  resizeObs.observe(rootRef.value)
})

onBeforeUnmount(() => {
  resizeObs?.disconnect()
  markers.length = 0
  lband?.remove()
  cband?.remove()
})

watch(() => props.scene, refreshData)
watch(() => [props.basemap, props.showWater, props.showHidden, props.showHill], applyVisibility)
watch(() => props.selected, highlightMarkers)
watch(theme, () => {
  applyColors()
  applyVisibility()
})
watch(lang, relabelMarkers)
watch(() => props.compare, (on) => {
  if (on) requestAnimationFrame(() => cband?.resize())
})

defineExpose({
  zoomIn: () => lband?.zoomIn(),
  zoomOut: () => lband?.zoomOut(),
  flyTo: (center, zoom = 11) => {
    // In compare mode, land the place in the middle of the NISAR (right) side
    const shift = props.compare ? Math.round((rootRef.value.clientWidth * split.value) / 200) : 0
    lband?.flyTo({ center, zoom, speed: 1.4, offset: [shift, 0], essential: true })
  },
  reset: () => lband?.flyTo({ center: props.initialView.center, zoom: props.initialView.zoom, essential: true }),
})
</script>

<style>
.mb-marker {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  background: none;
  border: 0;
  padding: 0;
}
.mb-marker-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: var(--color-card);
  border: 2px solid var(--color-ink);
  flex: none;
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), background-color 0.2s ease;
}
.mb-marker-name {
  font-family: "Geist Mono Variable", "Noto Sans Bengali", monospace;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-ink);
  background: color-mix(in oklab, var(--color-card) 92%, transparent);
  padding: 1px 5px;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgb(15 28 46 / 0.2);
  white-space: nowrap;
  transition: background-color 0.2s ease, color 0.2s ease;
}
.mb-marker:hover .mb-marker-dot,
.mb-marker.is-selected .mb-marker-dot {
  transform: scale(1.3);
  background: var(--color-missed);
  border-color: var(--color-card);
}
.mb-marker.is-selected .mb-marker-name {
  background: var(--color-ink);
  color: var(--color-paper);
}
</style>
