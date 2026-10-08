<template>
  <div class="w-full flex-grow relative overflow-hidden bg-space-950 font-sans">
    
    <!-- Subtle Grid Background -->
    <div class="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none"></div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-16 relative z-10 animate-fade-in">
      
      <!-- Dashboard Header -->
      <div class="flex flex-col lg:flex-row items-start lg:items-end justify-between mb-10 md:mb-12 gap-6">
        <div>
          <div class="inline-flex items-center gap-2 mb-4">
            <div class="w-2 h-2 rounded-full bg-accent-teal animate-pulse"></div>
            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-[0.2em]">Live Analytics Dashboard</span>
          </div>
          <h2 class="text-4xl md:text-5xl font-black text-white tracking-tight mb-2">Impact Insights</h2>
          <p class="text-slate-400 text-sm md:text-base">
            Demographic impact analysis combining NISAR L-band flood masks with WorldPop 100m data.
          </p>
        </div>
        
        <div class="flex gap-3 w-full lg:w-auto">
          <button @click="downloadMockup('CSV')" class="flex-1 lg:flex-none flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-space-900 border border-white/10 hover:border-accent-teal/50 text-xs font-bold text-white transition-all shadow-lg hover:shadow-[0_0_15px_rgba(20,184,166,0.2)]">
            <FileSpreadsheet class="w-4 h-4 text-accent-teal" /> Export CSV
          </button>
          <button @click="downloadMockup('KML')" class="flex-1 lg:flex-none flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-space-900 border border-white/10 hover:border-accent-blue/50 text-xs font-bold text-white transition-all shadow-lg hover:shadow-[0_0_15px_rgba(56,189,248,0.2)]">
            <Globe class="w-4 h-4 text-accent-blue" /> Export KML
          </button>
        </div>
      </div>

      <!-- Advanced KPI Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6 mb-10 md:mb-12">
        <!-- Missed Population KPI -->
        <div class="p-6 md:p-8 rounded-2xl bg-space-900/80 border border-white/5 relative overflow-hidden group hover:border-red-500/30 transition-colors duration-500">
          <div class="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-opacity duration-500">
            <Users class="w-24 h-24 text-red-500" />
          </div>
          <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">Total Missed Population</p>
          <div class="flex items-end gap-3 mb-4">
            <p class="text-5xl font-black text-white tracking-tighter">142,500</p>
          </div>
          <div class="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-red-500/10 border border-red-500/20 text-[10px] font-bold text-red-400 uppercase tracking-wider">
            <TrendingUp class="w-3 h-3" /> Hidden from C-Band
          </div>
        </div>
        
        <!-- Hidden Flood Area KPI -->
        <div class="p-6 md:p-8 rounded-2xl bg-space-900/80 border border-white/5 relative overflow-hidden group hover:border-accent-teal/30 transition-colors duration-500">
          <div class="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-opacity duration-500">
            <Map class="w-24 h-24 text-accent-teal" />
          </div>
          <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">Total Hidden Flood Area</p>
          <div class="flex items-baseline gap-2 mb-4">
            <p class="text-5xl font-black text-white tracking-tighter">34.2</p>
            <p class="text-lg font-bold text-slate-500">km²</p>
          </div>
          <div class="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-accent-teal/10 border border-accent-teal/20 text-[10px] font-bold text-accent-teal uppercase tracking-wider">
            <Trees class="w-3 h-3" /> Under dense canopy
          </div>
        </div>
        
        <!-- Hill Risk Zones KPI -->
        <div class="p-6 md:p-8 rounded-2xl bg-space-900/80 border border-white/5 relative overflow-hidden group hover:border-accent-orange/30 transition-colors duration-500">
          <div class="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-opacity duration-500">
            <AlertTriangle class="w-24 h-24 text-accent-orange" />
          </div>
          <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">High Risk Landslide Zones</p>
          <div class="flex items-baseline gap-2 mb-4">
            <p class="text-5xl font-black text-white tracking-tighter">12</p>
            <p class="text-lg font-bold text-slate-500">sites</p>
          </div>
          <div class="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-accent-orange/10 border border-accent-orange/20 text-[10px] font-bold text-accent-orange uppercase tracking-wider">
            <ShieldAlert class="w-3 h-3" /> Immediate Review
          </div>
        </div>
      </div>

      <!-- Main Data Dashboard -->
      <div class="rounded-2xl bg-space-900/50 border border-white/5 overflow-hidden backdrop-blur-sm">
        
        <!-- Toolbar -->
        <div class="p-5 border-b border-white/5 flex flex-col sm:flex-row justify-between items-center gap-4 bg-space-900">
          <div class="flex items-center gap-3">
            <h3 class="text-base font-bold text-white">Upazila Breakdown</h3>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-white/10 text-slate-300">Top 5</span>
          </div>
          <div class="relative w-full sm:w-64">
            <Search class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input type="text" placeholder="Filter regions..." class="w-full bg-space-950 border border-white/10 rounded-lg pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-accent-blue/50 transition-colors" />
          </div>
        </div>

        <!-- Table -->
        <div class="overflow-x-auto">
          <table class="w-full text-left whitespace-nowrap">
            <thead class="bg-space-950/50 border-b border-white/5 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
              <tr>
                <th class="px-6 py-4">Region</th>
                <th class="px-6 py-4">Hidden Area (km²)</th>
                <th class="px-6 py-4">Est. Missed Population</th>
                <th class="px-6 py-4 text-right">Data Confidence</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/5">
              <tr v-for="(row, i) in mockData" :key="i" class="hover:bg-space-800/50 transition-colors">
                <td class="px-6 py-5">
                  <p class="font-bold text-white text-sm">{{ row.upazila }}</p>
                  <p class="text-slate-500 text-[10px] mt-1">{{ row.district }}</p>
                </td>
                <td class="px-6 py-5 w-[30%]">
                  <div class="flex flex-col gap-1.5">
                    <span class="font-bold text-sm text-slate-300">{{ row.area }} <span class="text-xs text-slate-500 font-normal">km²</span></span>
                    <div class="w-full h-1.5 bg-space-950 rounded-full overflow-hidden">
                      <div class="h-full bg-accent-teal rounded-full" :style="`width: ${(row.area/6)*100}%`"></div>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-5">
                  <span class="text-lg font-black text-white">{{ row.population.toLocaleString() }}</span>
                  <span class="text-xs text-slate-500 ml-1">people</span>
                </td>
                <td class="px-6 py-5 text-right">
                  <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded border text-[9px] font-bold uppercase tracking-wider" 
                        :class="row.conf.includes('high') || row.conf.includes('missed by C-band') ? 'bg-accent-blue/5 text-accent-blue border-accent-blue/20' : 'bg-accent-orange/5 text-accent-orange border-accent-orange/20'">
                    <ShieldCheck v-if="row.conf.includes('high') || row.conf.includes('missed by C-band')" class="w-3.5 h-3.5" />
                    <AlertTriangle v-else class="w-3.5 h-3.5" />
                    {{ row.conf }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    
    <!-- Dummy Download Toast -->
    <div v-if="showToast" class="fixed bottom-6 right-6 z-50 animate-fade-in-up bg-space-800 border border-accent-teal/50 text-white px-5 py-3 rounded-lg shadow-2xl flex items-center gap-3">
      <CheckCircle2 class="w-5 h-5 text-accent-teal" />
      <span class="font-medium text-sm">Exporting {{ toastFormat }} data...</span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { FileSpreadsheet, Globe, TrendingUp, Trees, AlertTriangle, Search, ShieldCheck, CheckCircle2, Users, Map, ShieldAlert } from 'lucide-vue-next'

const showToast = ref(false)
const toastFormat = ref('')

const downloadMockup = (format) => {
  toastFormat.value = format
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 3000)
}

const mockData = [
  { upazila: 'Fatikchhari', district: 'Chattogram', area: 5.2, population: 24500, conf: 'Likely flooded (high confidence)' },
  { upazila: 'Hathazari', district: 'Chattogram', area: 3.8, population: 18200, conf: 'Likely missed by C-band' },
  { upazila: 'Parshuram', district: 'Feni', area: 4.1, population: 15100, conf: 'Possibly flooded' },
  { upazila: 'Chhagalnaiya', district: 'Feni', area: 2.9, population: 12400, conf: 'Likely flooded (high confidence)' },
  { upazila: 'Fulgazi', district: 'Feni', area: 3.5, population: 16800, conf: 'Possibly flooded' },
]
</script>
