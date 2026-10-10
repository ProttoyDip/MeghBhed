<template>
  <canvas v-show="supported" ref="canvasRef" class="block h-full w-full" aria-hidden="true"></canvas>
</template>

<script setup>
// "Soffit" — animated WebGL2 gradient (one fullscreen triangle, one fragment shader).
// Shader and CONFIG values are used exactly as supplied; only the engine is adapted
// to live inside a section (sized to its parent, pointer relative to the canvas,
// cleaned up on unmount, still frame under reduced motion).
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { reducedMotion } from '../motion'

const CONFIG = {
  bgColor: '#0e3a3c',
  colorA: '#3fc8c0',
  colorB: '#8fd8b0',
  colorC: '#c8e0d0',
  colorD: '#f04b8b',
  scale: 0.2,
  speed: 0.33,
  tilt: 2.96,
  rock: 0.3,
  horizon: 0.15,
  breathe: 0.12,
  spread: -2.03,
  curve: 3.14,
  direct: 0.6,
  bounce: 0.64,
  bounceCurve: 2.2,
  spillCentre: 0.12,
  spillWidth: 1.91,
  spillFloor: 0.66,
  amount: 0.47,
  warp: 2.83,
  warpScale: 1.2,
  flow: 0.2,
  roughness: 0.53,
  lacunarity: 2.23,
  motes: 0.074,
  moteScale: 18,
  ambient: 0.16,
  contrast: 2.98,
  midpoint: 0.78,
  sink: 0.1,
  glow: 0.29,
  grain: 0,
  grainAnim: 0,
  dither: 1.11,
  vignette: 0.07,
  steer: -0.24,
  lift: 0.09,
  sweep: 0.32,
  cursor: 1,
  parallax: 0.01,
  maxDpr: 1,
}

const VERT = `#version 300 es
void main() {
  vec2 p = vec2((gl_VertexID << 1) & 2, gl_VertexID & 2);
  gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0);
}`

const FRAG = `#version 300 es
precision highp float;
out vec4 fragColor;

uniform vec2  iResolution;
uniform float iTime;
uniform vec2  iMouse;
uniform float uScale;

uniform vec3  uBg, uColorA, uColorB, uColorC, uColorD;
uniform float uSpeed, uTilt, uRock, uHorizon, uBreathe, uSpread, uCurve, uDirect;
uniform float uBounce, uBounceCurve;
uniform float uSpillCentre, uSpillWidth, uSpillFloor;
uniform float uAmount, uWarp, uWarpScale, uFlow, uRoughness, uLacunarity, uMotes, uMoteScale;
uniform float uAmbient, uContrast, uMidpoint, uSink, uGlow;
uniform float uGrain, uDither, uVignette;
uniform float uSteer, uLift, uSweep, uParallax;

#define OCTAVES 4

vec2 hash2(vec2 p) {
  p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
  return -1.0 + 2.0 * fract(sin(p) * 43758.5453123);
}

float snoise(vec2 p) {
  const float K1 = 0.366025404, K2 = 0.211324865;
  vec2 i = floor(p + (p.x + p.y) * K1);
  vec2 a = p - i + (i.x + i.y) * K2;
  float m = step(a.y, a.x);
  vec2 o = vec2(m, 1.0 - m);
  vec2 b = a - o + K2;
  vec2 c = a - 1.0 + 2.0 * K2;
  vec3 h = max(0.5 - vec3(dot(a, a), dot(b, b), dot(c, c)), 0.0);
  vec3 n = h * h * h * h * vec3(dot(a, hash2(i)), dot(b, hash2(i + o)), dot(c, hash2(i + 1.0)));
  return dot(n, vec3(70.0));
}

float fbm(vec2 p) {
  float v = 0.0, amp = 0.5;
  for (int i = 0; i < OCTAVES; i++) {
    v += amp * snoise(p);
    p *= uLacunarity;
    amp *= uRoughness;
  }
  return v;
}

vec3 ramp4(float t) {
  vec3 c = mix(uColorA, uColorB, smoothstep(0.00, 0.36, t));
  c = mix(c, uColorC, smoothstep(0.32, 0.70, t));
  c = mix(c, uColorD, smoothstep(0.66, 1.00, t));
  return c;
}

float triDither(vec2 fc) {
  float a = fract(sin(dot(fc, vec2(12.9898, 78.233))) * 43758.5453);
  float b = fract(sin(dot(fc + 17.0, vec2(12.9898, 78.233))) * 43758.5453);
  return (a + b - 1.0) / 255.0;
}

uniform float uGrainAnim;
float houseGrain(vec2 fc) {
  uvec2 q = uvec2(fc) * uvec2(1597334677u, 3812015801u)
          + uint(floor(iTime * 24.0 * uGrainAnim)) * 2654435769u;
  uint n = q.x ^ q.y; n = n * 1664525u + 1013904223u; n ^= n >> 16u; n *= 2246822519u; n ^= n >> 13u;
  float a = float(n & 0xffffu) / 65535.0;
  n *= 3266489917u; n ^= n >> 16u;
  float b = float(n & 0xffffu) / 65535.0;
  return a + b - 1.0;
}
void main() {
  vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution) / iResolution.y;
  uv *= uScale;
  vec2 iM = iMouse * uScale;
  float t = iTime * uSpeed;

  vec2 p = uv - iM * uParallax;

  float tilt = uTilt + sin(t * 0.13) * uRock + iM.x * uSteer;
  vec2 dir = vec2(cos(tilt), sin(tilt));
  float axis = dot(p, dir);
  float across = dot(p, vec2(-dir.y, dir.x));

  vec2 q = vec2(fbm(p * uWarpScale + vec2(0.0, t * uFlow)),
                fbm(p * uWarpScale + vec2(5.2, 1.3) - t * uFlow * 0.7));
  float air = fbm(p + uWarp * q + vec2(t * 0.12, -t * 0.09)) * 0.5 + 0.5;

  float horizon = uHorizon + sin(t * 0.09 + 2.1) * uBreathe - iM.y * uLift;
  float alt = clamp(0.5 + (axis - horizon) * uSpread + (air - 0.5) * uAmount, 0.0, 1.0);

  float ac = (across - uSpillCentre - iM.x * uSweep) / max(0.05, uSpillWidth);
  float spill = mix(uSpillFloor, 1.0, exp(-ac * ac));

  float direct = pow(alt, max(0.05, uCurve)) * uDirect * spill;

  float bounce = uBounce * pow(1.0 - alt, max(0.05, uBounceCurve));

  float f = uAmbient + direct + bounce;
  f += uMotes * snoise(p * uMoteScale + vec2(-t * 0.5, t * 0.35)) * 0.5 * alt;

  f = clamp((f - uMidpoint) * uContrast + 0.5, 0.0, 1.0);

  vec3 col = ramp4(f);
  col += uColorD * uGlow * pow(f, 4.0);
  col = mix(uBg, col, smoothstep(0.0, max(0.01, uSink), f) * 0.90 + 0.10);

  col *= 1.0 - uVignette * dot(uv, uv);
  { float hgL = clamp(dot(col, vec3(0.299, 0.587, 0.114)), 0.0, 1.0);
    col += houseGrain(gl_FragCoord.xy) * uGrain * mix(1.0, 4.0 * hgL * (1.0 - hgL), 0.6); }
  col += triDither(gl_FragCoord.xy) * uDither;

  fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}`

const canvasRef = ref(null)
const supported = ref(true)

let gl = null
let program = null
let raf = 0
let resizeObs = null
let visObs = null
let visible = true
const cleanups = []

// A full-screen shader on a CPU rasteriser (no GPU acceleration) would pin the
// main thread, so such devices get the still first frame instead of the animation.
function softwareRendered() {
  const info = gl.getExtension('WEBGL_debug_renderer_info')
  const renderer = info ? gl.getParameter(info.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER)
  return /swiftshader|llvmpipe|software|microsoft basic render/i.test(String(renderer))
}

function hexToVec3(hex) {
  const v = parseInt(hex.replace('#', ''), 16)
  return [((v >> 16) & 255) / 255, ((v >> 8) & 255) / 255, (v & 255) / 255]
}

onMounted(() => {
  const canvas = canvasRef.value
  gl = canvas.getContext('webgl2', { alpha: false, antialias: false, depth: false, stencil: false, powerPreference: 'high-performance' })
  if (!gl) {
    supported.value = false // the section's own background shows instead
    return
  }

  const compile = (type, src) => {
    const sh = gl.createShader(type)
    gl.shaderSource(sh, src)
    gl.compileShader(sh)
    if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(sh))
    return sh
  }
  try {
    program = gl.createProgram()
    gl.attachShader(program, compile(gl.VERTEX_SHADER, VERT))
    gl.attachShader(program, compile(gl.FRAGMENT_SHADER, FRAG))
    gl.linkProgram(program)
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program))
  } catch (err) {
    console.warn('SoffitGradient disabled:', err)
    supported.value = false
    return
  }
  gl.useProgram(program)
  gl.bindVertexArray(gl.createVertexArray())

  const LOC = {}
  const loc = (n) => (n in LOC ? LOC[n] : (LOC[n] = gl.getUniformLocation(program, n)))
  const u1f = (n, v) => gl.uniform1f(loc(n), v)
  const u2f = (n, x, y) => gl.uniform2f(loc(n), x, y)
  const u3c = (n, hex) => {
    const c = hexToVec3(hex)
    gl.uniform3f(loc(n), c[0], c[1], c[2])
  }

  // CONFIG → uniforms: one uniform per key, `u` + capitalised key (bgColor → uBg)
  u3c('uBg', CONFIG.bgColor)
  for (const k of ['colorA', 'colorB', 'colorC', 'colorD']) u3c(`u${k[0].toUpperCase()}${k.slice(1)}`, CONFIG[k])
  for (const [k, v] of Object.entries(CONFIG)) {
    if (typeof v !== 'number' || k === 'cursor' || k === 'maxDpr') continue
    u1f(`u${k[0].toUpperCase()}${k.slice(1)}`, v)
  }

  // Sized to the parent section, not the window
  let cssW = 1
  let cssH = 1
  const resize = () => {
    const dpr = Math.min(window.devicePixelRatio || 1, CONFIG.maxDpr)
    cssW = Math.max(1, canvas.clientWidth)
    cssH = Math.max(1, canvas.clientHeight)
    const w = Math.max(1, Math.round(cssW * dpr))
    const h = Math.max(1, Math.round(cssH * dpr))
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w
      canvas.height = h
    }
    gl.viewport(0, 0, w, h)
    u2f('iResolution', w, h)
  }
  let resizeQueued = false
  resizeObs = new ResizeObserver(() => {
    if (resizeQueued) return
    resizeQueued = true
    requestAnimationFrame(() => {
      resizeQueued = false
      resize()
      if (reducedMotion || !raf) gl.drawArrays(gl.TRIANGLES, 0, 3)
    })
  })
  resizeObs.observe(canvas)
  resize()

  // Pointer: two-stage lerp (fast lead, slower body), relative to the canvas
  const mouse = { x: 0, y: 0, ax: 0, ay: 0, tx: 0, ty: 0 }
  const aim = (e) => {
    const r = canvas.getBoundingClientRect()
    const a = cssW / cssH
    mouse.tx = ((e.clientX - r.left) / r.width - 0.5) * a
    mouse.ty = 0.5 - (e.clientY - r.top) / r.height
  }
  window.addEventListener('pointermove', aim, { passive: true })
  window.addEventListener('pointerdown', aim, { passive: true })
  cleanups.push(() => {
    window.removeEventListener('pointermove', aim)
    window.removeEventListener('pointerdown', aim)
  })

  visObs = new IntersectionObserver((es) => (visible = es[0].isIntersecting), { threshold: 0 })
  visObs.observe(canvas)

  // Clamped, accumulated clock: a background tab costs a pause, never a lurch
  let prevT = performance.now()
  let clock = 0
  const frame = (now) => {
    raf = requestAnimationFrame(frame)
    const raw = now - prevT
    prevT = now
    if (!visible || document.hidden) return
    const ms = raw > 50 ? 50 : raw < 4.167 ? 4.167 : raw
    const s = ms > 36.7 ? 2.2 : ms * 0.06
    clock += ms * 0.001

    const kLead = 0.105 * s
    const kBody = 0.043 * s
    mouse.ax += (mouse.tx - mouse.ax) * kLead
    mouse.ay += (mouse.ty - mouse.ay) * kLead
    mouse.x += (mouse.ax - mouse.x) * kBody
    mouse.y += (mouse.ay - mouse.y) * kBody

    u1f('iTime', clock)
    if (mouse.rest === undefined) mouse.rest = { x: mouse.tx, y: mouse.ty }
    if (!CONFIG.cursor) {
      mouse.tx = mouse.rest.x
      mouse.ty = mouse.rest.y
    }
    u2f('iMouse', mouse.x, mouse.y)
    gl.drawArrays(gl.TRIANGLES, 0, 3)
  }

  u1f('iTime', 0)
  u2f('iMouse', 0, 0)
  gl.drawArrays(gl.TRIANGLES, 0, 3) // one draw before the loop, never a blank canvas
  if (!reducedMotion && !softwareRendered()) raf = requestAnimationFrame(frame)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  resizeObs?.disconnect()
  visObs?.disconnect()
  cleanups.forEach((fn) => fn())
  gl?.getExtension('WEBGL_lose_context')?.loseContext()
  gl = null
})
</script>
