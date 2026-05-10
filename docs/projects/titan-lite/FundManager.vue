<template>
  <div class="fund-manager">
    <!-- 1. 核心资产概览卡片 (强制居中) -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="label">单位净值 (NAV)</div>
        <div class="value highlight">{{ status.nav || '1.0000' }}</div>
      </div>
      <div class="stat-card">
        <div class="label">全币种总估值 (Total Value)</div>
        <div class="value multi-currency">
          <div class="primary-val">USD: ${{ formatNumber(status.total_value_usd) }}</div>
          <div class="secondary-vals">
            <span>HKD: {{ formatNumber(status.total_value_hkd) }}</span>
            <span class="divider">|</span>
            <span>CNY: {{ formatNumber(status.total_value_cny) }}</span>
          </div>
        </div>
      </div>
      <div class="stat-card">
        <div class="label">累计盈亏</div>
        <div class="value pnl-value" :class="getPnlClass(analysis.metrics?.total_return)">
          <span class="arrow">{{ getPnlArrow(analysis.metrics?.total_return) }}</span>
          {{ analysis.metrics?.total_return || '0.00%' }}
        </div>
      </div>
    </div>

    <!-- 2. 专业分析视图 -->
    <div class="section analysis-view">
      <h3 class="section-title">📈 业绩与风控分析 (Quant Analysis)</h3>
      <div class="analysis-grid">
        <div class="metrics-panel">
          <div class="m-item"><strong>夏普比率 (Sharpe)</strong> <span class="right-align">{{ analysis.metrics?.sharpe }}</span></div>
          <div class="m-item"><strong>最大回撤 (MDD)</strong> <span class="text-brick right-align">{{ analysis.metrics?.max_drawdown }}</span></div>
          <div class="m-item"><strong>年化波动率</strong> <span class="right-align">{{ analysis.metrics?.volatility }}</span></div>
        </div>
        <div class="chart-wrapper">
          <svg v-if="analysis.history?.user?.length > 1" viewBox="0 0 450 180" class="nav-chart">
            <line x1="40" y1="30" x2="430" y2="30" stroke="var(--vp-c-divider)" stroke-dasharray="2" />
            <line x1="40" y1="80" x2="430" y2="80" stroke="var(--vp-c-divider)" stroke-dasharray="2" />
            <line x1="40" y1="130" x2="430" y2="130" stroke="var(--vp-c-divider)" stroke-dasharray="2" />
            <line x1="40" y1="10" x2="40" y2="150" stroke="var(--vp-c-text-3)" stroke-width="1" />
            <line x1="40" y1="150" x2="440" y2="150" stroke="var(--vp-c-text-3)" stroke-width="1" />
            <polyline fill="none" stroke="#666" stroke-width="1" stroke-dasharray="4" :points="benchmarkPoints" />
            <polyline fill="none" stroke="var(--vp-c-brand)" stroke-width="2.5" :points="chartPoints" />
            <text x="5" y="35" font-size="9" fill="var(--vp-c-text-3)">High</text>
            <text x="5" y="155" font-size="9" fill="var(--vp-c-text-3)">Base</text>
            <text x="200" y="170" font-size="10" text-anchor="middle" fill="var(--vp-c-text-3)">Time Series</text>
            <rect x="300" y="5" width="10" height="10" fill="var(--vp-c-brand)" />
            <text x="315" y="14" font-size="9" fill="var(--vp-c-text-2)">Fund</text>
            <rect x="370" y="5" width="10" height="10" fill="#666" />
            <text x="385" y="14" font-size="9" fill="var(--vp-c-text-2)">SPY</text>
          </svg>
          <div v-else class="chart-placeholder">资产曲线积累中 (录入历史日期可立即生成)</div>
        </div>
      </div>
    </div>

    <!-- 3. 持仓与流水管理 -->
    <div class="section main-container">
      <div class="tab-header">
        <div class="tabs">
          <button @click="switchTab('positions')" :class="{ active: activeTab === 'positions' && viewMode === 'list' }">💼 持仓分析</button>
          <button @click="switchTab('history')" :class="{ active: activeTab === 'history' && viewMode === 'list' }">📜 交易账本</button>
        </div>
        <button @click="viewMode = viewMode === 'list' ? 'trade' : 'list'" class="btn sm-btn action-toggle">
          {{ viewMode === 'list' ? '+ 资产录入' : '返回列表' }}
        </button>
      </div>

      <!-- A. 列表视图 -->
      <div v-if="viewMode === 'list'">
        <!-- 持仓表组 -->
        <div v-if="activeTab === 'positions'">
          <h4 class="table-label">💵 现金资产 (Cash Reserves)</h4>
          <table class="data-table mb-2">
            <thead>
              <tr>
                <th>币种</th>
                <th>持有余额</th>
                <th>折合 USD</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in status.cash_positions" :key="c.symbol">
                <td class="center-align"><strong>{{ c.symbol }}</strong></td>
                <td class="right-align tabular">{{ formatNumber(c.quantity) }}</td>
                <td class="right-align tabular">${{ formatNumber(c.mkt_value_usd) }}</td>
              </tr>
            </tbody>
          </table>

          <h4 class="table-label">🇺🇸 美股持仓 (US Equities)</h4>
          <table class="data-table mb-2">
            <thead>
              <tr>
                <th>标的代码</th>
                <th>持有数量</th>
                <th>平均成本 (USD)</th>
                <th>实时现价</th>
                <th>持仓市值 (USD)</th>
                <th>累计盈亏</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="pos in status.us_equities" :key="pos.symbol">
                <td class="center-align"><strong>{{ pos.symbol }}</strong></td>
                <td class="right-align tabular">{{ pos.quantity }}</td>
                <td class="right-align tabular">${{ formatNumber(pos.cost) }}</td>
                <td class="right-align tabular">${{ formatNumber(pos.current_price) }}</td>
                <td class="right-align tabular"><strong>${{ formatNumber(pos.mkt_value) }}</strong></td>
                <td class="right-align tabular" :class="getPnlClass(pos.pnl)">{{ pos.pnl }}</td>
              </tr>
            </tbody>
          </table>

          <h4 class="table-label">🇭🇰 港股持仓 (HK Equities)</h4>
          <table class="data-table">
            <thead>
              <tr>
                <th>标的代码</th>
                <th>持有数量</th>
                <th>平均成本 (HKD)</th>
                <th>实时现价</th>
                <th>持仓市值 (HKD)</th>
                <th>累计盈亏</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="pos in status.hk_equities" :key="pos.symbol">
                <td class="center-align"><strong>{{ pos.symbol }}</strong></td>
                <td class="right-align tabular">{{ pos.quantity }}</td>
                <td class="right-align tabular">{{ formatNumber(pos.cost) }}</td>
                <td class="right-align tabular">{{ formatNumber(pos.current_price) }}</td>
                <td class="right-align tabular"><strong>{{ formatNumber(pos.mkt_value) }}</strong></td>
                <td class="right-align tabular" :class="getPnlClass(pos.pnl)">{{ pos.pnl }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 交易流水账本 -->
        <div v-else>
          <h4 class="table-label">🧾 历史成交账本 (Audit Ledger)</h4>
          <table class="data-table">
            <thead>
              <tr>
                <th>成交日期</th>
                <th>代码/币种</th>
                <th>业务类型</th>
                <th>成交数量</th>
                <th>单价/汇率</th>
                <th>成交总额</th>
                <th>管理</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="tx in tradeHistory" :key="tx.id">
                <td class="small-text center-align">{{ tx.timestamp.split(' ')[0] }}</td>
                <td class="center-align"><strong>{{ tx.symbol }}</strong></td>
                <td class="center-align"><span class="side-tag" :class="tx.side">{{ formatSide(tx.side) }}</span></td>
                <td class="right-align tabular">{{ tx.quantity }}</td>
                <td class="right-align tabular">${{ formatNumber(tx.price) }}</td>
                <td class="right-align tabular">${{ formatNumber(tx.total) }}</td>
                <td class="center-align">
                  <button @click="deleteTrade(tx.id)" class="del-btn">撤销</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 资产录入表单 -->
      <div v-else class="trade-form">
        <div class="form-grid">
          <div class="input-group">
            <label>操作类型</label>
            <select v-model="tradeForm.side" class="full-width">
              <option value="INITIAL">初始资产同步 (不计入现金流)</option>
              <option value="DEPOSIT">资金入金 (充值本金)</option>
              <option value="BUY">二级市场买入 (扣减现金)</option>
              <option value="SELL">二级市场卖出 (回笼现金)</option>
            </select>
          </div>
          <div class="input-group">
            <label>代码 / 币种</label>
            <input v-model="tradeForm.symbol" placeholder="如 NVDA 或 USD" class="full-width" />
          </div>
          <div class="input-group">
            <label>数量 / 金额</label>
            <input v-model.number="tradeForm.quantity" type="number" class="full-width" />
          </div>
          <div class="input-group">
            <label>成交价格 / 汇率</label>
            <input v-model.number="tradeForm.price" type="number" class="full-width" />
          </div>
          <div class="input-group">
            <label>成交日期</label>
            <input v-model="tradeForm.date" type="date" class="full-width" />
          </div>
        </div>
        <button @click="handleTrade" :disabled="loading" class="btn trade-btn">确认记录并更新账户</button>
      </div>
    </div>

    <!-- 4. AI 诊断 (左对齐) -->
    <div class="section">
      <div class="header-with-btn left-align">
        <h3 class="section-title">🧠 AI 资产配置诊断</h3>
        <button @click="fetchDiagnosis" :disabled="diagLoading" class="btn ai-btn">执行深度体检</button>
      </div>
      <div v-if="diagnosis" class="diagnosis-content markdown-body" v-html="renderMarkdown(diagnosis)"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { marked } from 'marked'

const status = ref({ nav: 1.0, total_value_usd: 0, cash_positions: [], us_equities: [], hk_equities: [] })
const analysis = ref({ metrics: {}, history: { user: [], benchmark: [] } })
const tradeHistory = ref([])
const activeTab = ref('positions')
const viewMode = ref('list')
const diagnosis = ref('')
const loading = ref(false)
const diagLoading = ref(false)

const tradeForm = ref({ symbol: '', side: 'INITIAL', quantity: 0, price: 1, date: new Date().toISOString().split('T')[0] })

// 动态检测 API 地址，支持服务器公网部署
const API_BASE = typeof window !== 'undefined' 
  ? `${window.location.protocol}//${window.location.hostname}:8000` 
  : 'http://localhost:8000'

const fetchAll = async () => {
  try {
    const sResp = await fetch(`${API_BASE}/portfolio/status`); 
    if (sResp.ok) status.value = await sResp.json();
    const aResp = await fetch(`${API_BASE}/portfolio/analysis`); 
    if (aResp.ok) analysis.value = await aResp.json();
    const hResp = await fetch(`${API_BASE}/portfolio/history`); 
    if (hResp.ok) tradeHistory.value = await hResp.json();
  } catch (e) { console.error("Sync failed", e) }
}

const switchTab = (tab) => {
  activeTab.value = tab;
  viewMode.value = 'list';
}

const chartPoints = computed(() => {
  const data = analysis.value.history?.user; 
  if (!data || data.length < 2) return ""
  const allNavs = [...data.map(d => d.nav), ...analysis.value.history.benchmark]
  const min = Math.min(...allNavs) * 0.98; const max = Math.max(...allNavs) * 1.02; const range = max - min || 1
  return data.map((d, i) => `${40 + (i/(data.length-1))*390},${150-((d.nav-min)/range)*140}`).join(" ")
})

const benchmarkPoints = computed(() => {
  const data = analysis.value.history?.benchmark; 
  if (!data || data.length < 2) return ""
  const user_data = analysis.value.history.user
  const allNavs = [...user_data.map(d => d.nav), ...data]
  const min = Math.min(...allNavs) * 0.98; const max = Math.max(...allNavs) * 1.02; const range = max - min || 1
  return data.map((v, i) => `${40 + (i/(data.length-1))*390},${150-((v-min)/range)*140}`).join(" ")
})

const handleTrade = async () => {
  loading.value = true
  try {
    const url = `${API_BASE}/portfolio/trade?symbol=${tradeForm.value.symbol.toUpperCase()}&side=${tradeForm.value.side}&quantity=${tradeForm.value.quantity}&price=${tradeForm.value.price}&date=${tradeForm.value.date}`
    const res = await (await fetch(url, { method: 'POST' })).json()
    alert(res.msg); await fetchAll(); viewMode.value = 'list'; activeTab.value = 'history';
  } catch (e) { alert("记录失败") } finally { loading.value = false }
}

const deleteTrade = async (id) => {
  if (!confirm("确定撤销记录并重新核算吗？")) return
  try {
    const res = await (await fetch(`${API_BASE}/portfolio/trade/${id}`, { method: 'DELETE' })).json()
    alert(res.msg); await fetchAll()
  } catch (e) { alert("撤销失败") }
}

const fetchDiagnosis = async () => {
  diagLoading.value = true
  try { diagnosis.value = (await (await fetch(`${API_BASE}/portfolio/diagnosis`)).json()).report }
  finally { diagLoading.value = false }
}

const formatNumber = (num) => num ? Number(num).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'
const getPnlClass = (pnl) => (pnl && pnl.startsWith('-')) ? 'text-brick' : 'text-mint'
const getPnlArrow = (pnl) => (pnl && pnl.startsWith('-')) ? '▾' : '▴'
const formatSide = (side) => {
  const map = { 'INITIAL': '初始同步', 'DEPOSIT': '入金', 'BUY': '买入', 'SELL': '卖出' }
  return map[side] || side
}
const renderMarkdown = (text) => text ? marked.parse(text) : ''

onMounted(fetchAll)
</script>

<style scoped>
.text-mint { color: #43a047; font-weight: 600; }
.text-brick { color: #d32f2f; font-weight: 600; }

.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 2.5rem; }
.stat-card { background: var(--vp-c-bg-soft); padding: 1.2rem 1rem; border-radius: 12px; border: 1px solid var(--vp-c-divider); text-align: center; display: flex; flex-direction: column; justify-content: center; min-height: 140px; }
.stat-card .label { font-size: 0.85rem; color: var(--vp-c-text-2); font-weight: 600; margin-bottom: 8px; }
.stat-card .value { font-size: 1.8rem; font-weight: 800; font-family: 'JetBrains Mono', monospace; line-height: 1.1; }

.multi-currency { display: flex; flex-direction: column; gap: 6px; }
.secondary-vals { font-size: 0.85rem; color: var(--vp-c-text-3); display: flex; justify-content: center; gap: 10px; }
.divider { color: var(--vp-c-divider); }
.highlight { color: var(--vp-c-brand); }
.pnl-value { display: flex; align-items: center; justify-content: center; gap: 4px; }

.section { background: var(--vp-c-bg-soft); padding: 1.8rem; border-radius: 16px; margin-bottom: 1.8rem; border: 1px solid var(--vp-c-divider); }
.section-title { margin-bottom: 1.5rem !important; text-align: left !important; width: 100%; }
.header-with-btn { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.header-with-btn.left-align { justify-content: flex-start; gap: 20px; }
.analysis-grid { display: grid; grid-template-columns: 220px 1fr; gap: 2rem; }
.m-item { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--vp-c-divider); font-size: 0.85rem; }
.chart-wrapper { background: var(--vp-c-bg); border-radius: 12px; padding: 1.2rem; border: 1px solid var(--vp-c-divider); }
.nav-chart { width: 100%; height: auto; overflow: visible; }
.chart-placeholder { height: 160px; display: flex; align-items: center; justify-content: center; color: var(--vp-c-text-3); font-style: italic; }

.table-label { font-size: 1rem; font-weight: 700; margin: 1.8rem 0 1rem; color: var(--vp-c-brand); border-left: 5px solid var(--vp-c-brand); padding-left: 12px; }
.tab-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.8rem; border-bottom: 1px solid var(--vp-c-divider); padding-bottom: 0.6rem; }
.tabs { display: flex; gap: 1.8rem; }
.tabs button { background: none; border: none; color: var(--vp-c-text-2); cursor: pointer; font-weight: 600; padding: 8px 0; border-bottom: 3px solid transparent; transition: all 0.2s; }
.tabs button.active { color: var(--vp-c-brand); border-bottom-color: var(--vp-c-brand); }
.data-table { width: 100%; border-collapse: collapse; margin-bottom: 1.5rem; table-layout: auto; }
th { text-align: center !important; font-size: 0.7rem; color: var(--vp-c-text-3); text-transform: uppercase; padding: 10px 6px; border-bottom: 2px solid var(--vp-c-divider); background: var(--vp-c-bg-alt); white-space: nowrap; }
td { padding: 12px 6px; border-bottom: 1px solid var(--vp-c-divider); font-size: 0.8rem; white-space: nowrap; }
.right-align { text-align: right !important; }
.center-align { text-align: center !important; }
.tabular { font-family: 'JetBrains Mono', monospace; letter-spacing: -0.3px; }

.small-text { font-size: 0.75rem; color: var(--vp-c-text-3); }
.trade-form { background: var(--vp-c-bg-alt); padding: 2.2rem; border-radius: 12px; border: 1px solid var(--vp-c-divider); }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1.8rem; margin-bottom: 2.2rem; }
.input-group label { display: block; font-size: 0.85rem; margin-bottom: 10px; font-weight: 700; color: var(--vp-c-text-2); }
.full-width { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid var(--vp-c-divider); background: var(--vp-c-bg); color: var(--vp-c-text-1); }

.btn { padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: 600; transition: all 0.2s; border: none; }
.sm-btn { background: var(--vp-c-brand-soft); color: var(--vp-c-brand); }
.trade-btn { background: var(--vp-c-brand); color: white; width: 100%; height: 50px; font-size: 1.1rem; }
.ai-btn { background: #43a047; color: white; min-width: 150px; white-space: nowrap; }
.del-btn { color: #d32f2f; background: none; border: 1px solid #d32f2f; font-size: 0.75rem; padding: 4px 12px; border-radius: 6px; }
.del-btn:hover { background: rgba(211, 47, 47, 0.1); }

.side-tag { padding: 3px 8px; border-radius: 5px; font-size: 0.7rem; font-weight: 800; }
.side-tag.BUY { background: rgba(67, 160, 71, 0.1); color: #43a047; }
.side-tag.SELL { background: rgba(211, 47, 47, 0.1); color: #d32f2f; }
.side-tag.INITIAL { background: rgba(100, 100, 100, 0.1); color: #aaa; }
.side-tag.DEPOSIT { background: rgba(0, 163, 255, 0.1); color: #00a3ff; }
</style>
