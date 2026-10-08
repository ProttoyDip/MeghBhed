<template>
  <div class="min-h-screen bg-space-900 text-slate-200 font-sans relative flex flex-col selection:bg-accent-blue/30 selection:text-white">
    <!-- Dynamic Ambient Background -->
    <div class="fixed inset-0 overflow-hidden pointer-events-none z-0">
      <div class="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] bg-accent-blue/10 rounded-full blur-[150px] mix-blend-screen animate-blob"></div>
      <div class="absolute top-[20%] -right-[10%] w-[40%] h-[60%] bg-accent-teal/5 rounded-full blur-[150px] mix-blend-screen animate-blob animation-delay-2000"></div>
      <div class="absolute -bottom-[20%] left-[20%] w-[60%] h-[50%] bg-accent-orange/5 rounded-full blur-[150px] mix-blend-screen animate-blob animation-delay-4000"></div>
      
      <!-- Subtle Grid Pattern -->
      <div class="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik00MCAwaC0xVjM5SDBWMGg0MnoiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4wMykiIGZpbGwtcnVsZT0iZXZlbm9kZCIvPgo8L3N2Zz4=')] opacity-30"></div>
    </div>

    <!-- Advanced Navbar -->
    <nav class="fixed top-0 left-0 w-full z-50 transition-all duration-500" :class="{ 'glass py-2 md:py-3 shadow-2xl': scrolled, 'bg-transparent py-4 md:py-5': !scrolled }">
      <div class="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8">
        <div class="relative flex items-center justify-between h-14 md:h-16">
          
          <!-- Left: Logo -->
          <div class="flex items-center gap-2 md:gap-3 cursor-pointer group shrink-0" @click="$router.push('/')">
            <div class="w-8 h-8 md:w-10 md:h-10 shrink-0 rounded-xl bg-gradient-to-br from-accent-blue to-accent-teal p-[1px] group-hover:shadow-[0_0_20px_rgba(56,189,248,0.5)] transition-all duration-300">
              <div class="w-full h-full rounded-xl bg-space-900 flex items-center justify-center">
                <Satellite class="w-4 h-4 md:w-5 md:h-5 text-accent-blue" />
              </div>
            </div>
            <div class="flex items-center gap-2">
              <h1 class="text-xl md:text-2xl font-black text-white tracking-tight group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-accent-teal group-hover:to-accent-blue transition-all duration-300">
                MeghBhed
              </h1>
            </div>
          </div>

          <!-- Center: Navigation (Absolute Center for Desktop) -->
          <div class="hidden lg:flex absolute left-1/2 -translate-x-1/2 items-center bg-space-800/80 backdrop-blur-xl border border-white/10 rounded-full p-1 shadow-[0_0_30px_rgba(0,0,0,0.5)] z-20">
            <router-link
              v-for="item in navItems"
              :key="item.name"
              :to="item.path"
              class="relative px-3 xl:px-5 py-2 rounded-full text-[13px] xl:text-sm font-medium transition-all duration-300 flex items-center gap-1.5 xl:gap-2.5 group whitespace-nowrap"
              active-class="text-white"
              :class="$route.path === item.path ? 'text-white' : 'text-slate-400 hover:text-white'"
            >
              <!-- Active Pill Background -->
              <div v-if="$route.path === item.path" class="absolute inset-0 bg-gradient-to-r from-white/10 to-white/5 rounded-full -z-10 shadow-inner border border-white/10"></div>
              
              <component :is="item.icon" class="w-3.5 h-3.5 xl:w-4 xl:h-4 transition-transform duration-300" :class="$route.path === item.path ? 'text-accent-blue scale-110 drop-shadow-[0_0_8px_rgba(56,189,248,0.8)]' : 'group-hover:text-accent-teal group-hover:scale-110'" />
              <span>{{ item.name }}</span>
            </router-link>
          </div>

          <!-- Right: Actions & Mobile Toggle -->
          <div class="flex items-center justify-end gap-2 xl:gap-3 shrink-0 z-10">
            
            <!-- Live Status Ticker -->
            <div class="hidden xl:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-accent-orange/10 border border-accent-orange/20 shadow-[0_0_15px_rgba(249,115,22,0.15)] group cursor-default">
              <span class="w-1.5 h-1.5 rounded-full bg-accent-orange animate-pulse shrink-0"></span>
              <span class="text-[10px] font-bold text-accent-orange tracking-wide group-hover:text-white transition-colors whitespace-nowrap">Live: Sentinel Pass in 2h</span>
            </div>

            <!-- Language Toggle -->
            <button class="hidden lg:flex items-center gap-1.5 px-2.5 py-1.5 rounded-full bg-space-800 border border-white/10 text-white font-bold text-[10px] hover:bg-space-700 transition-colors shrink-0">
              <Globe class="w-3.5 h-3.5 text-slate-400" />
              <span class="whitespace-nowrap">EN / বাং</span>
            </button>

            <!-- Get Started Button -->
            <button class="hidden lg:flex items-center gap-2 px-4 py-2 rounded-full bg-white text-space-900 font-bold text-[13px] hover:scale-105 hover:bg-gradient-to-r hover:from-white hover:to-slate-200 hover:shadow-[0_0_25px_rgba(255,255,255,0.4)] transition-all duration-300 shrink-0 whitespace-nowrap">
              Get Started
            </button>
            
            <!-- Mobile menu button -->
            <button @click="mobileMenuOpen = !mobileMenuOpen" class="lg:hidden p-2 rounded-xl bg-space-800 border border-white/10 text-white hover:bg-space-700 transition-colors shrink-0">
              <Menu v-if="!mobileMenuOpen" class="w-5 h-5" />
              <X v-else class="w-5 h-5" />
            </button>
          </div>
          
        </div>
      </div>
      
      <!-- Mobile Menu Overlay & Dropdown -->
      <transition name="fade">
        <div v-if="mobileMenuOpen" class="md:hidden fixed inset-0 top-[72px] bg-space-950/80 backdrop-blur-md z-40" @click="mobileMenuOpen = false"></div>
      </transition>

      <transition name="slide-down">
        <div v-if="mobileMenuOpen" class="md:hidden absolute top-full left-0 w-full bg-space-900/95 backdrop-blur-2xl border-b border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.5)] py-6 px-4 flex flex-col gap-3 z-50">
          
          <div class="flex items-center gap-2 px-4 py-3 mb-2 rounded-xl bg-accent-orange/10 border border-accent-orange/20 w-full">
            <span class="w-2 h-2 rounded-full bg-accent-orange animate-pulse"></span>
            <span class="text-xs font-bold text-accent-orange tracking-wide">Live: Sentinel Pass in 2h</span>
          </div>

          <router-link
            v-for="item in navItems"
            :key="item.name"
            :to="item.path"
            @click="mobileMenuOpen = false"
            class="px-5 py-4 rounded-xl text-base font-semibold flex items-center gap-4 transition-all duration-300"
            :class="$route.path === item.path ? 'bg-gradient-to-r from-accent-blue/20 to-accent-teal/10 text-white border border-accent-blue/30 shadow-[0_0_15px_rgba(56,189,248,0.2)]' : 'text-slate-300 hover:bg-space-800'"
          >
            <component :is="item.icon" class="w-6 h-6" :class="$route.path === item.path ? 'text-accent-blue' : ''" />
            {{ item.name }}
          </router-link>
          
          <div class="w-full h-px bg-gradient-to-r from-transparent via-white/10 to-transparent my-3"></div>
          
          <a href="https://github.com/ProttoyDip/MeghBhed" target="_blank" @click="mobileMenuOpen = false" class="px-5 py-4 rounded-xl text-base font-semibold flex items-center gap-4 text-slate-300 hover:bg-space-800 transition-colors">
            <Github class="w-6 h-6" />
            GitHub Repository
          </a>
        </div>
      </transition>
    </nav>

    <!-- Main Content -->
    <main class="pt-20 md:pt-24 flex-grow relative z-10 flex flex-col">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    
    <!-- Premium Footer -->
    <footer class="relative z-10 mt-auto overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-t from-space-900 via-space-900/90 to-transparent pointer-events-none"></div>
      <div class="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12 relative z-10 border-t border-white/5">
        <div class="flex flex-col md:flex-row items-center justify-between gap-4 md:gap-6 text-center md:text-left">
          <div class="flex items-center gap-3">
            <p class="text-xs md:text-sm text-slate-400 font-medium flex items-center gap-1.5">
              Made with <Heart class="w-4 h-4 text-red-500 fill-red-500 animate-pulse-slow" /> by <span class="text-white font-bold tracking-wide">Team Last_Call</span>
            </p>
          </div>
          <div class="flex flex-wrap justify-center md:justify-end items-center gap-4 md:gap-8 text-xs md:text-sm font-semibold text-slate-500">
            <a href="#" class="hover:text-white transition-colors">Methodology</a>
            <a href="#" class="hover:text-white transition-colors">Data Sources</a>
            <a href="https://www.spaceappschallenge.org/2026/" target="_blank" class="text-accent-orange/80 hover:text-accent-orange transition-colors">NASA Space Apps 2026</a>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Map, BarChart3, Bot, Home, Satellite, Github, Rocket, Menu, X, Heart, Globe } from 'lucide-vue-next'

const scrolled = ref(false)
const mobileMenuOpen = ref(false)

const handleScroll = () => {
  scrolled.value = window.scrollY > 20
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

const navItems = [
  { name: 'Overview', path: '/', icon: Home },
  { name: 'Analysis Map', path: '/map', icon: Map },
  { name: 'Insights', path: '/statistics', icon: BarChart3 },
  { name: 'AI Assistant', path: '/assistant', icon: Bot },
]
</script>

<style>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  transform-origin: top;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: scaleY(0.95) translateY(-10px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
