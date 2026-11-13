// Unit tests for the speech-to-text endpoint, with the NVIDIA gRPC client mocked: no audio leaves the machine.
import { test, beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import { handleTranscribe, transcribe, SAMPLE_RATE, MAX_AUDIO_BYTES, DEFAULT_FUNCTION_ID } from '../server/transcribe-core.js'
import { resetRateLimit } from '../server/ask-core.js'

const headers = { origin: 'http://localhost:5173', host: 'localhost:5173' }
const pcm = (seconds) => Buffer.alloc(Math.round(SAMPLE_RATE * 2 * seconds)).toString('base64')

// A stand-in for the Riva client: records the call and answers like the real service
function mockClient(reply, calls = []) {
  class Metadata {
    constructor() { this.map = {} }
    set(k, v) { this.map[k] = v }
  }
  return {
    calls,
    grpc: { Metadata },
    Recognize(request, meta, options, cb) {
      calls.push({ request, meta: meta.map, options })
      if (reply instanceof Error) cb(reply)
      else cb(null, { results: [{ alternatives: [{ transcript: reply }] }] })
    },
  }
}
const log = () => {}

beforeEach(() => resetRateLimit())

test('GET says whether speech-to-text is configured, never a key', async () => {
  assert.deepEqual((await handleTranscribe({ method: 'GET' }, { env: {} })).body, { available: false })
  const r = await handleTranscribe({ method: 'GET' }, { env: { NVIDIA_API_KEY: 'secret-nv' } })
  assert.deepEqual(r.body, { available: true })
})

test('a recording is sent as 16 kHz PCM with the key in a header, and the text comes back', async () => {
  const c = mockClient('How many people live near the flood in Satkania?')
  const r = await handleTranscribe({ method: 'POST', headers, body: { audio: pcm(2), lang: 'en' }, ip: '1.1.1.1' }, { env: { NVIDIA_API_KEY: 'secret-nv' }, clientImpl: c, log })
  assert.equal(r.status, 200)
  assert.equal(r.body.text, 'How many people live near the flood in Satkania?')
  const call = c.calls[0]
  assert.equal(call.request.config.encoding, 'LINEAR_PCM')
  assert.equal(call.request.config.sample_rate_hertz, 16000)
  assert.equal(call.request.config.language_code, 'en')
  assert.equal(call.meta.authorization, 'Bearer secret-nv')
  assert.equal(call.meta['function-id'], DEFAULT_FUNCTION_ID)
  assert.ok(!JSON.stringify(r.body).includes('secret-nv'))
})

test('Bangla mode asks the model for Bangla', async () => {
  const c = mockClient('সাতকানিয়ায় কত মানুষ?')
  await transcribe(Buffer.alloc(32000), 'bn', { env: { NVIDIA_API_KEY: 'k' }, clientImpl: c })
  assert.equal(c.calls[0].request.config.language_code, 'bn')
})

test('too short, too long, cross-origin and unconfigured requests are refused', async () => {
  const env = { NVIDIA_API_KEY: 'k' }
  const o = { env, clientImpl: mockClient('x'), log }
  assert.equal((await handleTranscribe({ method: 'POST', headers, body: { audio: pcm(0.1) }, ip: '2.2.2.2' }, o)).body.error, 'too_short')
  assert.equal((await handleTranscribe({ method: 'POST', headers, body: { audio: Buffer.alloc(MAX_AUDIO_BYTES + 2).toString('base64') }, ip: '2.2.2.2' }, o)).body.error, 'too_long')
  assert.equal((await handleTranscribe({ method: 'POST', headers: { origin: 'https://evil.example', host: 'localhost:5173' }, body: { audio: pcm(2) } }, o)).status, 403)
  assert.equal((await handleTranscribe({ method: 'POST', headers, body: { audio: pcm(2) }, ip: '2.2.2.2' }, { env: {}, log })).status, 503)
})

test('a service error is reported without its details', async () => {
  const err = Object.assign(new Error('UNAUTHENTICATED: bad key secret-nv'), { code: 16 })
  const r = await handleTranscribe({ method: 'POST', headers, body: { audio: pcm(2) }, ip: '3.3.3.3' }, { env: { NVIDIA_API_KEY: 'secret-nv' }, clientImpl: mockClient(err), log })
  assert.equal(r.status, 502)
  assert.deepEqual(r.body, { error: 'transcription_failed' })
})
