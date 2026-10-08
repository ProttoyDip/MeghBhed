<template>
  <div class="w-full h-[calc(100vh-80px)] md:h-[calc(100vh-100px)] relative overflow-hidden flex bg-space-950 font-sans">
    
    <!-- Mobile Sidebar Toggle -->
    <button @click="sidebarOpen = !sidebarOpen" class="lg:hidden absolute top-4 left-4 z-50 p-2.5 rounded-lg bg-space-800 border border-white/10 shadow-xl text-white">
      <Layers v-if="!sidebarOpen" class="w-5 h-5" />
      <X v-else class="w-5 h-5" />
    </button>

    <!-- Sidebar Panel (Professional GIS Look) -->
    <div 
      class="absolute top-0 left-0 lg:static z-40 w-full lg:w-[380px] h-full flex flex-col transition-transform duration-300 lg:translate-x-0 bg-space-900 border-r border-white/5 shadow-2xl"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <!-- Header -->
      <div class="p-5 border-b border-white/5 shrink-0 bg-space-950">
        <div class="flex items-center gap-2 mb-1">
          <MapIcon class="w-4 h-4 text-accent-blue" />
          <h2 class="text-sm font-bold text-white uppercase tracking-wider">Analysis Map</h2>
        </div>
        <p class="text-[10px] text-slate-500 font-medium">Chattogram Division • July 2026 Flood Event</p>
      </div>

      <!-- Controls Area -->
      <div class="flex-1 overflow-y-auto p-5 scrollbar-thin">
        
        <!-- Dataset Selector -->
        <div class="mb-6">
          <h3 class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Loaded Datasets</h3>
          <div class="space-y-2">
            <!-- Layer 1 -->
            <label class="flex items-center justify-between p-3 rounded-lg border border-accent-blue/30 bg-accent-blue/5 cursor-pointer hover:bg-accent-blue/10 transition-colors">
              <div class="flex items-center gap-3">
                <Satellite class="w-4 h-4 text-accent-blue" />
                <div>
                  <span class="block text-xs font-bold text-white">NISAR GCOV L-Band</span>
                  <span class="block text-[9px] text-accent-blue/80 uppercase tracking-wide">Track 133 • Ascending</span>
                </div>
              </div>
              <input type="checkbox" checked class="accent-accent-blue w-4 h-4 rounded bg-space-800 border-white/20">
            </label>

            <!-- Layer 2 -->
            <label class="flex items-center justify-between p-3 rounded-lg border border-white/10 bg-space-800/50 cursor-pointer hover:bg-space-800 transition-colors">
              <div class="flex items-center gap-3">
                <Globe2 class="w-4 h-4 text-slate-400" />
                <div>
                  <span class="block text-xs font-bold text-slate-300">OPERA DSWx-S1</span>
                  <span class="block text-[9px] text-slate-500 uppercase tracking-wide">Sentinel-1 RTC Derived</span>
                </div>
              </div>
              <input type="checkbox" checked class="accent-slate-500 w-4 h-4 rounded bg-space-800 border-white/20">
            </label>
            
            <!-- Layer 3 -->
            <label class="flex items-center justify-between p-3 rounded-lg border border-accent-orange/20 bg-space-800/50 cursor-pointer hover:bg-space-800 transition-colors">
              <div class="flex items-center gap-3">
                <Mountain class="w-4 h-4 text-accent-orange" />
                <div>
                  <span class="block text-xs font-bold text-slate-300">Landslide Susceptibility</span>
                  <span class="block text-[9px] text-slate-500 uppercase tracking-wide">NASA LHASA Model Overlay</span>
                </div>
              </div>
              <input type="checkbox" class="accent-accent-orange w-4 h-4 rounded bg-space-800 border-white/20">
            </label>
          </div>
        </div>

        <!-- Time Series Control -->
        <div class="mb-6">
          <h3 class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Acquisition Timeline</h3>
          <div class="p-4 rounded-lg border border-white/5 bg-space-800/30">
            <div class="flex justify-between text-[10px] text-slate-400 mb-2 font-medium">
              <span>Pre-Flood (Jul 12)</span>
              <span class="text-white font-bold">Peak (Jul 28)</span>
              <span>Post (Aug 09)</span>
            </div>
            <input type="range" min="1" max="100" value="50" class="w-full h-1 bg-space-700 rounded-lg appearance-none cursor-pointer accent-accent-blue">
          </div>
        </div>

        <!-- Radar Stats Panel -->
        <div>
          <h3 class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Pixel Radiometry (RCS)</h3>
          <div class="grid grid-cols-2 gap-2">
            <div class="p-3 rounded-lg bg-space-800/30 border border-white/5">
              <p class="text-[9px] text-slate-500 uppercase tracking-wider mb-1">σ° HH (Current)</p>
              <p class="text-sm font-bold text-white">+3.8 dB</p>
            </div>
            <div class="p-3 rounded-lg bg-space-800/30 border border-white/5">
              <p class="text-[9px] text-slate-500 uppercase tracking-wider mb-1">σ° HV (Current)</p>
              <p class="text-sm font-bold text-white">-14.2 dB</p>
            </div>
            <div class="col-span-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-between group cursor-pointer hover:bg-red-500/20 transition-colors">
              <div>
                <p class="text-[9px] text-red-400 uppercase tracking-wider mb-0.5">Double-Bounce Anomaly</p>
                <p class="text-sm font-bold text-white flex items-center gap-2">34.2 km² <span class="text-[10px] font-normal text-slate-400">total in frame</span></p>
              </div>
              <AlertTriangle class="w-5 h-5 text-red-500 opacity-80 group-hover:scale-110 transition-transform" />
            </div>
          </div>
        </div>
      </div>
      
      <!-- Footer Tools -->
      <div class="p-4 border-t border-white/5 shrink-0 bg-space-950 flex justify-between gap-2">
        <button class="flex-1 py-2 bg-space-800 hover:bg-space-700 rounded-lg text-[10px] font-bold text-white tracking-widest uppercase transition-colors border border-white/5 flex items-center justify-center gap-2">
          <Download class="w-3 h-3" /> Export GeoTIFF
        </button>
      </div>
    </div>

    <!-- Map Canvas Area -->
    <div class="flex-1 relative bg-[#0a0f18] overflow-hidden select-none" ref="mapContainerRef" @mousemove="handleMouseMove" @touchmove="handleTouchMove">
      
      <div class="absolute inset-0 w-full h-full z-10">
        
        <!-- Base Map: L-Band (Reveals hidden floods in red) -->
        <div class="absolute inset-0 w-full h-full bg-[url('https://images.unsplash.com/photo-1524661135-423995f22d0b?q=80&w=2000&auto=format&fit=crop')] bg-cover bg-center brightness-[0.85] contrast-125">
          <!-- Base L-Band Water (Blue) -->
          <div class="absolute inset-0 bg-space-900/30 mix-blend-overlay"></div>
          
          <!-- The Magic: Hidden Floods in Red -->
          <div class="absolute top-1/3 left-[20%] w-32 h-32 md:w-64 md:h-64 bg-red-500 blur-[40px] md:blur-[60px] rounded-full opacity-80 mix-blend-screen pointer-events-none"></div>
          <div class="absolute bottom-1/4 left-[35%] w-40 h-24 md:w-80 md:h-40 bg-red-500 blur-[40px] md:blur-[60px] rounded-full opacity-70 mix-blend-screen pointer-events-none"></div>
          <div class="absolute top-1/2 right-[25%] w-48 h-32 bg-red-500 blur-[50px] rounded-full opacity-60 mix-blend-screen pointer-events-none"></div>
          
          <div class="absolute top-6 right-6 z-20">
            <div class="px-3 py-1.5 bg-red-500/20 backdrop-blur-md border border-red-500/50 rounded-md text-[10px] font-bold text-white uppercase tracking-widest shadow-[0_0_15px_rgba(239,68,68,0.4)]">
              NISAR (L-Band)
            </div>
          </div>
        </div>

        <!-- Clipped Map: C-Band -->
        <div class="absolute inset-0 w-full h-full bg-[url('https://images.unsplash.com/photo-1524661135-423995f22d0b?q=80&w=2000&auto=format&fit=crop')] bg-cover bg-center brightness-[0.6] contrast-100 grayscale-[40%] border-r-2 border-white shadow-[2px_0_15px_rgba(255,255,255,0.3)]" :style="{ clipPath: `polygon(0 0, ${sliderPos}% 0, ${sliderPos}% 100%, 0 100%)` }">
          <!-- C-Band Water (Blue) -->
          <div class="absolute inset-0 bg-space-900/40 mix-blend-overlay"></div>
          <div class="absolute inset-0 flex items-center justify-center opacity-60 pointer-events-none">
            <div class="w-64 h-64 md:w-[500px] md:h-[500px] bg-accent-blue blur-[60px] md:blur-[100px] rounded-full"></div>
            <div class="absolute top-1/4 left-1/4 w-40 h-40 bg-accent-blue blur-[50px] rounded-full opacity-80"></div>
          </div>
          
          <div class="absolute top-6 left-6 z-20">
            <div class="px-3 py-1.5 bg-space-800/80 backdrop-blur-md border border-white/20 rounded-md text-[10px] font-bold text-white uppercase tracking-widest shadow-lg">
              OPERA (C-Band)
            </div>
          </div>
        </div>

        <!-- The Slider Handle -->
        <div class="absolute top-0 bottom-0 w-[2px] bg-white z-40 cursor-ew-resize flex items-center justify-center group" :style="{ left: `${sliderPos}%` }">
          <div class="absolute w-8 h-12 bg-space-900 border border-white/50 rounded flex items-center justify-center shadow-2xl group-hover:bg-space-800 group-hover:scale-110 transition-all">
            <div class="w-[1px] h-4 bg-white/50 mx-0.5"></div>
            <div class="w-[1px] h-4 bg-white/50 mx-0.5"></div>
          </div>
        </div>
      </div>
      
      <!-- Professional Floating Tools Map -->
      <div class="absolute bottom-24 md:bottom-6 right-6 z-30 flex flex-col gap-2">
        <button class="w-10 h-10 bg-space-900/90 backdrop-blur border border-white/10 rounded-lg flex items-center justify-center text-white hover:bg-space-800 transition-colors shadow-lg">
          <Plus class="w-4 h-4" />
        </button>
        <button class="w-10 h-10 bg-space-900/90 backdrop-blur border border-white/10 rounded-lg flex items-center justify-center text-white hover:bg-space-800 transition-colors shadow-lg">
          <Minus class="w-4 h-4" />
        </button>
        <button class="w-10 h-10 bg-space-900/90 backdrop-blur border border-white/10 rounded-lg flex items-center justify-center text-white hover:bg-space-800 transition-colors shadow-lg mt-2">
          <LocateFixed class="w-4 h-4" />
        </button>
      </div>

      <!-- Live Coordinates -->
      <div class="absolute bottom-4 right-20 md:right-24 z-30 flex gap-4 text-[9px] font-mono text-slate-400 bg-space-950/60 backdrop-blur px-2 py-1 rounded">
        <span>Lat: 22.8456° N</span>
        <span>Lon: 91.8021° E</span>
        <span>Zoom: 14z</span>
      </div>

      <!-- Professional Legend -->
      <div class="absolute bottom-6 left-6 z-30 bg-space-900/90 backdrop-blur-md border border-white/10 rounded-lg p-4 shadow-2xl hidden md:block">
        <h4 class="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-3">Detection Classifications</h4>
        <div class="space-y-2">
          <div class="flex items-center gap-3">
            <div class="w-3 h-3 rounded-sm bg-accent-blue shadow-[0_0_8px_rgba(56,189,248,0.6)]"></div>
            <span class="text-xs text-slate-300">Open Water (C-Band & L-Band Match)</span>
          </div>
          <div class="flex items-center gap-3">
            <div class="w-3 h-3 rounded-sm bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]"></div>
            <span class="text-xs text-white font-medium">Sub-Canopy Inundation (L-Band Only)</span>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Layers, X, Map as MapIcon, Satellite, Globe2, Mountain, AlertTriangle, Download, Plus, Minus, LocateFixed } from 'lucide-vue-next'

const sidebarOpen = ref(false)
const sliderPos = ref(50)
const mapContainerRef = ref(null)

const handleMouseMove = (e) => {
  if (e.buttons === 1 && mapContainerRef.value) { // Left click is held down
    const rect = mapContainerRef.value.getBoundingClientRect()
    const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width))
    sliderPos.value = (x / rect.width) * 100
  }
}

const handleTouchMove = (e) => {
  if (mapContainerRef.value && e.touches.length > 0) {
    const rect = mapContainerRef.value.getBoundingClientRect()
    const x = Math.max(0, Math.min(e.touches[0].clientX - rect.left, rect.width))
    sliderPos.value = (x / rect.width) * 100
  }
}
</script>

<style scoped>
.scrollbar-thin::-webkit-scrollbar {
  width: 4px;
}
.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}
.scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}
</style>
