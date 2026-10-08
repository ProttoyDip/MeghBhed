<template>
  <div class="relative w-full flex-grow flex flex-col items-center overflow-x-hidden">
    
    <!-- Hero Section (Elegant & Premium) -->
    <section class="relative w-full min-h-[90vh] flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 py-16 md:py-20 overflow-hidden">
      <!-- Dark minimal grid background -->
      <div class="absolute inset-0 bg-space-950 -z-20">
        <div class="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px]"></div>
        <div class="absolute left-0 right-0 top-0 -z-10 m-auto h-[310px] w-[310px] rounded-full bg-accent-blue/20 opacity-50 blur-[100px]"></div>
        <div class="absolute bottom-0 right-[-20%] -z-10 h-[400px] w-[400px] rounded-full bg-accent-teal/10 opacity-40 blur-[120px] mix-blend-screen"></div>
        <div class="absolute top-[20%] left-[-10%] -z-10 h-[300px] w-[300px] rounded-full bg-accent-blue/10 opacity-30 blur-[100px] mix-blend-screen"></div>
      </div>
      
      <!-- Realistic Radar Sweep Animation Background -->
      <div class="absolute inset-0 flex items-center justify-center opacity-30 pointer-events-none overflow-hidden z-0">
        <!-- Radar Grid Circles -->
        <div class="absolute w-[300px] h-[300px] md:w-[600px] md:h-[600px] rounded-full border border-accent-blue/10"></div>
        <div class="absolute w-[450px] h-[450px] md:w-[900px] md:h-[900px] rounded-full border border-accent-blue/10"></div>
        <div class="absolute w-[600px] h-[600px] md:w-[1200px] md:h-[1200px] rounded-full border border-accent-blue/10"></div>
        
        <!-- Radar Crosshairs -->
        <div class="absolute w-full h-[1px] bg-accent-blue/5"></div>
        <div class="absolute h-full w-[1px] bg-accent-blue/5"></div>
        
        <!-- Sweeping Beam (Double-sided) -->
        <div class="absolute w-[600px] h-[600px] md:w-[1200px] md:h-[1200px] rounded-full overflow-hidden" style="animation: radar-sweep 12s linear infinite;">
          <div class="absolute inset-0" style="background: conic-gradient(from 0deg at 50% 50%, transparent 0deg, transparent 120deg, rgba(56, 189, 248, 0.3) 180deg, transparent 180deg, transparent 300deg, rgba(56, 189, 248, 0.3) 360deg);"></div>
        </div>

        <!-- Radar Pings (Detected Objects) -->
        <div class="absolute top-[35%] left-[60%] w-3 h-3 bg-red-500 rounded-full shadow-[0_0_15px_rgba(239,68,68,1)]" style="animation: radar-ping 8s infinite; animation-delay: 1.5s;"></div>
        <div class="absolute top-[65%] left-[40%] w-2 h-2 bg-accent-teal rounded-full shadow-[0_0_10px_rgba(20,184,166,1)]" style="animation: radar-ping 8s infinite; animation-delay: 5.5s;"></div>
        <div class="absolute top-[25%] left-[30%] w-2.5 h-2.5 bg-accent-orange rounded-full shadow-[0_0_10px_rgba(249,115,22,1)]" style="animation: radar-ping 8s infinite; animation-delay: 7s;"></div>
      </div>
      
      <div class="relative z-10 text-center max-w-5xl mx-auto mt-8 md:mt-0 flex flex-col items-center">
        
        <!-- Elegant Status Badge -->
        <div class="mb-8 animate-fade-in-up">
          <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-space-800/80 border border-white/10 backdrop-blur-md shadow-[0_0_20px_rgba(0,0,0,0.5)] cursor-default group hover:border-accent-blue/50 transition-colors duration-500">
            <span class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-teal opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-accent-teal"></span>
            </span>
            <span class="text-[10px] md:text-[11px] font-semibold text-slate-300 tracking-[0.2em] uppercase group-hover:text-white transition-colors duration-300">Phase 1: Concept Build</span>
          </div>
        </div>
        
        <!-- Ultra-premium Typography -->
        <h1 class="text-6xl sm:text-7xl md:text-8xl lg:text-[7rem] font-black tracking-tighter mb-6 leading-[1.05] animate-fade-in-up" style="animation-delay: 0.1s;">
          <span class="block text-transparent bg-clip-text bg-gradient-to-r from-accent-teal via-accent-blue to-accent-orange animate-gradient-x mb-2 drop-shadow-lg">মেঘভেদ</span>
          <span class="block text-transparent bg-clip-text bg-gradient-to-br from-white via-slate-200 to-slate-500 pb-2">
            Piercing the Clouds
          </span>
        </h1>
        
        <p class="mt-6 text-xl sm:text-2xl md:text-3xl text-slate-300 font-medium max-w-4xl mx-auto leading-tight animate-fade-in-up" style="animation-delay: 0.2s;">
          See the flood the <span class="relative inline-block text-white">other maps
            <svg class="absolute w-full h-3 -bottom-1 left-0 text-red-500/80" viewBox="0 0 100 10" preserveAspectRatio="none">
              <path d="M0 5 Q 50 10 100 0" stroke="currentColor" stroke-width="2" fill="none" class="animate-dash" stroke-dasharray="100" stroke-dashoffset="0"/>
            </svg>
          </span> missed.
        </p>
        
        <p class="mt-6 md:mt-8 text-base md:text-lg text-slate-400 max-w-3xl mx-auto leading-relaxed px-2 animate-fade-in-up" style="animation-delay: 0.3s;">
          Using NASA–ISRO NISAR L-band radar to find flooded villages under tree cover that free C-band flood maps cannot see, and to count the people living there.
        </p>
        
        <!-- Refined CTAs -->
        <div class="mt-10 md:mt-12 flex flex-col sm:flex-row justify-center gap-4 w-full max-w-md mx-auto sm:max-w-none animate-fade-in-up" style="animation-delay: 0.4s;">
          <router-link to="/map" class="group relative px-8 py-3.5 rounded-xl bg-space-800 border border-white/10 hover:border-white/20 text-white font-bold text-base hover:bg-space-700 transition-all duration-300 flex items-center justify-center gap-3 w-full sm:w-auto hover:-translate-y-0.5">
            <Map class="w-5 h-5 text-accent-teal group-hover:scale-110 transition-transform duration-300 shrink-0" />
            <span>Launch Interactive Map</span>
          </router-link>
          
          <router-link to="/assistant" class="group relative px-8 py-3.5 rounded-xl bg-space-800 border border-white/10 hover:border-white/20 text-white font-bold text-base hover:bg-space-700 transition-all duration-300 flex items-center justify-center gap-3 w-full sm:w-auto hover:-translate-y-0.5">
            <Bot class="w-5 h-5 text-accent-blue group-hover:rotate-12 transition-transform duration-300 shrink-0" />
            <span>Talk to AI Assistant</span>
          </router-link>
        </div>
      </div>
      
      <!-- Minimalist Scroll Indicator -->
      <div class="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 opacity-50 hover:opacity-100 transition-opacity duration-300 cursor-pointer animate-pulse-slow">
        <div class="w-[1px] h-12 bg-gradient-to-b from-transparent via-slate-400 to-transparent"></div>
        <span class="text-[9px] font-bold tracking-[0.3em] text-slate-400 uppercase">Scroll</span>
      </div>
    </section>

    <!-- The Problem Section (Clean, Magazine Layout) -->
    <section class="w-full max-w-7xl mx-auto px-4 sm:px-6 py-24 md:py-32 relative">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
        <!-- Text Content -->
        <div class="lg:col-span-5 lg:col-start-1">
          <div class="inline-flex items-center gap-2 mb-6">
            <span class="w-8 h-[1px] bg-accent-orange"></span>
            <span class="text-xs font-bold text-accent-orange tracking-[0.2em] uppercase">The Flaw in Current Tech</span>
          </div>
          <h3 class="text-4xl md:text-5xl font-black text-white mb-6 leading-tight tracking-tight">Invisible Disasters</h3>
          <p class="text-slate-400 text-lg leading-relaxed mb-8">
            Free global flood maps rely on Sentinel-1's C-band radar. But C-band radar is scattered by dense vegetation leaves and branches. It <strong class="text-white font-semibold border-b border-accent-orange/30">largely misses water underneath the canopy.</strong>
          </p>
          
          <div class="flex gap-6">
            <div class="border-l-2 border-red-500/50 pl-4 py-1">
              <p class="text-3xl font-black text-white mb-1">1.28M</p>
              <p class="text-xs font-semibold text-slate-500 uppercase tracking-widest">People Affected</p>
            </div>
            <div class="border-l-2 border-red-500/50 pl-4 py-1">
              <p class="text-3xl font-black text-white mb-1">59</p>
              <p class="text-xs font-semibold text-slate-500 uppercase tracking-widest">Deaths</p>
            </div>
          </div>
          <p class="text-[10px] text-slate-600 mt-4 uppercase tracking-widest">Source: UN SitRep #2, July 2026</p>
        </div>

        <!-- Elegant Quote Card -->
        <div class="lg:col-span-6 lg:col-start-7 relative group">
          <div class="absolute -inset-1 bg-gradient-to-r from-accent-orange/10 to-transparent rounded-3xl blur transition duration-1000 group-hover:duration-200"></div>
          <div class="relative glass-panel p-10 md:p-12 rounded-3xl border border-white/5 bg-space-800/80 backdrop-blur-xl">
            <Quote class="w-12 h-12 text-accent-orange/20 mb-6" />
            <p class="text-xl md:text-2xl font-medium text-slate-200 leading-relaxed">
              "Relief teams plan with flood maps that <span class="text-red-400/90 font-semibold">cannot see</span> flooded villages under trees. Help goes where the map shows water, and families under the trees get missed."
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Moving Data Sources Marquee -->
    <section class="w-full py-10 md:py-14 border-y border-white/5 bg-space-900/50 overflow-hidden flex flex-col items-center">
      <p class="text-xs font-bold text-slate-500 uppercase tracking-widest mb-6 md:mb-8">Powered by World-Class Data</p>
      <div class="w-full relative flex overflow-hidden">
        <div class="absolute left-0 top-0 bottom-0 w-20 md:w-40 bg-gradient-to-r from-space-900 to-transparent z-10 pointer-events-none"></div>
        <div class="absolute right-0 top-0 bottom-0 w-20 md:w-40 bg-gradient-to-l from-space-900 to-transparent z-10 pointer-events-none"></div>
        <div class="flex animate-marquee whitespace-nowrap min-w-full hover:[animation-play-state:paused]">
          <div v-for="i in 2" :key="i" class="flex gap-12 md:gap-24 px-6 md:px-12 items-center">
            <span class="text-xl md:text-3xl font-black text-slate-700 hover:text-white transition-colors duration-300">NASA ISRO NISAR</span>
            <span class="text-xl md:text-3xl font-black text-slate-700 hover:text-white transition-colors duration-300">ESA Sentinel-1</span>
            <span class="text-xl md:text-3xl font-black text-slate-700 hover:text-white transition-colors duration-300">Copernicus DEM</span>
            <span class="text-xl md:text-3xl font-black text-slate-700 hover:text-white transition-colors duration-300">WorldPop 100m</span>
            <span class="text-xl md:text-3xl font-black text-slate-700 hover:text-white transition-colors duration-300">ESA WorldCover</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Bento Grid Features (Clean & Ultra-Premium) -->
    <section class="w-full bg-space-950 relative py-24 md:py-32 border-b border-white/5">
      <div class="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik00MCAwaC0xVjM5SDBWMGg0MnoiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4wMikiIGZpbGwtcnVsZT0iZXZlbm9kZCIvPgo8L3N2Zz4=')] mix-blend-overlay"></div>
      
      <div class="max-w-7xl mx-auto px-4 sm:px-6 relative z-10">
        <div class="text-center mb-16 md:mb-20">
          <div class="inline-flex items-center gap-2 mb-4">
            <span class="w-8 h-[1px] bg-accent-teal"></span>
            <span class="text-xs font-bold text-accent-teal tracking-[0.2em] uppercase">The Solution</span>
            <span class="w-8 h-[1px] bg-accent-teal"></span>
          </div>
          <h3 class="text-4xl md:text-5xl lg:text-6xl font-black text-white tracking-tight">Why L-Band Changes Everything</h3>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 md:auto-rows-[300px]">
          <!-- Large Feature Card -->
          <div class="md:col-span-2 md:row-span-2 relative group overflow-hidden rounded-3xl bg-space-800/50 border border-white/5 hover:border-white/10 transition-colors duration-500 flex flex-col justify-between">
            <!-- Subtle internal glow -->
            <div class="absolute top-0 right-0 w-96 h-96 bg-accent-teal/5 blur-[100px] rounded-full group-hover:bg-accent-teal/10 transition-colors duration-700"></div>
            
            <!-- Top Section: Data Plots & Stats -->
            <div class="relative p-8 md:p-10 pb-0 z-10 w-full flex flex-col sm:flex-row items-start sm:items-end justify-between gap-6">
              
              <div class="flex flex-col gap-4 w-full sm:w-auto">
                <div class="w-12 h-12 rounded-xl bg-space-700/50 border border-white/10 flex items-center justify-center text-accent-teal shadow-lg mb-2">
                  <Waves class="w-6 h-6" />
                </div>
                
                <!-- Live Stats Mini-dashboard -->
                <div class="grid grid-cols-2 gap-3 w-full sm:w-64">
                  <div class="bg-space-950/50 border border-white/5 p-3 rounded-xl">
                    <p class="text-[9px] text-slate-500 uppercase tracking-widest mb-1">Model Accuracy</p>
                    <div class="flex items-end gap-2">
                      <span class="text-xl font-black text-accent-teal">94.2</span><span class="text-xs text-slate-400 mb-1">%</span>
                    </div>
                    <div class="w-full h-1 bg-space-800 mt-2 rounded-full overflow-hidden">
                      <div class="h-full bg-accent-teal w-[94%]"></div>
                    </div>
                  </div>
                  
                  <div class="bg-space-950/50 border border-white/5 p-3 rounded-xl">
                    <p class="text-[9px] text-slate-500 uppercase tracking-widest mb-1">Data Confidence</p>
                    <div class="flex items-end gap-2">
                      <span class="text-xl font-black text-accent-blue">High</span>
                    </div>
                    <p class="text-[9px] text-accent-blue mt-1">Uncertainty &lt; 5%</p>
                  </div>
                </div>
              </div>

              <!-- Colorful Bar Chart Representation -->
              <div class="w-full sm:w-auto p-4 bg-space-950/30 border border-white/5 rounded-xl flex flex-col items-center gap-4">
                <p class="text-[9px] text-slate-500 uppercase tracking-widest w-full text-left">Signal Reflection Pattern</p>
                <div class="w-48 h-28 flex items-end justify-between gap-2 opacity-90 pb-2">
                  <div class="w-6 bg-gradient-to-t from-space-900 to-accent-blue rounded-t-sm h-[40%] animate-pulse-slow"></div>
                  <div class="w-6 bg-gradient-to-t from-space-900 to-accent-teal rounded-t-sm h-[65%] animate-pulse-slow" style="animation-delay: 0.2s"></div>
                  <div class="w-6 bg-gradient-to-t from-space-900 to-red-500 rounded-t-sm h-[90%] animate-pulse-slow shadow-[0_0_15px_rgba(239,68,68,0.5)]" style="animation-delay: 0.4s">
                    <div class="w-full h-full border-t-2 border-white/50"></div>
                  </div>
                  <div class="w-6 bg-gradient-to-t from-space-900 to-accent-orange rounded-t-sm h-[70%] animate-pulse-slow" style="animation-delay: 0.6s"></div>
                  <div class="w-6 bg-gradient-to-t from-space-900 to-accent-blue rounded-t-sm h-[50%] animate-pulse-slow" style="animation-delay: 0.8s"></div>
                </div>
                <div class="flex items-center gap-4 w-full justify-between px-2">
                  <span class="text-[9px] text-slate-500 font-mono">HV</span>
                  <span class="text-[10px] text-red-400 font-bold font-mono">HH Spike</span>
                  <span class="text-[9px] text-slate-500 font-mono">VH</span>
                </div>
              </div>
            </div>

            <!-- Bottom Section: Text -->
            <div class="relative p-8 md:p-10 z-10 max-w-2xl mt-4 md:mt-0">
              <h4 class="text-3xl md:text-4xl font-bold text-white mb-3">The Double Bounce Effect</h4>
              <p class="text-slate-400 text-base md:text-lg leading-relaxed font-medium">
                NISAR's ~24 cm L-band wavelength passes straight through the forest canopy. It reflects off the flat floodwater, hits the tree trunks, and bounces back to the satellite, revealing hidden floods with remarkable accuracy.
              </p>
            </div>
          </div>

          <!-- Small Feature Card 1 -->
          <div class="relative group rounded-3xl bg-space-800/50 border border-white/5 hover:border-white/10 transition-colors duration-500 p-8 flex flex-col">
            <div class="w-12 h-12 rounded-xl bg-space-700/50 border border-white/10 flex items-center justify-center text-accent-blue mb-auto shadow-lg">
              <Users class="w-6 h-6" />
            </div>
            <div>
              <h4 class="text-xl font-bold text-white mb-2">Counting People</h4>
              <p class="text-slate-400 text-sm leading-relaxed">Overlaying WorldPop 100m demographic data to quantify exactly how many lives are hidden beneath the canopy.</p>
            </div>
          </div>

          <!-- Small Feature Card 2 -->
          <div class="relative group rounded-3xl bg-space-800/50 border border-white/5 hover:border-white/10 transition-colors duration-500 p-8 flex flex-col">
            <div class="w-12 h-12 rounded-xl bg-space-700/50 border border-white/10 flex items-center justify-center text-accent-orange mb-auto shadow-lg">
              <Mountain class="w-6 h-6" />
            </div>
            <div>
              <h4 class="text-xl font-bold text-white mb-2">Hill Risk Layer</h4>
              <p class="text-slate-400 text-sm leading-relaxed">Combining Copernicus DEM, NASA IMERG rainfall, and LHASA models to flag potential landslide zones.</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Our Approach Workflow (Minimalist Timeline) -->
    <section class="w-full max-w-7xl mx-auto px-4 sm:px-6 py-24 md:py-32">
      <div class="text-center mb-16 md:mb-20">
        <h3 class="text-4xl md:text-5xl font-black text-white tracking-tight">How MeghBhed Works</h3>
      </div>
      
      <div class="relative w-full">
        <!-- Connecting Line -->
        <div class="hidden md:block absolute top-12 left-10 right-10 h-1 bg-space-800 rounded-full overflow-hidden">
          <div class="h-full w-full bg-gradient-to-r from-accent-blue via-accent-teal to-accent-orange animate-gradient-x opacity-50"></div>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 relative">
          <div v-for="(step, i) in workflow" :key="i" class="relative group p-6 rounded-2xl bg-space-800/30 backdrop-blur-xl border border-white/5 hover:bg-space-800/80 hover:border-white/10 transition-all duration-300 shadow-xl">
            <!-- Node dot -->
            <div class="hidden md:flex absolute -top-12 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-space-900 border-2 border-accent-blue shadow-[0_0_10px_rgba(56,189,248,0.8)] z-10 items-center justify-center">
              <div class="w-1 h-1 bg-white rounded-full"></div>
            </div>
            <div class="text-4xl font-black text-white/10 mb-3 group-hover:text-accent-blue/20 transition-colors duration-300">
              0{{ i + 1 }}
            </div>
            <h4 class="text-lg font-bold text-white mb-2">{{ step.title }}</h4>
            <p class="text-sm text-slate-400 leading-relaxed">{{ step.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Team Section (Clean Spotlight) -->
    <section class="w-full py-24 md:py-32 relative overflow-hidden bg-space-950 border-t border-white/5">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 relative z-10">
        <div class="text-center mb-16 md:mb-20">
          <h3 class="text-3xl md:text-5xl font-black text-white tracking-tight mb-4">Team Last_Call</h3>
          <p class="text-slate-500 font-medium tracking-widest uppercase text-xs">The Masterminds</p>
        </div>
        
        <div class="w-full relative flex overflow-hidden">
          <div class="absolute left-0 top-0 bottom-0 w-12 md:w-32 bg-gradient-to-r from-space-950 to-transparent z-10 pointer-events-none"></div>
          <div class="absolute right-0 top-0 bottom-0 w-12 md:w-32 bg-gradient-to-l from-space-950 to-transparent z-10 pointer-events-none"></div>
          <div class="flex animate-marquee whitespace-nowrap min-w-full hover:[animation-play-state:paused]">
            <div v-for="i in 2" :key="'team-'+i" class="flex items-center">
              <div v-for="(member, idx) in team" :key="member.name + i" class="flex flex-col items-center group mx-8 md:mx-12">
                <div class="w-28 h-28 md:w-40 md:h-40 mb-5 rounded-full p-1 bg-space-800 border-2 border-white/10 group-hover:border-accent-blue/50 transition-colors duration-500 overflow-hidden relative shadow-xl">
                  <template v-if="member.image">
                    <img :src="member.image" :alt="member.name" class="w-full h-full object-cover rounded-full transition-all duration-500 transform group-hover:scale-110" />
                  </template>
                  <template v-else>
                    <div class="w-full h-full rounded-full bg-space-900 flex items-center justify-center">
                      <component :is="member.icon" class="w-10 h-10 text-slate-400 group-hover:text-accent-blue transition-colors duration-500" />
                    </div>
                  </template>
                </div>
                
                <div class="text-center">
                  <h4 class="text-base md:text-lg font-bold text-white mb-1 leading-tight">{{ member.name }}</h4>
                  <p class="text-[10px] md:text-[11px] text-accent-teal font-semibold uppercase tracking-widest">{{ member.role }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { Map, ArrowRight, Quote, Waves, Users, Mountain, Bot, Database, Code2, BrainCircuit, Mic2, Compass } from 'lucide-vue-next'

const workflow = [
  { title: "Before & During", desc: "Take NISAR L2 GCOV scenes from the same orbit track before and during the floods." },
  { title: "Water Under Trees", desc: "Look inside ESA WorldCover tree pixels. Flag HH double-bounce increases without HV rise." },
  { title: "Compare with C-Band", desc: "Overlay NASA OPERA DSWx-S1 and apply a fair-comparison rule to find missing flood data." },
  { title: "Count The People", desc: "Sum the hidden-flood area and WorldPop 100m population data for each upazila." }
]

const team = [
  { name: 'Prottoy Saha Dip', role: 'GIS & Radar', icon: Compass, image: '/dip.jpg' },
  { name: 'Md. Thouhidul Islam', role: 'Data Analytics', icon: Database, image: '/apurbo.jpg' },
  { name: 'S.M. Sao.Mio Rashid Sakin', role: 'Backend & AI', icon: BrainCircuit, image: '/sakin.jpg' },
  { name: 'Shuvo Singh Partho', role: 'AI ML & Full Stack', icon: Code2, image: '/partho.jpg' },
  { name: 'Eva Jahan', role: 'Data Collection', icon: Users, image: '/eva.jpg' },
  { name: 'Suchismita Sarker', role: 'Design & Pitch', icon: Mic2, image: '/suchi.jpg' }
]
</script>

<style scoped>
/* Ultra-premium smooth drawing of the curved line under text */
@keyframes dash {
  to {
    stroke-dashoffset: 100;
  }
}
.animate-dash {
  animation: dash 2s cubic-bezier(0.4, 0, 0.2, 1) forwards;
  animation-delay: 1s;
}
</style>
