import { createApp } from 'vue'
// Self-hosted fonts (no third-party font requests; works on patchy connections)
import '@fontsource-variable/geist'
import '@fontsource-variable/geist-mono'
import '@fontsource/noto-sans-bengali/bengali-400.css'
import '@fontsource/noto-sans-bengali/bengali-500.css'
import '@fontsource/noto-sans-bengali/bengali-600.css'
import '@fontsource/noto-sans-bengali/bengali-700.css'
import '@fontsource/noto-serif-bengali/bengali-800.css'
import './style.css'
import './theme'
import App from './App.vue'
import router from './router'
import { vReveal } from './motion'

createApp(App)
  .use(router)
  .directive('reveal', vReveal)
  .mount('#app')
