<template>
  <svg viewBox="0 0 360 230" role="img" :aria-label="band === 'l' ? t('home.diagram.ariaL') : t('home.diagram.ariaC')" class="block" :class="band === 'l' ? 'text-missed' : 'text-ink-2'">
    <defs>
      <marker :id="`arrow-${band}`" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M0 0 L10 5 L0 10 z" fill="currentColor" />
      </marker>
      <pattern :id="`water-${band}`" width="10" height="5" patternUnits="userSpaceOnUse">
        <path d="M0 3 q2.5 -2 5 0 t5 0" fill="none" class="stroke-water" stroke-width="0.8" opacity="0.6" />
      </pattern>
    </defs>

    <!-- Satellite -->
    <g transform="translate(26 18)">
      <rect x="10" y="6" width="16" height="12" rx="1.5" class="fill-ink" />
      <rect x="-6" y="9" width="14" height="6" fill="none" class="stroke-ink" stroke-width="1.4" />
      <rect x="28" y="9" width="14" height="6" fill="none" class="stroke-ink" stroke-width="1.4" />
      <path d="M-6 12 h14 M28 12 h14" class="stroke-ink" stroke-width="0.8" />
      <text x="18" y="34" text-anchor="middle" class="dg-label fill-ink-2">{{ band === 'l' ? 'NISAR' : 'Sentinel-1' }}</text>
    </g>

    <!-- Ground and water -->
    <rect x="0" y="198" width="360" height="32" class="fill-paper-3" />
    <rect x="150" y="196" width="210" height="16" class="fill-water-soft" />
    <rect x="150" y="196" width="210" height="16" :fill="`url(#water-${band})`" />
    <line x1="150" y1="196" x2="360" y2="196" class="stroke-water" stroke-width="1.2" />
    <text x="352" y="224" text-anchor="end" class="dg-label fill-ink-2">{{ t('home.diagram.floodwater') }}</text>

    <!-- Tree -->
    <rect x="236" y="118" width="9" height="80" fill="#6b5a43" />
    <g fill="#6f8a5a">
      <circle cx="240" cy="98" r="36" opacity="0.92" />
      <circle cx="206" cy="114" r="24" opacity="0.9" />
      <circle cx="274" cy="114" r="24" opacity="0.9" />
      <circle cx="300" cy="140" r="18" opacity="0.85" />
    </g>
    <rect x="312" y="158" width="6" height="40" fill="#6b5a43" />

    <template v-if="band === 'c'">
      <!-- Short wave stops in the canopy -->
      <path d="M62 44 L200 96" stroke="currentColor" stroke-width="2" stroke-dasharray="3 3" fill="none" :marker-end="`url(#arrow-${band})`" class="dg-beam" />
      <g stroke="currentColor" stroke-width="1.6" fill="none">
        <path d="M206 100 l-14 -14" :marker-end="`url(#arrow-${band})`" />
        <path d="M210 100 l4 -20" :marker-end="`url(#arrow-${band})`" />
        <path d="M210 104 l20 -6" :marker-end="`url(#arrow-${band})`" />
        <path d="M206 106 l-18 6" :marker-end="`url(#arrow-${band})`" />
      </g>
      <text x="112" y="122" class="dg-note fill-ink-2">{{ t('home.diagram.scattered') }}</text>
      <g transform="translate(196 176)">
        <rect x="-4" y="-12" width="96" height="18" rx="2" class="fill-card stroke-rule" />
        <text x="44" y="1" text-anchor="middle" class="dg-label fill-ink-2">{{ t('home.diagram.notDetected') }}</text>
      </g>
    </template>

    <template v-else>
      <!-- Long wave: canopy → water → trunk → back to satellite -->
      <path d="M62 44 L222 196" stroke="currentColor" stroke-width="2.2" stroke-dasharray="12 6" fill="none" class="dg-beam" />
      <path d="M222 196 L236 182" stroke="currentColor" stroke-width="2.2" fill="none" />
      <path d="M236 180 L74 52" stroke="currentColor" stroke-width="2.2" stroke-dasharray="12 6" fill="none" :marker-end="`url(#arrow-${band})`" class="dg-beam" />
      <circle cx="222" cy="196" r="3.5" fill="currentColor" />
      <circle cx="236" cy="182" r="3.5" fill="currentColor" />
      <text x="92" y="140" class="dg-note fill-ink-2">{{ t('home.diagram.passes') }}</text>
      <g transform="translate(250 178)">
        <rect x="-2" y="-12" width="96" height="18" rx="2" class="fill-card" stroke="currentColor" />
        <text x="46" y="1" text-anchor="middle" class="dg-label" fill="currentColor">{{ t('home.diagram.bounce') }}</text>
      </g>
    </template>
  </svg>
</template>

<script setup>
import { t } from '../i18n'

defineProps({ band: { type: String, required: true } })
</script>

<style scoped>
.dg-label {
  font: 600 10px "Geist Mono Variable", "Noto Sans Bengali", monospace;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.dg-note {
  font: italic 500 12px "Geist Variable", "Noto Sans Bengali", sans-serif;
}
/* The dashed beams travel along their path (each path is drawn in travel direction) */
.dg-beam {
  animation: dg-flow 1.6s linear infinite;
}
@keyframes dg-flow {
  to {
    stroke-dashoffset: -36;
  }
}
@media (prefers-reduced-motion: reduce) {
  .dg-beam {
    animation: none;
  }
}
</style>
