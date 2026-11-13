// Unit tests for the assistant's server logic, with fetch mocked: no real provider is ever called.
// Run with: npm run test:unit
import { test, beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import { ask, handle, configuredProviders, publicProviders, splitSource, resetRateLimit, RATE_LIMIT, MAX_QUESTION_CHARS } from '../server/ask-core.js'
import { buildFacts, extractNumbers, numbersAreGrounded } from '../server/facts.js'

const FACTS = buildFacts()
const GOOD = 'In Satkania, NISAR likely saw 27.7 km² of flood on 12 July 2026 that the 16 July map missed; about 106,169 people live within 100 m (an upper bound).\nSource: stats.json → Satkania'
const INVENTED = 'In Satkania about 999,999 people were affected.\nSource: stats.json → Satkania'

const openaiReply = (text) => ({ ok: true, status: 200, json: async () => ({ choices: [{ message: { content: text } }] }) })
const geminiReply = (text) => ({ ok: true, status: 200, json: async () => ({ candidates: [{ content: { parts: [{ text }] } }] }) })
const anthropicReply = (text) => ({ ok: true, status: 200, json: async () => ({ stop_reason: 'end_turn', content: [{ type: 'text', text }] }) })
const httpError = (status) => ({ ok: false, status, json: async () => ({}) })

// A fetch that answers per host and records what was called (never the network)
function mockFetch(byHost) {
  const calls = []
  const impl = async (url, init) => {
    const host = new URL(url).host
    calls.push({ host, url: String(url), init })
    const r = byHost[host]
    if (!r) throw new Error('unexpected host ' + host)
    return typeof r === 'function' ? r(url, init) : r
  }
  return { impl, calls }
}
const opts = (env, fetchImpl) => ({ env, fetchImpl, factsBlock: FACTS, log: () => {} })
const headers = { origin: 'http://localhost:5173', host: 'localhost:5173' }

beforeEach(() => resetRateLimit())

test('the first provider succeeds', async () => {
  const f = mockFetch({ 'api.groq.com': openaiReply(GOOD) })
  const r = await ask({ question: 'How many people in Satkania?' }, opts({ GROQ_API_KEY: 'test-key', GEMINI_API_KEY: 'test-key' }, f.impl))
  assert.equal(r.fallback, false)
  assert.equal(r.provider, 'Groq')
  assert.equal(r.model, 'openai/gpt-oss-20b')
  assert.equal(r.source, 'stats.json → Satkania')
  assert.match(r.answer, /106,169/)
  assert.equal(f.calls.length, 1)
})

test('the first provider fails and the second succeeds', async () => {
  const f = mockFetch({ 'api.groq.com': httpError(429), 'generativelanguage.googleapis.com': geminiReply(GOOD) })
  const r = await ask({ question: 'q' }, opts({ GROQ_API_KEY: 'k', GEMINI_API_KEY: 'k' }, f.impl))
  assert.equal(r.fallback, false)
  assert.equal(r.provider, 'Google Gemini')
  assert.deepEqual(r.tried.map((t) => t.status), ['http 429', 'ok'])
})

test('all providers fail: fallback is true and no error text leaks', async () => {
  const f = mockFetch({
    'api.groq.com': httpError(500),
    'generativelanguage.googleapis.com': async () => {
      throw new Error('socket hang up')
    },
    'api.openai.com': openaiReply(''),
  })
  const r = await ask({ question: 'q' }, opts({ GROQ_API_KEY: 'k', GEMINI_API_KEY: 'k', OPENAI_API_KEY: 'k' }, f.impl))
  assert.equal(r.fallback, true)
  assert.equal(r.answer, null)
  assert.deepEqual(r.tried.map((t) => t.status), ['http 500', 'network error', 'empty'])
})

test('an answer with an invented number is rejected and the next provider is tried', async () => {
  const f = mockFetch({ 'api.groq.com': openaiReply(INVENTED), 'api.anthropic.com': anthropicReply(GOOD) })
  const r = await ask({ question: 'q' }, opts({ GROQ_API_KEY: 'k', ANTHROPIC_API_KEY: 'k' }, f.impl))
  assert.equal(r.provider, 'Anthropic')
  assert.equal(r.tried[0].status, 'ungrounded')
})

test('a provider with no key is skipped', async () => {
  const f = mockFetch({ 'api.openai.com': openaiReply(GOOD) })
  const r = await ask({ question: 'q' }, opts({ OPENAI_API_KEY: 'k' }, f.impl)) // groq and gemini come first in the order but have no key
  assert.equal(r.provider, 'OpenAI')
  assert.deepEqual(f.calls.map((c) => c.host), ['api.openai.com'])
  assert.deepEqual(configuredProviders({}).length, 0)
})

test('no provider configured: fallback without any network call', async () => {
  const f = mockFetch({})
  const r = await ask({ question: 'q' }, opts({}, f.impl))
  assert.equal(r.fallback, true)
  assert.equal(f.calls.length, 0)
})

test('a slow provider times out and the next one answers', async () => {
  const slow = (url, init) => new Promise((_, reject) => init.signal.addEventListener('abort', () => reject(Object.assign(new Error('aborted'), { name: 'AbortError' }))))
  const f = mockFetch({ 'api.groq.com': slow, 'openrouter.ai': openaiReply(GOOD) })
  const r = await ask({ question: 'q' }, { ...opts({ GROQ_API_KEY: 'k', OPENROUTER_API_KEY: 'k' }, f.impl), timeoutMs: 30 })
  assert.equal(r.provider, 'OpenRouter')
  assert.equal(r.tried[0].status, 'timeout')
})

test('LLM_ORDER sets the order, and the choice made by the visitor goes first', async () => {
  const env = { GROQ_API_KEY: 'k', OPENROUTER_API_KEY: 'k', LLM_ORDER: 'openrouter,groq' }
  assert.deepEqual(configuredProviders(env).map((p) => p.id), ['openrouter', 'groq'])
  const f = mockFetch({ 'api.groq.com': openaiReply(GOOD), 'openrouter.ai': openaiReply(GOOD) })
  const r = await ask({ question: 'q', prefer: 'groq' }, opts(env, f.impl))
  assert.equal(r.provider, 'Groq')
})

test('a model variable overrides the default, and custom OpenAI-compatible services work', async () => {
  const env = { GROQ_API_KEY: 'k', GROQ_MODEL: 'some/other-model', CUSTOM1_API_KEY: 'k', CUSTOM1_BASE_URL: 'https://router.example/v1/', CUSTOM1_MODEL: 'tiny', CUSTOM1_NAME: 'My Router' }
  assert.deepEqual(publicProviders(env), [
    { id: 'groq', label: 'Groq', model: 'some/other-model' },
    { id: 'custom1', label: 'My Router', model: 'tiny' },
  ])
  const f = mockFetch({ 'api.groq.com': httpError(402), 'router.example': openaiReply(GOOD) })
  const r = await ask({ question: 'q' }, opts(env, f.impl))
  assert.equal(r.provider, 'My Router')
  assert.equal(f.calls[1].url, 'https://router.example/v1/chat/completions')
})

test('requests carry the key only in a header, with the limits asked for', async () => {
  const f = mockFetch({ 'api.groq.com': openaiReply(GOOD), 'api.anthropic.com': anthropicReply(GOOD), 'api.openai.com': openaiReply(GOOD) })
  await ask({ question: 'q' }, opts({ GROQ_API_KEY: 'secret-groq', GROQ_MODEL: 'meta/plain-chat-model' }, f.impl))
  const body = JSON.parse(f.calls[0].init.body)
  assert.equal(f.calls[0].init.headers.authorization, 'Bearer secret-groq')
  assert.equal(body.max_tokens, 300)
  assert.equal(body.temperature, 0.2)
  assert.ok(!JSON.stringify(body).includes('secret-groq'))
  await ask({ question: 'q' }, opts({ GROQ_API_KEY: 'k' }, f.impl)) // the default, gpt-oss-20b, reasons before it answers
  const oss = JSON.parse(f.calls[1].init.body)
  assert.equal(oss.reasoning_effort, 'low')
  assert.equal(oss.max_tokens, 1000)
  f.calls.splice(1, 1)
  await ask({ question: 'q' }, opts({ ANTHROPIC_API_KEY: 'secret-ant' }, f.impl))
  const a = JSON.parse(f.calls[1].init.body)
  assert.equal(f.calls[1].init.headers['x-api-key'], 'secret-ant')
  assert.equal(a.max_tokens, 300)
  assert.equal(a.temperature, undefined) // current Claude models reject non-default sampling parameters
  await ask({ question: 'q' }, opts({ OPENAI_API_KEY: 'k' }, f.impl))
  const o = JSON.parse(f.calls[2].init.body)
  assert.equal(o.temperature, undefined) // gpt-5 models are reasoning models
  assert.ok(o.max_completion_tokens >= 300)
})

test('handler: an over-long question is rejected', async () => {
  const r = await handle({ method: 'POST', headers, body: { question: 'x'.repeat(MAX_QUESTION_CHARS + 1) }, ip: '1.1.1.1' }, opts({ GROQ_API_KEY: 'k' }, mockFetch({}).impl))
  assert.equal(r.status, 400)
  assert.equal(r.body.error, 'question_too_long')
  assert.equal(r.body.fallback, true)
})

test('handler: cross-origin and missing-origin requests are refused', async () => {
  const o = opts({}, mockFetch({}).impl)
  assert.equal((await handle({ method: 'POST', headers: { origin: 'https://evil.example', host: 'localhost:5173' }, body: { question: 'q' } }, o)).status, 403)
  assert.equal((await handle({ method: 'POST', headers: { host: 'localhost:5173' }, body: { question: 'q' } }, o)).status, 403)
  assert.equal((await handle({ method: 'POST', headers, body: { question: 'q' }, ip: '2.2.2.2' }, o)).status, 200)
})

test('handler: rate limit per IP', async () => {
  const o = opts({}, mockFetch({}).impl)
  for (let i = 0; i < RATE_LIMIT.max; i++) assert.equal((await handle({ method: 'POST', headers, body: { question: 'q' }, ip: '3.3.3.3' }, o)).status, 200)
  assert.equal((await handle({ method: 'POST', headers, body: { question: 'q' }, ip: '3.3.3.3' }, o)).status, 429)
  assert.equal((await handle({ method: 'POST', headers, body: { question: 'q' }, ip: '4.4.4.4' }, o)).status, 200)
})

test('handler: GET lists configured providers and never a key; the POST reply has only the public fields', async () => {
  const env = { GROQ_API_KEY: 'secret-groq-key' }
  const g = await handle({ method: 'GET', headers }, opts(env, mockFetch({}).impl))
  assert.deepEqual(g.body, { providers: [{ id: 'groq', label: 'Groq', model: 'openai/gpt-oss-20b' }] })
  const p = await handle({ method: 'POST', headers, body: { question: 'q', lang: 'bn' }, ip: '5.5.5.5' }, opts(env, mockFetch({ 'api.groq.com': openaiReply(GOOD) }).impl))
  assert.deepEqual(Object.keys(p.body).sort(), ['answer', 'fallback', 'model', 'provider', 'source'])
  assert.ok(!JSON.stringify([g.body, p.body]).includes('secret-groq-key'))
})

test('grounding: separators, Bangla digits and rounding are accepted; invented numbers are not', () => {
  const ok = (s) => numbersAreGrounded(s, FACTS.numbers).ok
  assert.ok(ok('587,479 people, 169.22 km², 12 July 2026'))
  assert.ok(ok('5,87,479 জন')) // Indian grouping
  assert.ok(ok('৫,৮৭,৪৭৯ জন মানুষ, ১৬৯.২২ বর্গকিমি')) // Bangla digits
  assert.ok(ok('about 169.2 km² and 79% drained')) // 169.22 and 78.7, rounded
  assert.ok(ok('only 3 dB and 5 m')) // single digits are not checked
  assert.ok(!ok('600,000 people'))
  assert.ok(!ok('about 170.5 km²'))
  assert.deepEqual(extractNumbers('a 1,234.5 b ৪২').map((n) => n.value), [1234.5, 42])
})

test('the source line is split off the answer', () => {
  assert.deepEqual(splitSource('Text here.\nSource: stats.json → totals'), { answer: 'Text here.', source: 'stats.json → totals' })
  assert.deepEqual(splitSource('No source line'), { answer: 'No source line', source: null })
})

test('the facts block is small and says what the rules require', () => {
  assert.ok(FACTS.text.length < 8000)
  for (const s of ['12 July 2026', 'upper bound', 'not a forecast', 'could not be confirmed', 'Satkania']) assert.ok(FACTS.text.includes(s), s)
})

// ---- NVIDIA free models, greetings, time limit, dates -------------------------------------------
import { NVIDIA_FREE_MODELS, stripThinking, systemPrompt } from '../server/ask-core.js'

test('NVIDIA expands into one fallback step per free model, and NVIDIA_MODELS overrides the list', () => {
  const ids = configuredProviders({ NVIDIA_API_KEY: 'k' })
  assert.deepEqual(ids.map((p) => p.model), NVIDIA_FREE_MODELS)
  assert.ok(ids.every((p) => p.label === 'NVIDIA'))
  assert.deepEqual(configuredProviders({ NVIDIA_API_KEY: 'k', NVIDIA_MODELS: 'a/one, b/two' }).map((p) => p.model), ['a/one', 'b/two'])
  assert.equal(configuredProviders({ NVIDIA_API_KEY: 'k', OPENROUTER_API_KEY: 'k' })[0].id, 'nvidia') // NVIDIA comes first by default
})

test('an NVIDIA model that is rate-limited falls through to the next NVIDIA model, with thinking switched off', async () => {
  let n = 0
  const f = mockFetch({ 'integrate.api.nvidia.com': () => (n++ === 0 ? httpError(429) : openaiReply(GOOD)) })
  const r = await ask({ question: 'q' }, opts({ NVIDIA_API_KEY: 'k' }, f.impl))
  assert.equal(r.provider, 'NVIDIA')
  assert.equal(r.model, NVIDIA_FREE_MODELS[1])
  const body = JSON.parse(f.calls[1].init.body)
  assert.deepEqual(body.chat_template_kwargs, { enable_thinking: false })
  assert.equal(body.max_tokens, 300)
})

test('thinking tags are removed before the answer is checked', async () => {
  assert.equal(stripThinking('<think>reasoning 999,999</think>Hello!'), 'Hello!')
  const f = mockFetch({ 'integrate.api.nvidia.com': openaiReply('<think>maybe 123,456 people</think>' + GOOD) })
  const r = await ask({ question: 'q' }, opts({ NVIDIA_API_KEY: 'k' }, f.impl))
  assert.equal(r.fallback, false)
  assert.doesNotMatch(r.answer, /think/)
})

test('the whole chain stops before the overall time limit', async () => {
  const slow = (url, init) => new Promise((_, reject) => init.signal.addEventListener('abort', () => reject(Object.assign(new Error('aborted'), { name: 'AbortError' }))))
  const f = mockFetch({ 'integrate.api.nvidia.com': slow, 'openrouter.ai': openaiReply(GOOD) })
  const t0 = Date.now()
  const r = await ask({ question: 'q' }, { ...opts({ NVIDIA_API_KEY: 'k', OPENROUTER_API_KEY: 'k' }, f.impl), timeoutMs: 1000, totalMs: 2000 })
  assert.ok(Date.now() - t0 < 2500)
  assert.equal(r.fallback, true)
  assert.ok(r.tried.some((x) => x.status.startsWith('skipped')))
})

test('grounding rejects a wrong date such as "10 July"', () => {
  assert.ok(!numbersAreGrounded('এই তথ্যগুলো ১০ জুলাই ২০২৬ এর জন্য', FACTS.numbers, FACTS.dates).ok)
  assert.ok(numbersAreGrounded('The flood map is for 12 July 2026; it drained by 19 July.', FACTS.numbers, FACTS.dates).ok)
})

test('the rules tell the model to greet instead of saying the data is missing, and no longer ask for a source line', () => {
  const sp = systemPrompt(FACTS.text, 'en')
  assert.match(sp, /greeting/)
  assert.doesNotMatch(sp, /Source:/)
})
