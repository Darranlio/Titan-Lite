<script setup>
import { ref } from 'vue'

const batchStatus = ref('')
const singleStatus = ref('')
const ticker = ref('')
const loadingBatch = ref(false)
const loadingSingle = ref(false)

// 基础配置：替换为你的真实后端地址
const API_BASE = 'http://your-server-ip:8000'

const runBatchAnalysis = async () => {
  loadingBatch.value = true
  batchStatus.value = '正在启动全市场深度扫描 (预计耗时 5-10 分钟)...'
  try {
    const response = await fetch(`${API_BASE}/run`, { method: 'POST' })
    const data = await response.json()
    batchStatus.value = '✅ 批量扫描已触发！请稍后刷新“研报库”查看结果。'
  } catch (error) {
    batchStatus.value = '❌ 启动失败，请检查后端服务。'
  } finally {
    loadingBatch.value = false
  }
}

const runSingleAnalysis = async () => {
  if (!ticker.value) {
    singleStatus.value = '请输入股票代码 (如 AAPL 或 0700.HK)'
    return
  }
  loadingSingle.value = true
  singleStatus.value = `正在针对 ${ticker.value} 进行专项深度研判...`
  try {
    const response = await fetch(`${API_BASE}/analyze/${ticker.value.toUpperCase()}`, { method: 'POST' })
    const data = await response.json()
    if (data.status === 'success') {
      singleStatus.value = `✅ ${ticker.value} 研判完成！请前往研报库查看详细报告。`
    } else {
      singleStatus.value = `⚠️ 研判失败，请检查代码是否正确或数据源是否可用。`
    }
  } catch (error) {
    singleStatus.value = '❌ 通信失败，请检查后端连接。'
  } finally {
    loadingSingle.value = false
  }
}
</script>

<template>
<div class="dashboard-container">
  <div class="card batch-card">
    <div class="icon">🌍</div>
    <h3>全市场深度扫描</h3>
    <p>自动抓取热点标的，通过 FMP/Finnhub 过滤并启动多智能体辩论。</p>
    <button @click="runBatchAnalysis" :disabled="loadingBatch" class="btn batch-btn">
      {{ loadingBatch ? '执行中...' : '开始全市场扫描' }}
    </button>
    <p v-if="batchStatus" class="status">{{ batchStatus }}</p>
  </div>

  <div class="card single-card">
    <div class="icon">🎯</div>
    <h3>个股专项研判</h3>
    <p>跳过初筛，直接对指定标的进行深度真伪鉴别与投研分析。</p>
    <div class="input-group">
      <input v-model="ticker" placeholder="输入代码 (如 NVDA)" @keyup.enter="runSingleAnalysis" />
      <button @click="runSingleAnalysis" :disabled="loadingSingle" class="btn single-btn">
        {{ loadingSingle ? '分析中...' : '深度研判' }}
      </button>
    </div>
    <p v-if="singleStatus" class="status">{{ singleStatus }}</p>
  </div>
</div>
</template>

<style scoped>
.dashboard-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin: 2rem 0;
}

@media (max-width: 768px) {
  .dashboard-container {
    grid-template-columns: 1fr;
  }
}

.card {
  padding: 1.5rem;
  border-radius: 12px;
  background-color: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  transition: transform 0.2s, border-color 0.2s;
}

.card:hover {
  border-color: var(--vp-c-brand);
}

.icon {
  font-size: 2rem;
  margin-bottom: 1rem;
}

h3 {
  margin: 0 0 0.5rem 0;
  color: var(--vp-c-text-1);
}

p {
  font-size: 0.9rem;
  color: var(--vp-c-text-2);
  line-height: 1.4;
  margin-bottom: 1.5rem;
}

.btn {
  width: 100%;
  padding: 0.7rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: opacity 0.2s;
}

.batch-btn {
  background: linear-gradient(135deg, var(--vp-c-brand), #3eaf7c);
  color: white;
}

.single-btn {
  background-color: var(--vp-c-brand-soft);
  color: var(--vp-c-brand);
  border: 1px solid var(--vp-c-brand);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-group {
  display: flex;
  gap: 0.5rem;
}

input {
  flex: 1;
  padding: 0.6rem;
  border-radius: 6px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg);
  color: var(--vp-c-text-1);
}

.status {
  margin-top: 1rem;
  font-size: 0.85rem;
  font-weight: 500;
}
</style>
