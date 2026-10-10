<template>
  <div class="relative flex min-h-dvh flex-col">
    <a href="#main" class="sr-only z-50 rounded bg-ink px-3 py-2 text-paper focus:not-sr-only focus:fixed focus:left-3 focus:top-3">{{ t('nav.skip') }}</a>

    <header class="sticky top-0 z-40 border-b border-rule bg-paper/90 backdrop-blur-md">
      <div class="mx-auto flex h-16 max-w-[88rem] items-center justify-between gap-4 px-4 sm:px-6">
        <router-link to="/" class="group flex items-baseline gap-2.5" aria-label="MeghBhed">
          <span class="font-bangla text-[1.6rem] font-extrabold leading-none text-ink">মেঘভেদ</span>
          <span class="font-display text-lg font-semibold tracking-tight text-ink-2 transition-colors group-hover:text-ink">MeghBhed</span>
        </router-link>

        <nav :aria-label="t('nav.menu')" class="hidden items-center gap-1 lg:flex">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="relative whitespace-nowrap px-3 py-2 text-sm font-medium text-ink-2 transition-colors after:absolute after:inset-x-3 after:-bottom-[13px] after:h-[3px] after:origin-left after:scale-x-0 after:bg-missed after:transition-transform after:duration-300 hover:text-ink hover:after:scale-x-100"
            exact-active-class="!text-ink after:!scale-x-100"
          >
            {{ t(item.key) }}
          </router-link>
        </nav>

        <div class="flex items-center gap-1.5">
          <span class="mr-1 hidden items-center gap-1.5 border border-hill/40 bg-hill-soft px-2 py-1 font-mono text-[10px] font-semibold uppercase tracking-[0.1em] text-hill 2xl:inline-flex">
            {{ t('nav.concept') }}
          </span>

          <!-- Language -->
          <button
            type="button"
            class="flex h-9 min-w-9 items-center justify-center gap-1.5 rounded-md border border-rule px-2.5 text-[13px] font-semibold text-ink transition-colors hover:border-ink/40 hover:bg-paper-2"
            :aria-label="t('nav.langLabel')"
            :title="t('nav.langLabel')"
            @click="toggleLang"
          >
            <Languages class="h-4 w-4 text-ink-2" :stroke-width="1.75" />
            <span>{{ t('nav.langButton') }}</span>
          </button>

          <!-- Theme -->
          <button
            type="button"
            class="relative flex h-9 w-9 items-center justify-center overflow-hidden rounded-md border border-rule text-ink transition-colors hover:border-ink/40 hover:bg-paper-2"
            :aria-label="theme === 'dark' ? t('nav.toLight') : t('nav.toDark')"
            :title="theme === 'dark' ? t('nav.toLight') : t('nav.toDark')"
            @click="toggleTheme"
          >
            <Sun class="absolute h-[18px] w-[18px] transition-all duration-500" :class="theme === 'dark' ? 'rotate-0 scale-100 opacity-100' : '-rotate-90 scale-50 opacity-0'" :stroke-width="1.75" />
            <Moon class="absolute h-[18px] w-[18px] transition-all duration-500" :class="theme === 'dark' ? 'rotate-90 scale-50 opacity-0' : 'rotate-0 scale-100 opacity-100'" :stroke-width="1.75" />
          </button>

          <a
            href="https://github.com/ProttoyDip/MeghBhed"
            target="_blank"
            rel="noopener"
            class="hidden h-9 w-9 items-center justify-center rounded-md text-ink-2 transition-colors hover:bg-paper-2 hover:text-ink sm:flex"
            :aria-label="t('nav.github')"
          >
            <Github class="h-[18px] w-[18px]" :stroke-width="1.75" />
          </a>
          <button
            type="button"
            class="flex h-9 w-9 items-center justify-center rounded-md border border-rule text-ink lg:hidden"
            :aria-expanded="menuOpen"
            aria-controls="mobile-nav"
            :aria-label="t('nav.menu')"
            @click="menuOpen = !menuOpen"
          >
            <X v-if="menuOpen" class="h-5 w-5" />
            <Menu v-else class="h-5 w-5" />
          </button>
        </div>
      </div>

      <transition name="page">
        <nav v-if="menuOpen" id="mobile-nav" :aria-label="t('nav.menu')" class="border-t border-rule bg-paper px-4 pb-4 pt-2 lg:hidden">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="flex items-center justify-between border-b border-rule/60 py-3 text-base font-medium text-ink-2"
            exact-active-class="!text-ink"
            @click="menuOpen = false"
          >
            {{ t(item.key) }}
            <ArrowRight class="h-4 w-4 text-ink-3" />
          </router-link>
          <p class="mt-3 font-mono text-[10px] uppercase tracking-[0.1em] text-hill">{{ t('nav.concept') }}</p>
        </nav>
      </transition>
    </header>

    <main id="main" class="relative z-10 flex flex-1 flex-col">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <footer v-if="!$route.meta.fullBleed" class="relative z-10 border-t border-rule bg-paper-2">
      <div v-reveal.stagger class="mx-auto grid max-w-[88rem] gap-10 px-4 py-12 sm:px-6 md:grid-cols-[1.4fr_1fr_1fr]">
        <div>
          <p class="font-bangla text-2xl font-extrabold text-ink">মেঘভেদ</p>
          <p class="mt-2 max-w-sm text-sm leading-relaxed text-ink-2">{{ t('footer.about') }}</p>
        </div>
        <div>
          <p class="label mb-3">{{ t('footer.project') }}</p>
          <ul class="space-y-2 text-sm">
            <li><a class="text-ink-2 underline-offset-4 hover:text-ink hover:underline" :href="`${repo}/blob/main/docs/METHOD.md`" target="_blank" rel="noopener">{{ t('footer.method') }}</a></li>
            <li><a class="text-ink-2 underline-offset-4 hover:text-ink hover:underline" :href="`${repo}/blob/main/docs/DATA.md`" target="_blank" rel="noopener">{{ t('footer.data') }}</a></li>
            <li><a class="text-ink-2 underline-offset-4 hover:text-ink hover:underline" :href="repo" target="_blank" rel="noopener">{{ t('footer.code') }}</a></li>
          </ul>
        </div>
        <div>
          <p class="label mb-3">{{ t('footer.context') }}</p>
          <ul class="space-y-2 text-sm">
            <li><a class="text-ink-2 underline-offset-4 hover:text-ink hover:underline" href="https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/" target="_blank" rel="noopener">{{ t('footer.challenge') }}</a></li>
            <li><a class="text-ink-2 underline-offset-4 hover:text-ink hover:underline" href="https://nisar-docs.asf.alaska.edu/" target="_blank" rel="noopener">{{ t('footer.nisarDocs') }}</a></li>
            <li><a class="text-ink-2 underline-offset-4 hover:text-ink hover:underline" :href="`${repo}/blob/main/LICENSE`" target="_blank" rel="noopener">{{ t('footer.licence') }}</a></li>
          </ul>
        </div>
      </div>
      <div class="border-t border-rule">
        <p class="mx-auto max-w-[88rem] px-4 py-4 font-mono text-[11px] text-ink-3 sm:px-6">{{ t('footer.disclaimer') }}</p>
      </div>
    </footer>

    <CursorFollower />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Github, Menu, X, ArrowRight, Languages, Sun, Moon } from 'lucide-vue-next'
import CursorFollower from './components/CursorFollower.vue'
import { t, lang, toggleLang } from './i18n'
import { theme, toggleTheme } from './theme'

const repo = 'https://github.com/ProttoyDip/MeghBhed'
const menuOpen = ref(false)
const route = useRoute()
watch(() => route.path, () => (menuOpen.value = false))

const navItems = [
  { key: 'nav.overview', path: '/' },
  { key: 'nav.map', path: '/map' },
  { key: 'nav.figures', path: '/statistics' },
  { key: 'nav.ask', path: '/assistant' },
]
</script>
