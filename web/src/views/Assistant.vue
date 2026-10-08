<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-10 h-[calc(100vh-80px)] md:h-[calc(100vh-100px)] flex flex-col animate-fade-in relative bg-space-950 font-sans">
    
    <!-- Ultra-subtle grid background -->
    <div class="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none"></div>

    <!-- Header Area -->
    <div class="text-center mb-6 md:mb-8 relative z-10 shrink-0">
      <div class="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-space-900 border border-accent-blue/30 shadow-[0_0_20px_rgba(56,189,248,0.15)] mb-4">
        <Bot class="w-6 h-6 text-accent-blue" />
      </div>
      <h2 class="text-2xl md:text-3xl font-black text-white mb-2 tracking-tight">MeghBhed Copilot</h2>
      <p class="text-slate-400 text-xs md:text-sm max-w-lg mx-auto">
        Query the NISAR L-band flood database in natural language.
      </p>
    </div>

    <!-- Main Chat Window -->
    <div class="flex-grow flex flex-col overflow-hidden mb-4 relative z-10 bg-space-900/50 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl">
      
      <!-- Messages Area -->
      <div class="flex-grow overflow-y-auto p-4 md:p-8 space-y-6 md:space-y-8 scrollbar-thin">
        
        <!-- Welcome Message -->
        <div class="flex gap-4">
          <div class="w-8 h-8 rounded-lg bg-accent-blue/10 border border-accent-blue/30 flex-shrink-0 flex items-center justify-center text-accent-blue">
            <Sparkles class="w-4 h-4" />
          </div>
          <div class="pt-1">
            <p class="text-sm md:text-base text-slate-300 leading-relaxed font-medium">System initialized. Connected to <code class="text-accent-teal text-xs bg-space-800 px-1 py-0.5 rounded border border-white/5">stats.json</code> offline database.</p>
            
            <div class="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button @click="sendMessage('Which upazila has the highest missed population?')" class="text-left p-3 rounded-xl bg-space-800/50 border border-white/5 hover:border-accent-blue/40 hover:bg-space-800 transition-colors group">
                <p class="text-xs text-slate-400 mb-1 flex items-center gap-1.5"><MessageSquare class="w-3 h-3 group-hover:text-accent-blue transition-colors" /> Example Query</p>
                <p class="text-sm font-semibold text-white leading-tight">Which upazila has the highest missed population?</p>
              </button>
              
              <button @click="sendMessage('ফটিকছড়িতে কত মানুষ বন্যাকবলিত?')" class="text-left p-3 rounded-xl bg-space-800/50 border border-white/5 hover:border-accent-blue/40 hover:bg-space-800 transition-colors group">
                <p class="text-xs text-slate-400 mb-1 flex items-center gap-1.5"><MessageSquare class="w-3 h-3 group-hover:text-accent-blue transition-colors" /> Example Query</p>
                <p class="text-sm font-semibold text-white leading-tight">ফটিকছড়িতে কত মানুষ বন্যাকবলিত?</p>
              </button>
            </div>
          </div>
        </div>
        
        <!-- Chat History -->
        <div v-for="(msg, idx) in messages" :key="idx" class="flex gap-4 animate-fade-in-up" :class="msg.role === 'user' ? 'flex-row-reverse' : ''">
          
          <!-- Avatar -->
          <div class="w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center shadow-md"
               :class="msg.role === 'user' ? 'bg-space-800 border border-white/10 text-slate-400' : 'bg-accent-blue/10 border border-accent-blue/30 text-accent-blue'">
            <User v-if="msg.role === 'user'" class="w-4 h-4" />
            <Bot v-else class="w-4 h-4" />
          </div>
          
          <!-- Message Content -->
          <div class="pt-1 max-w-[85%] md:max-w-[75%]" :class="msg.role === 'user' ? 'text-right' : ''">
            <div class="inline-block" :class="msg.role === 'user' ? 'bg-space-800 border border-white/10 rounded-2xl rounded-tr-sm px-4 py-3' : ''">
              <!-- If Assistant, render rich HTML -->
              <template v-if="msg.role === 'assistant'">
                
                <!-- Typing Status -->
                <div v-if="msg.isTyping" class="flex items-center gap-2 text-xs text-accent-blue font-mono">
                  <div class="w-1.5 h-1.5 bg-accent-blue rounded-full animate-bounce"></div>
                  <div class="w-1.5 h-1.5 bg-accent-blue rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                  <div class="w-1.5 h-1.5 bg-accent-blue rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                  <span class="ml-2">Querying NISAR database...</span>
                </div>
                
                <!-- Completed Response -->
                <div v-else>
                  <div class="text-sm md:text-base text-slate-300 leading-relaxed font-medium" v-html="msg.content"></div>
                  
                  <div class="mt-3 flex items-center gap-3">
                    <span class="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-space-950 border border-white/10 text-[9px] font-bold text-slate-500 uppercase">
                      <CheckCircle2 class="w-3 h-3 text-accent-teal" /> Verified
                    </span>
                    <span class="text-[9px] text-slate-600 font-mono">24ms response</span>
                  </div>
                </div>
              </template>
              
              <!-- If User -->
              <p v-else class="text-sm md:text-base text-white font-medium">{{ msg.content }}</p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Input Box Area -->
      <div class="p-4 border-t border-white/5 bg-space-950/50 shrink-0">
        <form @submit.prevent="submitForm" class="relative flex items-center w-full">
          <input 
            type="text" 
            v-model="inputText"
            :disabled="isWaiting"
            placeholder="Ask Copilot..." 
            class="w-full bg-space-900 border border-white/10 rounded-xl py-3.5 pl-4 pr-12 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-accent-blue/50 transition-colors disabled:opacity-50"
          >
          <button type="submit" :disabled="isWaiting || !inputText.trim()" class="absolute right-2 p-2 rounded-lg bg-white/5 hover:bg-white/10 text-white transition-colors disabled:opacity-30">
            <Send class="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Bot, User, Send, MessageSquare, Sparkles, CheckCircle2 } from 'lucide-vue-next'

const inputText = ref('')
const isWaiting = ref(false)
const messages = ref([])

const dummyResponses = {
  "Which upazila has the highest missed population?": `Based on the latest cross-reference of L-band backscatter against C-band maps, <strong class="text-white">Fatikchhari upazila</strong> shows the highest discrepancy.<br><br>
  <div class="mt-3 p-3 bg-space-950 border border-white/10 rounded-lg flex items-center justify-between">
    <div>
      <span class="text-[10px] text-slate-500 uppercase tracking-wider block mb-1">Missed Population</span>
      <span class="text-lg font-black text-accent-teal">24,500</span>
    </div>
    <div class="text-right">
      <span class="text-[10px] text-slate-500 uppercase tracking-wider block mb-1">Hidden Area</span>
      <span class="text-lg font-black text-white">5.2 km²</span>
    </div>
  </div>`,
  "ফটিকছড়িতে কত মানুষ বন্যাকবলিত?": `আমাদের L-band রাডার ডেটা অনুযায়ী, <strong class="text-white">ফটিকছড়ি</strong> উপজেলায় গাছপালার নিচে আনুমানিক <strong class="text-accent-orange">২৪,৫০০</strong> মানুষ বন্যাকবলিত, যা সাধারণ C-band ম্যাপ ডিটেক্ট করতে পারেনি।`
}

const submitForm = () => {
  if (!inputText.value.trim() || isWaiting.value) return
  sendMessage(inputText.value)
}

const sendMessage = (text) => {
  if (isWaiting.value) return
  
  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  isWaiting.value = true
  
  // Add typing indicator
  messages.value.push({ role: 'assistant', content: '', isTyping: true })
  
  setTimeout(() => {
    messages.value.pop()
    const response = dummyResponses[text] || `I am operating in offline concept mode. For this demonstration, please try clicking one of the suggested queries.`
    messages.value.push({ role: 'assistant', content: response })
    isWaiting.value = false
  }, 1200)
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
