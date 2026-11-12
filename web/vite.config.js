import vue from '@vitejs/plugin-vue'
import { defineConfig, loadEnv } from 'vite'

// Runs the same handler as the Vercel function (api/ask.js) under `npm run dev`, so the assistant
// works locally without the Vercel CLI. Keys are read from web/.env.local into the dev server's
// own process; they are never given the VITE_ prefix, so Vite never puts them in the browser bundle.
function askApiDev() {
  return {
    name: 'meghbhed-ask-api-dev',
    apply: 'serve',
    configureServer(server) {
      const env = loadEnv(server.config.mode, process.cwd(), '')
      for (const [k, v] of Object.entries(env)) if (!(k in process.env)) process.env[k] = v
      server.middlewares.use('/api/ask', async (req, res) => {
        const { default: handler } = await server.ssrLoadModule('/api/ask.js')
        handler(req, res)
      })
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), askApiDev()],
})
