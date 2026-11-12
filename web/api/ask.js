// Vercel serverless function: POST /api/ask { question, lang, provider? }
//   -> { answer, source, provider, model, fallback }
// GET /api/ask -> { providers: [{ id, label, model }] } (which services are configured; never a key).
// All logic, and every read of an API key, is in ../server/ask-core.js.
import { handle } from '../server/ask-core.js'

async function readBody(req) {
  if (req.body && typeof req.body === 'object') return req.body // Vercel has already parsed JSON
  if (typeof req.body === 'string') return safeParse(req.body)
  const chunks = []
  let size = 0
  for await (const chunk of req) {
    size += chunk.length
    if (size > 8192) return {} // far more than a 500-character question needs
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
    out = await handle({ method: req.method, headers: req.headers, body: req.method === 'POST' ? await readBody(req) : null, ip })
  } catch {
    out = { status: 200, body: { answer: null, source: null, provider: null, model: null, fallback: true } } // never a raw error
  }
  res.statusCode = out.status
  res.setHeader('content-type', 'application/json; charset=utf-8')
  res.setHeader('cache-control', 'no-store')
  res.end(JSON.stringify(out.body))
}
