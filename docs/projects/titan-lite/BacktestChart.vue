<template>
  <div class="backtest-container">
    <div class="metrics-grid">
      <div class="m-card">
        <div class="m-label">总回报</div>
        <div class="m-value" :class="isPositive(metrics.total_return) ? 'up' : 'down'">{{ metrics.total_return }}</div>
      </div>
      <div class="m-card">
        <div class="m-label">超额收益 (Alpha)</div>
        <div class="m-value highlight">{{ metrics.alpha }}</div>
      </div>
      <div class="m-card">
        <div class="m-label">夏普比率</div>
        <div class="m-value">{{ metrics.sharpe_ratio }}</div>
      </div>
      <div class="m-card">
        <div class="m-label">最大回撤</div>
        <div class="m-value down">{{ metrics.max_drawdown }}</div>
      </div>
    </div>

    <div class="chart-box">
      <div class="chart-header">
        <span class="legend asset">● {{ symbol }}</span>
        <span class="legend bench">● SPY (基准)</span>
      </div>
      <svg class="line-chart" viewBox="0 0 400 200" preserveAspectRatio="none">
        <!-- Grid Lines -->
        <line x1="0" y1="180" x2="400" y2="180" stroke="var(--vp-c-divider)" stroke-width="1" />
        <line x1="0" y1="20" x2="400" y2="20" stroke="var(--vp-c-divider)" stroke-width="1" />
        
        <!-- Benchmark Path -->
        <polyline
          fill="none"
          stroke="#999"
          stroke-width="1.5"
          stroke-dasharray="4"
          :points="benchPoints"
        />
        
        <!-- Asset Path -->
        <polyline
          fill="none"
          stroke="var(--vp-c-brand)"
          stroke-width="2.5"
          :points="assetPoints"
        />
      </svg>
      <div class="chart-footer">
        <span>{{ startDate }}</span>
        <span>12个月收益曲线对比</span>
        <span>今日</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  symbol: String,
  btData: Object
})

const metrics = computed(() => props.btData?.metrics || {})
const chartData = computed(() => props.btData?.chart_data || [])

const isPositive = (val) => val && !val.startsWith('-')

const startDate = computed(() => chartData.value[0]?.date || '-')

const points = computed(() => {
  if (chartData.value.length < 2) return { asset: "", bench: "" }
  
  const vals = chartData.value.flatMap(d => [d.asset, d.bench])
  const min = Math.min(...vals) * 0.95
  const max = Math.max(...vals) * 1.05
  const range = max - min || 1
  
  const asset = chartData.value.map((d, i) => {
    const x = (i / (chartData.value.length - 1)) * 400
    const y = 200 - ((d.asset - min) / range) * 160 - 20
    return `${x},${y}`
  }).join(" ")

  const bench = chartData.value.map((d, i) => {
    const x = (i / (chartData.value.length - 1)) * 400
    const y = 200 - ((d.bench - min) / range) * 160 - 20
    return `${x},${y}`
  }).join(" ")
  
  return { asset, bench }
})

const assetPoints = computed(() => points.value.asset)
const benchPoints = computed(() => points.value.bench)
</script>

<style scoped>
.backtest-container {
  margin: 1.5rem 0;
  padding: 1.5rem;
  background: var(--vp-c-bg-alt);
  border-radius: 12px;
  border: 1px solid var(--vp-c-divider);
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.m-card {
  text-align: center;
  padding: 0.8rem;
  background: var(--vp-c-bg-soft);
  border-radius: 8px;
}

.m-label { font-size: 0.75rem; color: var(--vp-c-text-3); margin-bottom: 0.4rem; }
.m-value { font-size: 1.1rem; font-weight: 800; font-family: 'JetBrains Mono', monospace; }
.m-value.up { color: #43a047; }
.m-value.down { color: #d32f2f; }
.m-value.highlight { color: var(--vp-c-brand); }

.chart-box {
  background: var(--vp-c-bg);
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid var(--vp-c-divider);
}

.chart-header { display: flex; gap: 1.5rem; margin-bottom: 0.8rem; font-size: 0.75rem; justify-content: center; }
.legend.asset { color: var(--vp-c-brand); font-weight: bold; }
.legend.bench { color: #999; }

.line-chart { width: 100%; height: 160px; overflow: visible; }
.chart-footer { display: flex; justify-content: space-between; font-size: 0.65rem; color: var(--vp-c-text-3); margin-top: 0.5rem; }
</style>
