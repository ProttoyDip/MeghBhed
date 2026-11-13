// Speech to text for the assistant's microphone, through NVIDIA's hosted speech API (Riva, gRPC).
// Server-side only. The key is read from NVIDIA_ASR_API_KEY or NVIDIA_API_KEY and never logged.
//
// The browser records 16 kHz mono audio and sends it as 16-bit PCM (base64). The default model is
// Whisper Large V3 on build.nvidia.com, which handles both Bangla and English.
import { fileURLToPath } from 'node:url'
import { rateLimited, sameOrigin } from './ask-core.js'

export const SAMPLE_RATE = 16000
export const MAX_SECONDS = 30
export const MAX_AUDIO_BYTES = SAMPLE_RATE * 2 * MAX_SECONDS // 16-bit mono
export const ASR_TIMEOUT_MS = 15000
// build.nvidia.com function id of openai/whisper-large-v3 (from its API page). Change with NVIDIA_ASR_FUNCTION_ID.
export const DEFAULT_FUNCTION_ID = 'b702f636-f60c-4a3d-a6f4-f3568c13bd7d'
const LANGUAGE = { en: 'en', bn: 'bn' }

export const asrKey = (env = process.env) => env.NVIDIA_ASR_API_KEY || env.NVIDIA_API_KEY || ''

let client = null
async function rivaClient() {
  if (client) return client
  const grpc = await import('@grpc/grpc-js')
  const loader = await import('@grpc/proto-loader')
  const root = fileURLToPath(new URL('./riva/', import.meta.url))
  const def = await loader.load('riva/proto/riva_asr.proto', { includeDirs: [root], keepCase: true, longs: Number, enums: String, defaults: true })
  const pkg = grpc.loadPackageDefinition(def)
  client = new pkg.nvidia.riva.asr.RivaSpeechRecognition('grpc.nvcf.nvidia.com:443', grpc.credentials.createSsl())
  client.grpc = grpc
  return client
}

/** Transcribe 16 kHz 16-bit mono PCM. Returns the text (possibly empty). Throws on failure. */
export async function transcribe(pcm, lang, { env = process.env, clientImpl = null, timeoutMs = ASR_TIMEOUT_MS } = {}) {
  const c = clientImpl ?? (await rivaClient())
  const grpc = c.grpc
  const meta = new grpc.Metadata()
  meta.set('function-id', env.NVIDIA_ASR_FUNCTION_ID || DEFAULT_FUNCTION_ID)
  meta.set('authorization', `Bearer ${asrKey(env)}`)
  const request = {
    config: {
      encoding: 'LINEAR_PCM',
      sample_rate_hertz: SAMPLE_RATE,
      audio_channel_count: 1,
      language_code: LANGUAGE[lang] ?? 'multi',
      max_alternatives: 1,
      enable_automatic_punctuation: true,
    },
    audio: pcm,
  }
  const res = await new Promise((resolve, reject) => {
    c.Recognize(request, meta, { deadline: Date.now() + timeoutMs }, (err, out) => (err ? reject(err) : resolve(out)))
  })
  return (res?.results ?? [])
    .map((r) => r.alternatives?.[0]?.transcript ?? '')
    .join(' ')
    .replace(/\s+/g, ' ')
    .trim()
}

/** Returns { status, body } for a request to /api/transcribe. GET says whether the service is configured. */
export async function handleTranscribe({ method, headers = {}, body, ip = 'unknown' }, options = {}) {
  const env = options.env ?? process.env
  if (method === 'GET') return { status: 200, body: { available: Boolean(asrKey(env)) } }
  if (method !== 'POST') return { status: 405, body: { error: 'method_not_allowed' } }
  if (!sameOrigin(headers)) return { status: 403, body: { error: 'forbidden' } }
  if (!asrKey(env)) return { status: 503, body: { error: 'not_configured' } }
  if (rateLimited(`asr:${ip}`)) return { status: 429, body: { error: 'rate_limited' } }
  const audio = typeof body?.audio === 'string' ? Buffer.from(body.audio, 'base64') : null
  if (!audio || audio.length < SAMPLE_RATE * 2 * 0.3) return { status: 400, body: { error: 'too_short' } }
  if (audio.length > MAX_AUDIO_BYTES) return { status: 400, body: { error: 'too_long' } }
  const lang = body?.lang === 'bn' ? 'bn' : 'en'
  const started = Date.now()
  const log = options.log ?? ((e) => console.log(JSON.stringify({ at: 'transcribe', ...e })))
  try {
    const text = await transcribe(audio, lang, { env, clientImpl: options.clientImpl })
    log({ status: 'ok', ms: Date.now() - started, seconds: +(audio.length / 2 / SAMPLE_RATE).toFixed(1), chars: text.length })
    return { status: 200, body: { text } }
  } catch (e) {
    log({ status: 'error', code: e?.code ?? null, ms: Date.now() - started })
    return { status: 502, body: { error: 'transcription_failed' } } // never the raw error
  }
}
