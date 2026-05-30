<template>
  <div class="archive-manager-container">
    <!-- Header with Search & Stats -->
    <div class="archive-header">
      <div class="search-bar">
        <input v-model="searchQuery" placeholder="搜索代码、评级或关键词..." class="search-input" />
      </div>
      <div class="archive-stats">
        <span class="stat-pill">总报告: <strong>{{ filteredReports.length }}</strong></span>
      </div>
    </div>

    <div class="table-wrapper">
      <table class="archive-table">
        <thead>
          <tr>
            <th @click="sortBy('date')" class="sortable col-time">研判时间</th>
            <th class="col-symbol">代码</th>
            <th class="col-rating">评级</th>
            <th class="col-price">价格</th>
            <th @click="sortBy('upside')" class="sortable col-upside">涨幅</th>
            <th class="col-manage">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in filteredReports" :key="r.symbol">
            <td class="small-text">{{ formatShortTime(r.file || r.date) }}</td>
            <td>
              <a :href="`./${r.symbol}/index`" class="symbol-link"><strong>{{ r.symbol }}</strong></a>
            </td>
            <td><span class="rating-tag" :class="r.rating.toLowerCase().replace(' ', '-')">{{ r.rating }}</span></td>
            <td class="tabular">${{ r.price }}</td>
            <td class="tabular" :class="r.upside > 0 ? 'up' : 'down'">{{ (r.upside * 100).toFixed(1) }}%</td>
            <td class="actions-cell">
              <div class="action-btns">
                <a :href="`./${r.symbol}/index`" class="view-btn">进入看板</a>
                <button @click="deleteSymbol(r.symbol)" class="delete-btn">删除标的</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'

const reports = ref([])
const searchQuery = ref('')
const sortKey = ref('date')
const sortOrder = ref(-1)

const API_BASE = typeof window !== 'undefined' 
  ? `${window.location.protocol}//${window.location.hostname}:8000` 
  : 'http://localhost:8000'

const fetchArchive = async () => {
  try {
    const res = await fetch(`${API_BASE}/archive/list`)
    reports.value = await res.json()
  } catch (e) { console.error("Archive fetch failed", e) }
}

onMounted(fetchArchive)

const filteredReports = computed(() => {
  // 1. 先按 symbol 去重，只保留最新的记录
  const uniqueReports = []
  const seenSymbols = new Set()
  
  for (const r of reports.value) {
    if (!seenSymbols.has(r.symbol)) {
      uniqueReports.push(r)
      seenSymbols.add(r.symbol)
    }
  }

  // 2. 搜索过滤
  let list = uniqueReports.filter(r => {
    const query = searchQuery.value.toLowerCase()
    return r.symbol.toLowerCase().includes(query) || 
           r.rating.toLowerCase().includes(query)
  })
  
  // 3. 排序
  return list.sort((a, b) => {
    let v1 = a[sortKey.value] || ''
    let v2 = b[sortKey.value] || ''
    if (sortKey.value === 'date') {
      v1 = a.file || a.date
      v2 = b.file || b.date
    }
    return v1 < v2 ? -1 * sortOrder.value : 1 * sortOrder.value
  })
})

const sortBy = (key) => {
  if (sortKey.value === key) {
    sortOrder.value *= -1
  } else {
    sortKey.value = key
    sortOrder.value = -1
  }
}

const deleteSymbol = async (symbol) => {
  if (!confirm(`确定要彻底删除 ${symbol} 的所有档案和看板吗？`)) return
  try {
    const res = await (await fetch(`${API_BASE}/archive/${symbol}`, { method: 'DELETE' })).json()
    alert(res.msg)
    await fetchArchive()
  } catch (e) { alert("删除失败") }
}

const formatShortTime = (ts) => {
  if (!ts) return '-'
  // 恢复显示年份: 2026-05-30 15:45
  const parts = ts.split('_')
  const time = parts[1] ? parts[1].replace(/(\d{2})(\d{2})/, '$1:$2') : ''
  return `${parts[0]} ${time}`
}
</script>

<style scoped>
.archive-manager-container { margin-top: 1rem; width: 100%; }

.archive-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  gap: 1rem;
}

.search-bar { flex: 1; max-width: 400px; }
.search-input {
  width: 100%;
  padding: 0.6rem 1rem;
  border-radius: 10px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg-soft);
  color: var(--vp-c-text-1);
  font-family: inherit;
  transition: all 0.2s;
}
.search-input:focus {
  border-color: var(--vp-c-brand);
  outline: none;
  box-shadow: 0 0 0 2px var(--vp-c-brand-soft);
}

.stat-pill {
  padding: 0.4rem 1rem;
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand);
  border-radius: 20px;
  font-size: 0.85rem;
}

.table-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  width: 100%;
  margin-top: 1rem;
  /* 移除丑陋的大外框和背景色 */
  border: none;
  background: transparent;
  border-radius: 0;
}

.archive-table {
  width: 100%;
  min-width: 700px; /* 适当放宽以容纳年份 */
  border-collapse: separate; /* 使用 separate 以便实现优雅的行边框 */
  border-spacing: 0;
  font-size: 0.9rem; /* 恢复正常阅读字号 */
}

.archive-table th {
  padding: 1rem;
  text-align: left;
  border-bottom: 2px solid var(--vp-c-divider); /* 加粗表头底线 */
  font-weight: 800;
  color: var(--vp-c-text-2);
  white-space: nowrap;
  background: transparent; /* 移除表头背景色，融入页面 */
}

.archive-table td {
  padding: 1.2rem 1rem; /* 增加上下呼吸空间 */
  text-align: left;
  border-bottom: 1px solid var(--vp-c-divider);
  transition: background-color 0.2s ease;
}

/* 行悬停高亮，增强阅读感 */
.archive-table tbody tr:hover td {
  background-color: var(--vp-c-bg-soft);
}

.col-time { width: 160px; }
.col-symbol { width: 80px; }
.col-rating { width: 120px; }
.col-price { width: 100px; }
.col-upside { width: 100px; }
.col-manage { text-align: right !important; padding-right: 1.5rem !important; }

.action-btns { 
  display: flex; 
  gap: 0.8rem; /* 恢复舒适的按钮间距 */
  justify-content: flex-end;
}
.view-btn, .delete-btn {
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.archive-table th {
  padding: 1rem;
  text-align: left;
  border-bottom: 2px solid var(--vp-c-divider); /* 加粗表头底线 */
  font-weight: 800;
  color: var(--vp-c-text-2);
  white-space: nowrap;
  background: transparent; /* 移除表头背景色，融入页面 */
}

.sortable { cursor: pointer; user-select: none; }
.sortable:hover { color: var(--vp-c-brand); }
.sort-icon { font-size: 0.7rem; opacity: 0.5; }

.symbol-link { color: var(--vp-c-brand); text-decoration: none; }
.symbol-link:hover { text-decoration: underline; }

.rating-tag {
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
  background: var(--vp-c-bg-alt);
  display: inline-block;
  white-space: nowrap;
}
.rating-tag.strong-buy { background: rgba(67, 160, 71, 0.2); color: #43a047; }
.rating-tag.buy { background: rgba(67, 160, 71, 0.1); color: #43a047; }
.rating-tag.overweight { background: rgba(67, 160, 71, 0.1); color: #43a047; }
.rating-tag.hold { background: rgba(100, 100, 100, 0.1); color: #888; }
.rating-tag.underweight { background: rgba(211, 47, 47, 0.1); color: #d32f2f; }
.rating-tag.sell { background: rgba(211, 47, 47, 0.1); color: #d32f2f; }
.rating-tag.strong-sell { background: rgba(211, 47, 47, 0.2); color: #d32f2f; }

.up { color: #43a047; font-weight: 700; }
.down { color: #d32f2f; font-weight: 700; }

.actions-cell { text-align: right !important; }
.action-btns { 
  display: inline-flex; 
  gap: 0.6rem; 
  align-items: center;
  justify-content: flex-end;
}
.view-btn, .delete-btn {
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  text-decoration: none !important;
  white-space: nowrap;
}
.view-btn { 
  background: var(--vp-c-brand); 
  color: white !important; 
}
.view-btn:hover { transform: translateY(-1px); filter: brightness(1.1); }

.delete-btn { 
  background: none; 
  border: 1px solid var(--vp-c-divider); 
  color: var(--vp-c-text-3); 
}
.delete-btn:hover { 
  border-color: #d32f2f; 
  color: #d32f2f; 
  background: rgba(211, 47, 47, 0.05); 
}

.empty-state { padding: 4rem; text-align: center; color: var(--vp-c-text-3); font-style: italic; }
</style>
