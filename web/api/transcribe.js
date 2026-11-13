// Vercel serverless function: POST /api/transcribe { audio: base64 16 kHz 16-bit mono PCM, lang } -> { text }
// GET /api/transcribe -> { available } (whether NVIDIA speech-to-text is configured; never a key).
// All logic, and every read of the key, is in ../server/transcribe-core.js.
import { handleTranscribe, MAX_AUDIO_BYTES } from '../server/transcribe-core.js'

const MAX_BODY = Math.ceil((MAX_AUDIO_BYTES * 4) / 3) + 4096 // base64 of 30 s of audio, plus the JSON around it

async function readBody(req) {
  if (req.body && typeof req.body === 'object') return req.body
  if (typeof req.body === 'string') return safeParse(req.body)
  const chunks = []
  let size = 0
  for await (const chunk of req) {
    size += chunk.length
    if (size > MAX_BODY) return {}
    chunks.push(chunk)
  }
  return safeParse(Buffer.concat(chunks).toString('utf8'))
}

function safeParse(text) {
  try {
    return JSON.parse(text || '{}')
  } catch {
    return {}
  }
}

export default async function handler(req, res) {
  let out
  try {
    const ip = String(req.headers['x-forwarded-for'] ?? req.socket?.remoteAddress ?? 'unknown').split(',')[0].trim()
    out = await handleTranscribe({ method: req.method, headers: req.headers, body: req.method === 'POST' ? await readBody(req) : null, ip })
  } catch {
    out = { status: 502, body: { error: 'transcription_failed' } }
  }
  res.statusCode = out.status
  res.setHeader('content-type', 'application/json; charset=utf-8')
  res.setHeader('cache-control', 'no-store')
  res.end(JSON.stringify(out.body))
}
