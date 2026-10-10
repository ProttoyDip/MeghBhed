<template>
  <!--
    Vue port of the "ai-chat-input" prompt (originally React/shadcn).
    Kept: spring expand, auto-growing textarea with edge fades, morphing
    mic / send / stop button, live voice waveform with speech-to-text.
    Dropped: model + effort pickers and image attachments — MeghBhed has no
    model choice and can't read images, so showing them would mislead.
  -->
  <div
    ref="rootRef"
    class="relative mx-auto flex w-full flex-col"
    :style="{ maxWidth: expanded ? '42rem' : '30rem', transition: smooth ? 'max-width 0.15s ease-out' : `max-width 0.4s ${SPRING}` }"
    @focusout="onBlur"
  >
    <div
      class="relative z-10 w-full border bg-card shadow-[0_1px_2px_rgb(15_28_46/0.06),0_8px_24px_rgb(15_28_46/0.08)] transition-[border-color,box-shadow] duration-200"
      :class="[expanded ? 'cursor-text border-ink/25 focus-within:border-ink/45 focus-within:shadow-[0_0_0_4px_color-mix(in_oklab,var(--color-water)_14%,transparent),0_8px_24px_rgb(15_28_46/0.10)]' : 'cursor-pointer border-rule hover:border-ink/30', recording ? '!border-missed/50' : '']"
      :style="{
        borderRadius: '24px',
        height: `${expanded ? containerHeight : 52}px`,
        transition: `height ${smooth ? '0.15s ease-out' : `0.4s ${SPRING}`}, border-color 0.2s, box-shadow 0.2s`,
        overflow: expanded ? 'visible' : 'hidden',
      }"
      @mousedown="onCardMouseDown"
    >
      <!-- Text box -->
      <textarea
        ref="textareaRef"
        :value="modelValue"
        :placeholder="placeholder"
        :aria-label="t('ask.input.label')"
        :disabled="disabled || recording"
        maxlength="400"
        rows="1"
        class="thin-scroll absolute inset-x-0 top-0 z-[1] w-full resize-none bg-transparent py-3.5 pl-5 pr-14 text-[15px] leading-[22px] text-ink outline-none placeholder:text-ink-3 focus-visible:outline-none"
        :class="[
          expanded ? 'translate-y-0 scale-100 opacity-100' : 'pointer-events-none -translate-y-1 scale-95 opacity-0',
          scrolling ? 'overflow-y-auto' : 'overflow-y-hidden',
        ]"
        :style="{ transition: smooth ? 'height 0.15s ease-out' : `opacity 0.3s ease-out, transform 0.3s ease-out, height 0.4s ${SPRING}` }"
        data-lenis-prevent
        @input="onInput"
        @scroll="updateFades"
        @keydown="onKeydown"
      ></textarea>

      <!-- Scroll fades -->
      <div ref="topFadeRef" class="pointer-events-none absolute left-5 right-14 top-0 z-[2] h-7 rounded-t-3xl bg-gradient-to-b from-card to-transparent opacity-0"></div>
      <div
        ref="bottomFadeRef"
        class="pointer-events-none absolute left-5 right-14 z-[2] h-7 bg-gradient-to-t from-card to-transparent opacity-0"
        :style="{ top: `${textareaHeight - 28}px`, transition: smooth ? 'top 0.15s ease-out' : `top 0.4s ${SPRING}` }"
      ></div>

      <!-- Collapsed pill label -->
      <button
        type="button"
        class="absolute inset-x-0 top-0 z-[1] flex h-[52px] items-center gap-2.5 pl-5 pr-14 text-left text-[15px] text-ink-3 outline-none"
        :class="expanded ? 'pointer-events-none translate-y-1 scale-105 opacity-0' : 'translate-y-0 scale-100 opacity-100'"
        :style="{ transition: `all 0.4s ${SPRING}` }"
        :tabindex="expanded ? -1 : 0"
        :aria-label="placeholder"
        @click="expand"
      >
        <Sparkles class="h-4 w-4 shrink-0 text-water" :stroke-width="1.75" />
        <span class="truncate">{{ placeholder }}</span>
      </button>

      <!-- Bottom toolbar -->
      <div
        class="absolute bottom-2 left-3 right-14 z-[10] flex items-center gap-1 transition-all duration-300"
        :class="expanded && !recording ? 'pointer-events-auto translate-y-0 opacity-100 blur-0' : 'pointer-events-none translate-y-2 opacity-0 blur-sm'"
        :style="{ transitionTimingFunction: SPRING }"
      >
        <button
          v-if="speechSupported"
          type="button"
          class="group flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold text-ink-2 transition-colors hover:bg-paper-2 hover:text-ink"
          :aria-label="t('ask.input.voiceLangToggle')"
          :title="t('ask.input.voiceLangToggle')"
          @mousedown.prevent
          @click.stop="voiceLang = voiceLang === 'bn' ? 'en' : 'bn'"
        >
          <Mic class="h-3.5 w-3.5 opacity-70 group-hover:opacity-100" :stroke-width="2" />
          <span class="relative inline-grid overflow-hidden">
            <transition name="morph" mode="out-in">
              <span :key="voiceLang" class="whitespace-nowrap">{{ t('ask.input.voiceLang', { lang: voiceLang === 'bn' ? 'বাংলা' : 'English' }) }}</span>
            </transition>
          </span>
        </button>
        <span class="ml-auto hidden truncate pr-1 font-mono text-[10px] text-ink-3 sm:block">{{ t('ask.input.hint') }}</span>
      </div>

      <!-- Voice waveform -->
      <div
        class="absolute bottom-2 right-14 z-[10] flex h-8 items-center justify-end gap-[3px] transition-all duration-500"
        :class="recording ? 'w-24 translate-x-0 opacity-100' : 'pointer-events-none w-0 translate-x-4 opacity-0'"
        :style="{ transitionTimingFunction: SPRING }"
        aria-hidden="true"
      >
        <span class="mr-2 whitespace-nowrap font-mono text-[10px] font-semibold uppercase tracking-[0.1em] text-missed">{{ t('ask.input.listening') }}</span>
        <span v-for="(v, i) in audio" :key="i" class="w-1 rounded-full bg-missed transition-[height] duration-75 ease-out" :style="{ height: `${Math.max(4, v * 24)}px` }"></span>
      </div>

      <!-- Send / mic / stop -->
      <button
        type="button"
        class="absolute bottom-2 right-2 z-[10] flex h-9 w-9 items-center justify-center rounded-full transition-all duration-300 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-water disabled:opacity-40"
        :class="recording ? 'bg-missed text-card' : 'bg-ink text-paper hover:opacity-90 active:scale-95'"
        :disabled="disabled || (!hasValue && !recording && !speechSupported)"
        :aria-label="showStop ? t('ask.input.stop') : showMic ? t('ask.input.speak') : t('ask.input.send')"
        @mousedown.prevent.stop
        @click="onAction"
      >
        <span class="relative flex h-full w-full items-center justify-center">
          <span class="morph-icon" :class="showArrow ? 'is-on' : 'is-off-cw'"><ArrowUp class="h-4 w-4" :stroke-width="2.25" /></span>
          <span class="morph-icon" :class="showMic ? 'is-on' : 'is-off-ccw'"><Mic class="h-4 w-4" :stroke-width="2" /></span>
          <span class="morph-icon" :class="showStop ? 'is-on' : 'is-off-cw'"><Square class="h-3 w-3 fill-current" :stroke-width="0" /></span>
        </span>
      </button>
    </div>

    <!-- Voice errors -->
    <transition name="morph">
      <p v-if="voiceError" role="alert" class="mt-2 px-4 text-center text-xs text-missed">{{ voiceError }}</p>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import { ArrowUp, Mic, Square, Sparkles } from 'lucide-vue-next'
import { t, lang } from '../i18n'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'submit'])

const SPRING = 'cubic-bezier(0.175, 0.885, 0.32, 1.275)'
const MIN_TEXT = 64
const MAX_TEXT = 160

const rootRef = ref(null)
const textareaRef = ref(null)
const topFadeRef = ref(null)
const bottomFadeRef = ref(null)

const expanded = ref(false)
const smooth = ref(false) // quick, non-springy resize while typing
const textareaHeight = ref(MIN_TEXT)
const scrolling = ref(false)
const containerHeight = computed(() => Math.max(112, textareaHeight.value + 48))

const hasValue = computed(() => props.modelValue.trim() !== '')

// ---- voice ------------------------------------------------------------------
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
const speechSupported = !!SpeechRecognition && !!navigator.mediaDevices?.getUserMedia
const voiceLang = ref(lang.value)
watch(lang, (l) => (voiceLang.value = l))

const recording = ref(false)
const audio = ref([0, 0, 0, 0, 0])
const voiceError = ref('')
let stream = null
let audioCtx = null
let raf = 0
let recognition = null

const showArrow = computed(() => (hasValue.value || !speechSupported) && !recording.value)
const showStop = computed(() => recording.value)
const showMic = computed(() => speechSupported && !hasValue.value && !recording.value)

function stopRecording() {
  recognition?.stop()
  recognition = null
  cancelAnimationFrame(raf)
  stream?.getTracks().forEach((tr) => tr.stop())
  stream = null
  audioCtx?.close()
  audioCtx = null
  recording.value = false
  audio.value = [0, 0, 0, 0, 0]
}

async function startRecording() {
  voiceError.value = ''
  smooth.value = false
  expanded.value = true
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  } catch {
    voiceError.value = t('ask.input.micBlocked')
    return
  }
  recording.value = true

  // Waveform from the live mic level
  audioCtx = new (window.AudioContext || window.webkitAudioContext)()
  const analyser = audioCtx.createAnalyser()
  analyser.fftSize = 64
  audioCtx.createMediaStreamSource(stream).connect(analyser)
  const data = new Uint8Array(analyser.frequencyBinCount)
  const step = Math.floor(data.length / 5)
  const draw = () => {
    analyser.getByteFrequencyData(data)
    audio.value = Array.from({ length: 5 }, (_, i) => {
      let sum = 0
      for (let j = 0; j < step; j++) sum += data[i * step + j]
      return sum / step / 255
    })
    raf = requestAnimationFrame(draw)
  }
  draw()

  // Speech to text, in Bangla or English
  recognition = new SpeechRecognition()
  recognition.lang = voiceLang.value === 'bn' ? 'bn-BD' : 'en-US'
  recognition.continuous = true
  recognition.interimResults = true
  let baseline = props.modelValue
  let heard = false
  recognition.onresult = (event) => {
    let interim = ''
    let final = ''
    for (let i = event.resultIndex; i < event.results.length; i++) {
      if (event.results[i].isFinal) final += event.results[i][0].transcript
      else interim += event.results[i][0].transcript
    }
    if (final) baseline += (baseline ? ' ' : '') + final
    heard = true
    setValue((baseline + (interim ? ` ${interim}` : '')).trim())
  }
  recognition.onerror = (e) => {
    if (e.error === 'not-allowed' || e.error === 'service-not-allowed') voiceError.value = t('ask.input.micBlocked')
    else if (e.error === 'no-speech') voiceError.value = t('ask.input.noSpeech')
    stopRecording()
  }
  recognition.onend = () => {
    if (!heard && !voiceError.value) voiceError.value = t('ask.input.noSpeech')
    stopRecording()
    nextTick(() => textareaRef.value?.focus())
  }
  recognition.start()
}

// ---- text box ---------------------------------------------------------------
function setValue(v) {
  smooth.value = true
  emit('update:modelValue', v)
}

function onInput(e) {
  voiceError.value = ''
  setValue(e.target.value)
}

function expand() {
  smooth.value = false
  expanded.value = true
}

function collapseIfEmpty() {
  if (hasValue.value || recording.value) return
  smooth.value = false
  expanded.value = false
}

function submit() {
  if (!hasValue.value || props.disabled) return
  emit('submit', props.modelValue.trim())
  smooth.value = false
  emit('update:modelValue', '')
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    submit()
  } else if (e.key === 'Escape' && !hasValue.value) {
    collapseIfEmpty()
    textareaRef.value?.blur()
  }
}

function onAction() {
  if (recording.value) stopRecording()
  else if (hasValue.value) submit()
  else if (speechSupported) startRecording()
}

function onCardMouseDown(e) {
  if (expanded.value && e.target !== textareaRef.value && !recording.value) {
    e.preventDefault()
    textareaRef.value?.focus()
  }
}

function onBlur(e) {
  if (rootRef.value?.contains(e.relatedTarget)) return
  collapseIfEmpty()
}

function updateFades() {
  const el = textareaRef.value
  if (!el) return
  const { scrollTop, scrollHeight, clientHeight } = el
  if (topFadeRef.value) topFadeRef.value.style.opacity = String(Math.min(scrollTop / 20, 1))
  if (bottomFadeRef.value) bottomFadeRef.value.style.opacity = String(Math.min(Math.max(scrollHeight - clientHeight - scrollTop - 16, 0) / 10, 1))
}

// Grow the textarea with its content (measured without animating from 0)
async function resize() {
  await nextTick()
  const el = textareaRef.value
  if (!el) return
  const prev = el.style.height
  el.style.transition = 'none'
  el.style.height = '0px'
  const sh = el.scrollHeight
  el.style.height = prev
  void el.offsetHeight
  el.style.transition = ''
  const h = Math.max(MIN_TEXT, Math.min(sh, MAX_TEXT))
  el.style.height = `${h}px`
  textareaHeight.value = h
  scrolling.value = sh > MAX_TEXT
  if (recording.value) el.scrollTop = el.scrollHeight
  setTimeout(updateFades, 0)
}

watch(() => props.modelValue, (v) => {
  if (v.trim() && !expanded.value) expand()
  resize()
})

watch(expanded, (on) => {
  resize()
  if (on && !recording.value) {
    setTimeout(() => {
      const el = textareaRef.value
      if (!el) return
      el.focus()
      el.setSelectionRange(el.value.length, el.value.length)
    }, 50)
  }
})

onBeforeUnmount(stopRecording)

defineExpose({ focus: expand })
</script>

<style scoped>
.morph-icon {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.3s, transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), filter 0.3s;
}
.morph-icon.is-on {
  opacity: 1;
  transform: scale(1) rotate(0);
  filter: blur(0);
}
.morph-icon.is-off-cw,
.morph-icon.is-off-ccw {
  opacity: 0;
  filter: blur(1px);
  pointer-events: none;
}
.morph-icon.is-off-cw {
  transform: scale(0.5) rotate(45deg);
}
.morph-icon.is-off-ccw {
  transform: scale(0.5) rotate(-45deg);
}

.morph-enter-active,
.morph-leave-active {
  transition: opacity 0.2s ease, transform 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.morph-enter-from {
  opacity: 0;
  transform: translateY(4px) scale(0.96);
}
.morph-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.96);
}
</style>
