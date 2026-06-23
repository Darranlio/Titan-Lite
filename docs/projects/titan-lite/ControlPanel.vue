<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const batchStatus = ref('')
const singleStatus = ref('')
const ticker = ref('')
const analysisMode = ref('solo')
const loadingBatch = ref(false)
const loadingSingle = ref(false)

// --- Phase 4.2: Auto-Suggestion ---
const suggestions = ref([])
const showSuggestions = ref(false)

let searchTimeout = null
const handleSearch = async () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  if (!ticker.value || ticker.value.length < 1) {
    suggestions.value = []
    showSuggestions.value = false
    return
  }
  
  searchTimeout = setTimeout(async () => {
    try {
      const res = await fetch(`${API_BASE}/search?q=${ticker.value}`)
      const data = await res.json()
      suggestions.value = Array.isArray(data) ? data : []
      showSuggestions.value = suggestions.value.length > 0
    } catch (e) {
      suggestions.value = []
      showSuggestions.value = false
    }
  }, 200)
}

const selectTicker = (s) => {
  ticker.value = s.symbol
  showSuggestions.value = false
  runSingleAnalysis()
}

// --- Phase 4.1: Real-time Feedback ---
const logs = ref([])
const currentStage = ref('Idle')
const progress = ref(0)
const currentTaskType = ref('none')
let timer = null

const API_BASE = typeof window !== 'undefined' 
  ? `${window.location.protocol}//${window.location.hostname}:8000` 
  : 'http://localhost:8000'

const fetchLogs = async () => {
  try {
    const token = localStorage.getItem('titan_token')
    const res = await fetch(`${API_BASE}/logs?type=${currentTaskType.value}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    logs.value = data.logs
    currentStage.value = data.stage
    progress.value = data.progress
    
    // --- Phase 4.3: Auto-reset Loading State ---
    if (data.stage === 'Completed' || (data.progress === 100 && data.stage === 'Idle')) {
      if (loadingSingle.value || loadingBatch.value) {
        if (loadingSingle.value) singleStatus.value = `✅ ${ticker.value.toUpperCase()} 研判完成！`
        if (loadingBatch.value) batchStatus.value = `✅ 全市场扫描完成！`
        
        loadingSingle.value = false
        loadingBatch.value = false
        setTimeout(stopPolling, 5000) // 保持轮询一会儿看结果，然后停止
      }
    }
  } catch (e) {}
}

const startPolling = () => {
  if (timer) clearInterval(timer)
  timer = setInterval(fetchLogs, 1500)
}

const stopPolling = () => {
  if (timer) clearInterval(timer)
}

const runBatchAnalysis = async () => {
  loadingBatch.value = true
  batchStatus.value = '正在启动全市场深度扫描...'
  currentTaskType.value = 'batch'
  startPolling()
  try {
    const token = localStorage.getItem('titan_token')
    await fetch(`${API_BASE}/run`, { 
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}` 
      },
      body: JSON.stringify({ market: 'Global', mode: 'solo' })
    })
    batchStatus.value = '✅ 批量扫描已触发！'
  } catch (error) {
    batchStatus.value = '❌ 启动失败'
  } finally {
    loadingBatch.value = false
    // 批量扫描耗时极长，建议持续轮询直至完成或手动停止
  }
}

const runSingleAnalysis = async () => {
  if (!ticker.value) return
  
  // 立即清理本地状态，防止历史遗留日志闪烁
  logs.value = []
  progress.value = 0
  currentStage.value = 'Initializing'
  
  loadingSingle.value = true
  singleStatus.value = `正在针对 ${ticker.value} 进行研判...`
  currentTaskType.value = 'single'
  startPolling()
  try {
    const token = localStorage.getItem('titan_token')
    const response = await fetch(`${API_BASE}/analyze/${ticker.value.toUpperCase()}?mode=${analysisMode.value}`, { 
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await response.json()
    if (data.status === 'started') {
      singleStatus.value = `研判中: ${ticker.value.toUpperCase()}`
    }
  } catch (error) {
    singleStatus.value = '❌ 通信失败'
    loadingSingle.value = false
  }
}

const stopAnalysis = async () => {
  try {
    const token = localStorage.getItem('titan_token')
    await fetch(`${API_BASE}/stop`, { 
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    singleStatus.value = '🛑 已手动终止'
    batchStatus.value = ''
    loadingSingle.value = false
    loadingBatch.value = false
    setTimeout(stopPolling, 2000)
  } catch (e) {
    alert("停止指令发送失败")
  }
}

const handleClickOutside = (e) => {
  if (!e.target.closest('.search-container')) {
    showSuggestions.value = false
  }
}

onMounted(() => {
  window.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  stopPolling()
  window.removeEventListener('click', handleClickOutside)
})
</script>

<template>
<div class="control-center">
  <div class="dashboard-container">
    <div class="card batch-card">
      <div class="icon">🌍</div>
      <h3>全市场深度扫描</h3>
      <p>初筛 -> 快筛 -> 深研全链路执行。</p>
      <button @click="runBatchAnalysis" :disabled="loadingBatch" class="btn batch-btn">
        {{ loadingBatch ? '执行中...' : '开始全市场扫描' }}
      </button>
      <p v-if="batchStatus" class="status">{{ batchStatus }}</p>
    </div>

    <div class="card single-card">
      <div class="icon">🎯</div>
      <h3>个股专项研判</h3>
      <p>直接对指定标的启动 Titan-Alpha 引擎。</p>
      <div class="mode-segmented-control">
        <label class="mode-btn" :class="{ active: analysisMode === 'solo' }">
          <input type="radio" v-model="analysisMode" value="solo" :disabled="loadingSingle" />
          <span class="m-icon">👤</span> 专家单挑
        </label>
        <label class="mode-btn" :class="{ active: analysisMode === 'debate' }">
          <input type="radio" v-model="analysisMode" value="debate" :disabled="loadingSingle" />
          <span class="m-icon">⚔️</span> 多体辩论
        </label>
        <label class="mode-btn" :class="{ active: analysisMode === 'quant' }">
          <input type="radio" v-model="analysisMode" value="quant" :disabled="loadingSingle" />
          <span class="m-icon">📉</span> 纯粹量化
        </label>
      </div>
      
      <div class="input-group search-container">
        <input 
          v-model="ticker" 
          placeholder="输入代码或公司名 (如 NVDA)" 
          @input="handleSearch"
          @keyup.enter="runSingleAnalysis" 
          @focus="handleSearch"
          :disabled="loadingSingle"
        />
        <!-- Auto-suggestion Dropdown -->
        <div v-if="showSuggestions" class="suggestion-box">
          <div 
            v-for="s in suggestions" 
            :key="s.symbol" 
            class="suggestion-item"
            @click="selectTicker(s)"
          >
            <span class="s-symbol">{{ s.symbol }}</span>
            <span class="s-name">{{ s.name }}</span>
            <span class="s-exch">{{ s.exch }}</span>
          </div>
        </div>
        <button v-if="!loadingSingle" @click="runSingleAnalysis" class="btn single-btn">启动深研</button>
        <button v-else @click="stopAnalysis" class="btn stop-btn">停止</button>
      </div>
      <p v-if="singleStatus" class="status">{{ singleStatus }}</p>
    </div>
  </div>

  <!-- Real-time Agent Thought Stream -->
  <div class="monitor-section" v-if="loadingSingle || loadingBatch || logs.length > 0">
    <div class="monitor-header">
      <div class="stage-info">
        <span class="pulse"></span> 
        当前阶段: <strong>{{ currentStage }}</strong>
      </div>
      <div class="progress-container">
        <div class="progress-bar" :style="{ width: progress + '%' }"></div>
        <span class="progress-text">{{ progress }}%</span>
      </div>
    </div>
    
    <div class="log-window" ref="logContainer">
      <div v-for="(line, i) in logs" :key="i" class="log-line">
        <span class="line-content">{{ line }}</span>
      </div>
      <div v-if="logs.length === 0" class="log-placeholder">正在等待 Agent 唤醒...</div>
    </div>
  </div>
</div>
</template>

<style scoped>
.control-center { margin-bottom: 3rem; }
.dashboard-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin: 1.5rem 0;
}

.card {
  padding: 1.5rem;
  border-radius: 16px;
  background-color: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
  position: relative;
}

.card:hover {
  transform: translateY(-8px);
  border-color: var(--vp-c-brand);
  background-color: var(--vp-c-bg-alt);
  box-shadow: 0 15px 35px rgba(0, 163, 255, 0.12);
}

.card::after {
  content: '';
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background: radial-gradient(circle at top right, var(--vp-c-brand-soft) 0%, transparent 60%);
  opacity: 0;
  transition: opacity 0.4s ease;
  pointer-events: none;
}
.card:hover::after { opacity: 0.2; }

.icon { 
  font-size: 2rem; 
  margin-bottom: 0.5rem; 
  display: inline-block; /* 确保 transform 生效且不影响布局 */
  transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
}
.card:hover .icon { transform: scale(1.1) rotate(5deg); } /* 减小缩放倍数，防止溢出 */

h3 { margin: 0 0 0.5rem 0; font-size: 1.1rem; }
p { font-size: 0.85rem; color: var(--vp-c-text-2); margin-bottom: 1.2rem; }

.btn { 
  width: 100%; 
  padding: 0.8rem; 
  border-radius: 10px; 
  font-weight: 800; 
  cursor: pointer; 
  border: none; 
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.batch-btn { 
  background: linear-gradient(135deg, var(--vp-c-brand), #3eaf7c); 
  color: white;
  box-shadow: 0 5px 15px rgba(0, 163, 255, 0.2);
}
.batch-btn:hover:not(:disabled) {
  transform: scale(1.03);
  box-shadow: 0 8px 25px rgba(0, 163, 255, 0.4);
  filter: brightness(1.1);
}

.single-btn { 
  background-color: var(--vp-c-brand-soft); 
  color: var(--vp-c-brand); 
  border: 1px solid var(--vp-c-brand); 
  min-width: 100px; 
}
.single-btn:hover:not(:disabled) {
  background-color: var(--vp-c-brand);
  color: white;
  transform: scale(1.03);
}

.stop-btn { 
  background-color: #d32f2f; 
  color: white; 
  min-width: 100px; 
}
.stop-btn:hover {
  background-color: #ff1744;
  transform: scale(1.03) rotate(-1deg);
}

.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.input-group { display: flex; gap: 0.5rem; }
.search-container { position: relative; }

.mode-segmented-control {
  display: flex;
  background-color: var(--vp-c-bg-mute);
  padding: 4px;
  border-radius: 12px;
  margin-bottom: 1rem;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
  gap: 4px;
}
.mode-btn {
  flex: 1;
  text-align: center;
  padding: 0.5rem 0.2rem;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--vp-c-text-2);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  user-select: none;
}
.mode-btn input[type="radio"] { display: none; }
.mode-btn:hover:not(.active) {
  background-color: var(--vp-c-bg-alt);
  color: var(--vp-c-text-1);
}
.mode-btn.active {
  background-color: var(--vp-c-brand);
  color: white;
  box-shadow: 0 4px 12px rgba(0, 163, 255, 0.3);
  transform: translateY(-1px);
}
.m-icon { font-size: 1rem; }

input { 
  flex: 1; 
  padding: 0.6rem 1rem; 
  border-radius: 10px; 
  border: 1px solid var(--vp-c-divider); 
  background: var(--vp-c-bg); 
  color: var(--vp-c-text-1); 
  font-family: 'JetBrains Mono', monospace;
  transition: all 0.3s ease;
}
input:focus {
  border-color: var(--vp-c-brand);
  box-shadow: 0 0 0 3px var(--vp-c-brand-soft);
  outline: none;
}

.suggestion-box {
  position: absolute;
  top: 100%;
  left: 0;
  right: 5rem; /* 避开按钮 */
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-brand);
  border-radius: 8px;
  z-index: 100;
  margin-top: 4px;
  max-height: 200px;
  overflow-y: auto;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
.suggestion-item {
  padding: 10px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--vp-c-divider);
}
.suggestion-item:hover { background: var(--vp-c-bg-alt); }
.s-symbol { font-weight: 800; color: var(--vp-c-brand); min-width: 60px; }
.s-name { font-size: 0.75rem; color: var(--vp-c-text-2); flex: 1; margin: 0 10px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.s-exch { font-size: 0.65rem; color: var(--vp-c-text-3); opacity: 0.7; }

.status { margin-top: 0.8rem; font-size: 0.8rem; font-weight: 600; color: var(--vp-c-brand); }

/* --- Monitor UI --- */
.monitor-section {
  margin-top: 2rem;
  background: #0d1117;
  border-radius: 12px;
  border: 1px solid #30363d;
  padding: 1.5rem;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}
.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.2rem;
  color: #c9d1d9;
}
.stage-info { display: flex; align-items: center; gap: 10px; font-size: 0.9rem; }
.pulse { width: 8px; height: 8px; background: #238636; border-radius: 50%; animation: pulse-animation 1.5s infinite; }
@keyframes pulse-animation { 0% { box-shadow: 0 0 0 0 rgba(35, 134, 54, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(35, 134, 54, 0); } 100% { box-shadow: 0 0 0 0 rgba(35, 134, 54, 0); } }

.progress-container { flex: 1; max-width: 200px; height: 8px; background: #30363d; border-radius: 4px; margin-left: 20px; position: relative; }
.progress-bar { height: 100%; background: var(--vp-c-brand); border-radius: 4px; transition: width 0.5s ease; }
.progress-text { position: absolute; right: -40px; top: -5px; font-size: 0.75rem; }

.log-window {
  height: 250px;
  overflow-y: auto;
  background: #161b22;
  border-radius: 8px;
  padding: 1rem;
  border: 1px solid #30363d;
}
.log-line { font-size: 0.8rem; line-height: 1.6; color: #8b949e; margin-bottom: 4px; }
.log-line:last-child { color: #58a6ff; font-weight: 700; }
.log-placeholder { color: #484f58; font-style: italic; text-align: center; margin-top: 100px; }

@media (max-width: 768px) {
  .dashboard-container { grid-template-columns: 1fr; }
}
</style>
