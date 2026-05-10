<template>
  <div class="fund-manager">
    <!-- 1. 资产概览卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="label">单位净值 (NAV)</div>
        <div class="value highlight">{{ status.nav || '1.0000' }}</div>
      </div>
      <div class="stat-card">
        <div class="label">总资产市值</div>
        <div class="value">${{ formatNumber(status.total_value) }}</div>
      </div>
      <div class="stat-card">
        <div class="label">累计盈亏</div>
        <div class="value" :class="getPnlClass(analysis.metrics?.total_return)">{{ analysis.metrics?.total_return || '0.00%' }}</div>
      </div>
    </div>

    <!-- 2. 专业分析视图 (图表与风险指标) -->
    <div class="section analysis-view">
      <h3>📈 基金业绩分析 (Quant Analysis)</h3>
      <div class="analysis-grid">
        <!-- 风险指标 -->
        <div class="metrics-panel">
          <div class="m-item"><strong>夏普比率 (Sharpe)</strong> <span>{{ analysis.metrics?.sharpe }}</span></div>
          <div class="m-item"><strong>最大回撤 (MDD)</strong> <span class="text-red">{{ analysis.metrics?.max_drawdown }}</span></div>
          <div class="m-item"><strong>年化波动率</strong> <span>{{ analysis.metrics?.volatility }}</span></div>
        </div>
        <!-- 净值曲线 (SVG版) -->
        <div class="chart-container">
          <svg v-if="analysis.history?.length > 1" viewBox="0 0 400 150" class="nav-chart">
            <polyline
              fill="none"
              stroke="var(--vp-c-brand)"
              stroke-width="2"
              :points="chartPoints"
            />
          </svg>
          <div v-else class="chart-placeholder">数据积累中，需至少 2 天历史记录...</div>
        </div>
      </div>
    </div>

    <!-- 3. 持仓列表 -->
    <div class="section">
      <div class="header-with-btn">
        <h3>💼 持仓明细</h3>
        <button @click="viewMode = viewMode === 'list' ? 'trade' : 'list'" class="btn sm-btn">
          {{ viewMode === 'list' ? '进行买卖交易' : '返回持仓列表' }}
        </button>
      </div>
      
      <div v-if="viewMode === 'list'">
        <table class="data-table">
          <thead>
            <tr>
              <th>代码</th>
              <th>数量</th>
              <th>成本</th>
              <th>现价</th>
              <th>盈亏</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="pos in status.positions" :key="pos.symbol">
              <td><strong>{{ pos.symbol }}</strong></td>
              <td>{{ pos.quantity }}</td>
              <td>${{ pos.cost }}</td>
              <td>${{ pos.current_price }}</td>
              <td :class="getPnlClass(pos.pnl)">{{ pos.pnl }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 交易操作台 (改为按需切换) -->
      <div v-else class="trade-form">
        <div class="form-row">
          <input v-model="tradeForm.symbol" placeholder="代码" class="input-field" />
          <select v-model="tradeForm.side" class="select-field">
            <option value="BUY">买入</option>
            <option value="SELL">卖出</option>
          </select>
          <input v-model.number="tradeForm.quantity" type="number" class="input-field" placeholder="数量" />
          <input v-model.number="tradeForm.price" type="number" class="input-field" placeholder="单价" />
          <button @click="handleTrade" :disabled="loading" class="btn trade-btn">提交成交</button>
        </div>
      </div>
    </div>

    <!-- 4. AI 组合诊断 -->
    <div class="section diagnosis-panel">
      <div class="header-with-btn">
        <h3>🧠 AI 资产配置诊断 (Morningstar Style)</h3>
        <button @click="fetchDiagnosis" :disabled="diagLoading" class="btn ai-btn">一键生成体检报告</button>
      </div>
      <div v-if="diagnosis" class="diagnosis-content markdown-body" v-html="renderMarkdown(diagnosis)"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { marked } from 'marked'

const status = ref({ nav: 1.0, total_value: 0, cash: 0, positions: [] })
const analysis = ref({ metrics: {}, history: [] })
const viewMode = ref('list')
const diagnosis = ref('')
const loading = ref(false)
const diagLoading = ref(false)

const tradeForm = ref({ symbol: '', side: 'BUY', quantity: 0, price: 0 })
const API_BASE = 'http://localhost:8000'

const fetchAll = async () => {
  try {
    const sResp = await fetch(`${API_BASE}/portfolio/status`)
    status.value = await sResp.json()
    const aResp = await fetch(`${API_BASE}/portfolio/analysis`)
    analysis.value = await aResp.json()
  } catch (e) { console.error(e) }
}

const chartPoints = computed(() => {
  if (!analysis.value.history?.length) return ""
  const data = analysis.value.history
  const minNav = Math.min(...data.map(d => d.nav)) * 0.99
  const maxNav = Math.max(...data.map(d => d.nav)) * 1.01
  const range = maxNav - minNav
  
  return data.map((d, i) => {
    const x = (i / (data.length - 1)) * 400
    const y = 150 - ((d.nav - minNav) / range) * 150
    return `${x},${y}`
  }).join(" ")
})

const handleTrade = async () => {
  if (!tradeForm.value.symbol || tradeForm.value.quantity <= 0) return
  loading.value = true
  try {
    const url = `${API_BASE}/portfolio/trade?symbol=${tradeForm.value.symbol}&side=${tradeForm.value.side}&quantity=${tradeForm.value.quantity}&price=${tradeForm.value.price}`
    await fetch(url, { method: 'POST' })
    await fetchAll()
    viewMode.value = 'list'
  } catch (e) { alert("交易失败") }
  finally { loading.value = false }
}

const fetchDiagnosis = async () => {
  diagLoading.value = true
  try {
    const resp = await fetch(`${API_BASE}/portfolio/diagnosis`)
    const res = await resp.json()
    diagnosis.value = res.report
  } finally { diagLoading.value = false }
}

const formatNumber = (num) => num ? Number(num).toLocaleString(undefined, { minimumFractionDigits: 2 }) : '0.00'
const getPnlClass = (pnl) => (pnl && pnl.startsWith('-')) ? 'text-red' : 'text-green'
const renderMarkdown = (text) => text ? marked.parse(text) : ''

onMounted(fetchAll)
</script>

<style scoped>
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
.stat-card { background: var(--vp-c-bg-soft); padding: 1.2rem; border-radius: 12px; border: 1px solid var(--vp-c-divider); text-align: center; }
.stat-card .value { font-size: 1.6rem; font-weight: 800; font-family: 'JetBrains Mono', monospace; }
.highlight { color: var(--vp-c-brand); }

.section { background: var(--vp-c-bg-soft); padding: 1.5rem; border-radius: 16px; margin-bottom: 1.5rem; border: 1px solid var(--vp-c-divider); }
.analysis-grid { display: grid; grid-template-columns: 200px 1fr; gap: 2rem; margin-top: 1rem; }
.m-item { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--vp-c-divider); font-size: 0.9rem; }
.chart-container { height: 150px; background: var(--vp-c-bg); border-radius: 8px; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.nav-chart { width: 100%; height: 100%; padding: 10px; }

.data-table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
th { color: var(--vp-c-text-2); font-weight: 500; font-size: 0.85rem; text-transform: uppercase; }
td, th { padding: 12px 8px; text-align: left; border-bottom: 1px solid var(--vp-c-divider); }
.text-red { color: #ff5252; font-weight: 600; }
.text-green { color: #4caf50; font-weight: 600; }

.btn { padding: 8px 16px; border-radius: 8px; cursor: pointer; font-weight: 600; transition: all 0.2s; border: none; }
.sm-btn { font-size: 0.8rem; background: var(--vp-c-bg); border: 1px solid var(--vp-c-brand); color: var(--vp-c-brand); }
.trade-btn { background: var(--vp-c-brand); color: white; width: 100%; margin-top: 10px; }
.ai-btn { background: #6200ea; color: white; }

.header-with-btn { display: flex; justify-content: space-between; align-items: center; }
.diagnosis-content { background: var(--vp-c-bg); padding: 1.5rem; border-radius: 12px; margin-top: 1rem; border: 1px solid var(--vp-c-divider); }
.input-field { padding: 8px; border-radius: 6px; border: 1px solid var(--vp-c-divider); background: var(--vp-c-bg); width: 120px; }
</style>
