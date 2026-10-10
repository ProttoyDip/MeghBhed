<template>
  <div class="relative flex w-full flex-1 overflow-hidden">
    <GradientBackdrop fade="radial" /><!-- SOFFIT GRADIENT (trial) -->
    <section v-reveal.stagger class="relative mx-auto flex w-full max-w-3xl flex-1 flex-col justify-center px-4 py-24 sm:px-6">
      <p class="label">{{ t('notFound.label') }}</p>
      <h1 class="mt-4 font-display text-5xl font-extrabold tracking-tight text-ink balance">{{ t('notFound.title') }}</h1>
      <p class="mt-4 max-w-xl text-ink-2">{{ t('notFound.body') }}</p>
      <div class="mt-8 flex flex-wrap gap-3">
        <router-link to="/" class="btn btn-ink">{{ t('notFound.back') }}</router-link>
        <router-link to="/map" class="btn btn-line">{{ t('notFound.map') }}</router-link>
      </div>
    </section>
  </div>
</template>

<script setup>
import { t } from '../i18n'
import GradientBackdrop from '../components/GradientBackdrop.vue' // SOFFIT GRADIENT (trial)
</script>
