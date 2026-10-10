<template>
  <div class="grid h-[calc(100dvh-65px)] w-full lg:grid-cols-[1fr_20rem]">
    <!-- Conversation -->
    <section class="relative flex min-h-0 flex-col lg:border-r lg:border-rule" :aria-label="t('ask.conversation')">
      <!-- Covers the whole column (so the input growing never resizes it) and fades out above the input -->
      <transition name="backdrop"><GradientBackdrop v-if="!messages.length" fade="radial" fade-bottom /></transition><!-- SOFFIT GRADIENT (trial) -->
      <transition name="bar">
        <div v-if="messages.length" class="relative flex items-center justify-between gap-4 border-b border-rule bg-paper/90 px-4 py-2.5 backdrop-blur-sm sm:px-8">
          <p class="label">{{ t('ask.conversation') }}</p>
          <button type="button" class="btn btn-line px-3 py-1.5" @click="newChat">
            <SquarePen class="h-4 w-4" :stroke-width="1.75" /> {{ t('ask.reset') }}
          </button>
        </div>
      </transition>
      <div class="relative min-h-0 flex-1">
      <div ref="scrollRef" class="thin-scroll relative h-full overflow-y-auto px-4 sm:px-8" data-lenis-prevent>
        <div class="mx-auto max-w-2xl py-8">
          <header v-if="!messages.length" v-reveal.stagger class="pb-6 pt-6 sm:pt-12">
            <p class="label">{{ t('ask.label') }}</p>
            <h1 class="mt-3 font-display text-4xl font-bold tracking-tight text-ink balance">{{ t('ask.title') }}</h1>
            <p class="mt-3 text-ink-2 pretty">{{ t('ask.lead') }}</p>
            <ul class="mt-8 divide-y divide-rule border-y border-rule">
              <li v-for="s in t('ask.suggestions')" :key="s">
                <button type="button" class="group flex w-full items-center justify-between gap-4 py-3 text-left text-[15px] text-ink transition-[color,padding] duration-300 hover:pl-2 hover:text-missed" @click="send(s)">
                  {{ s }}
                  <CornerDownLeft class="h-4 w-4 shrink-0 text-ink-3 transition-colors group-hover:text-missed" />
                </button>
              </li>
            </ul>
          </header>

          <TransitionGroup tag="ol" name="msg" class="space-y-8">
            <li v-for="m in messages" :key="m.id">
              <!-- User -->
              <div v-if="m.role === 'user'" class="flex justify-end">
                <p class="max-w-[85%] whitespace-pre-line rounded-lg bg-ink px-4 py-2.5 text-[15px] text-paper">{{ m.text }}</p>
              </div>

              <!-- Assistant -->
              <div v-else class="max-w-[92%]">
                <p class="label mb-2 flex items-center gap-1.5 !text-[10px]"><Sparkles class="h-3 w-3 text-water" />{{ t('ask.bot') }}</p>
                <div v-if="m.pending" class="space-y-2" :aria-label="t('ask.looking')">
                  <div class="shimmer h-3 w-4/5 rounded"></div>
                  <div class="shimmer h-3 w-3/5 rounded"></div>
                </div>
                <template v-else>
                  <p class="text-[15px] leading-relaxed text-ink pretty">{{ m.text }}</p>
                  <dl v-if="m.facts?.length" class="mt-4 overflow-hidden rounded-lg border border-rule bg-card">
                    <div v-for="f in m.facts" :key="f[0]" class="flex items-baseline justify-between gap-4 border-b border-rule px-3 py-2 last:border-b-0">
                      <dt class="text-sm text-ink-2">{{ f[0] }}</dt>
                      <dd class="num font-mono text-sm font-semibold text-ink">{{ f[1] }}</dd>
                    </div>
                  </dl>
                  <div class="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1">
                    <p v-if="m.source" class="font-mono text-[11px] text-ink-3">{{ t('common.source') }}: {{ m.source }}</p>
                    <router-link v-if="m.link" :to="m.link.to" class="group inline-flex items-center gap-1 text-sm font-medium text-ink underline decoration-rule decoration-2 underline-offset-4 hover:decoration-ink">
                      {{ m.link.label }} <ArrowRight class="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
                    </router-link>
                  </div>
                </template>
              </div>
            </li>
          </TransitionGroup>
        </div>
      </div>
      </div>

      <!-- Composer -->
      <div class="relative px-4 pb-4 pt-3 sm:px-8">
        <div v-if="messages.length" class="pointer-events-none absolute inset-x-0 -top-8 h-8 bg-linear-to-t from-paper to-transparent"></div>
        <PromptInput v-model="input" :placeholder="t('ask.placeholder')" :disabled="busy" @submit="send" />
        <p class="mx-auto mt-2.5 max-w-2xl text-center text-[11px] text-ink-3">{{ t('ask.footnote') }}</p>
      </div>
    </section>

    <!-- What it knows -->
    <aside class="hidden overflow-y-auto bg-paper-2/60 p-6 lg:block" :aria-label="t('ask.about')" data-lenis-prevent>
      <p class="label">{{ t('ask.canTitle') }}</p>
      <ul class="mt-3 space-y-2 text-sm text-ink-2">
        <li v-for="c in t('ask.can')" :key="c" class="flex gap-2"><Check class="mt-0.5 h-4 w-4 shrink-0 text-ok" />{{ c }}</li>
      </ul>
      <p class="label mt-8">{{ t('ask.wontTitle') }}</p>
      <ul class="mt-3 space-y-2 text-sm text-ink-2">
        <li v-for="w in t('ask.wont')" :key="w" class="flex gap-2"><X class="mt-0.5 h-4 w-4 shrink-0 text-missed" />{{ w }}</li>
      </ul>
      <p class="label mt-8">{{ t('ask.covered') }}</p>
      <p class="mt-3 text-sm leading-relaxed text-ink-2">{{ upazilas.map((u) => loc(u)).join(', ') }}</p>
    </aside>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { ArrowRight, CornerDownLeft, Check, X, SquarePen, Sparkles } from 'lucide-vue-next'
import PromptInput from '../components/PromptInput.vue'
import GradientBackdrop from '../components/GradientBackdrop.vue' // SOFFIT GRADIENT (trial)
import { answer } from '../data/assistant'
import { upazilas } from '../data/concept'
import { t, loc } from '../i18n'

const input = ref('')
const busy = ref(false)
const messages = ref([])
const scrollRef = ref(null)
let nextId = 0
let pendingTimer = 0

async function scrollDown() {
  await nextTick()
  scrollRef.value?.scrollTo({ top: scrollRef.value.scrollHeight, behavior: 'smooth' })
}

function send(text) {
  const q = text.trim()
  if (!q || busy.value) return
  input.value = ''
  busy.value = true
  messages.value.push({ id: nextId++, role: 'user', text: q })
  const pendingId = nextId++
  messages.value.push({ id: pendingId, role: 'assistant', pending: true })
  scrollDown()

  pendingTimer = setTimeout(() => {
    const i = messages.value.findIndex((m) => m.id === pendingId)
    if (i !== -1) messages.value.splice(i, 1, { id: pendingId, role: 'assistant', ...answer(q) })
    busy.value = false
    scrollDown()
  }, 650)
}

// Clear the conversation (and any answer still being looked up) and return to the welcome screen
function newChat() {
  clearTimeout(pendingTimer)
  busy.value = false
  messages.value = []
  input.value = ''
  scrollRef.value?.scrollTo({ top: 0 })
}
</script>

<style scoped>
.backdrop-leave-active {
  transition: opacity 0.6s ease;
}
.backdrop-leave-to {
  opacity: 0;
}
.bar-enter-active,
.bar-leave-active {
  transition: opacity 0.25s ease;
}
.bar-enter-from,
.bar-leave-to {
  opacity: 0;
}
.msg-enter-active {
  transition: opacity 0.4s ease, transform 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}
.msg-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
.shimmer {
  background: linear-gradient(90deg, var(--color-paper-3) 0%, var(--color-paper-2) 50%, var(--color-paper-3) 100%);
  background-size: 200% 100%;
  animation: shimmer 1.2s ease-in-out infinite;
}
@keyframes shimmer {
  to {
    background-position: -200% 0;
  }
}
</style>
