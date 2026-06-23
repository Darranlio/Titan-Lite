<template>
  <div class="history-manager-container">
    <div class="table-wrapper">
      <table class="history-table">
        <thead>
          <tr>
            <th class="col-time">研判时间</th>
            <th class="col-rating">结论评级</th>
            <th class="col-price">价格</th>
            <th class="col-upside">预期涨幅</th>
            <th class="col-score">可信度评分</th>
            <th class="col-manage">档案管理</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="h in historyData" :key="h.file || h.date">
            <td class="small-text">{{ formatTime(h.file || h.date) }}</td>
            <td><span class="rating-tag" :class="h.rating.toLowerCase().replace(' ', '-')">{{ h.rating }}</span></td>
            <td class="tabular">${{ h.price }}</td>
            <td class="tabular" :class="(h.upside || 0) > 0 ? 'up' : 'down'">{{ ((h.upside || 0) * 100).toFixed(2) }}%</td>
            <td class="tabular">{{ h.fact_score || '-' }}</td>
            <td class="actions-cell">
              <div class="action-btns">
                <a :href="`./${h.file || h.date}`" class="view-btn">阅读正文</a>
                <button @click="deleteReport(h.file || h.date)" class="delete-btn">删除该期</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="historyData.length === 0" class="empty-state">
        暂无历史研报记录。
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { showToast, showConfirm } from './hooks/useUI.js'

const props = defineProps({
  symbol: String
})

const historyData = ref([])

const API_BASE = typeof window !== 'undefined' 
  ? `${window.location.protocol}//${window.location.hostname}:8000` 
  : 'http://localhost:8000'

// 假设 metadata.json 会在 VitePress 构建后作为一个静态资源可通过当前目录访问
const metaUrl = `./metadata.json`

const fetchHistory = async () => {
  try {
    // 加载当前目录下的 metadata.json 并附加一个时间戳防止缓存
    const response = await fetch(`${metaUrl}?t=${new Date().getTime()}`)
    if (response.ok) {
      historyData.value = await response.json()
    }
  } catch (e) {
    console.error("无法加载历史记录", e)
  }
}

onMounted(fetchHistory)

const deleteReport = async (fileTs) => {
  const confirmed = await showConfirm(`确定要永久删除这份 ${fileTs} 的研报吗？该操作不可逆。`)
  if (!confirmed) return
  try {
    const savedToken = localStorage.getItem('titan_token')
    const headers = savedToken ? { 'Authorization': `Bearer ${savedToken}` } : {}
    const res = await (await fetch(`${API_BASE}/archive/${props.symbol}/${fileTs}`, { method: 'DELETE', headers })).json()
    showToast(res.msg)
    // 重新获取数据以刷新表格
    await fetchHistory()
  } catch (e) {
    showToast("删除失败，请检查后端服务是否运行。", "error")
  }
}

const formatTime = (ts) => {
  if (!ts) return '-'
  return ts.replace('_', ' ')
}
</script>

<style scoped>
.history-manager-container { margin-top: 1rem; width: 100%; }

.table-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  width: 100%;
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  background: var(--vp-c-bg-soft);
}

.history-table {
  width: 100%;
  min-width: 600px;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.history-table th, .history-table td {
  padding: 0.8rem 1rem;
  text-align: left;
  border-bottom: 1px solid var(--vp-c-divider);
}

.history-table th {
  background: var(--vp-c-bg-alt);
  font-weight: 800;
  color: var(--vp-c-text-2);
  white-space: nowrap;
}

.history-table tbody tr:hover td {
  background-color: var(--vp-c-bg-alt);
}

.col-time { width: 140px; }
.col-rating { width: 120px; }
.col-price { width: 80px; }
.col-upside { width: 80px; }
.col-score { width: 80px; }
.col-manage { text-align: right !important; padding-right: 1.5rem !important; }

.rating-tag {
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
  background: var(--vp-c-bg-alt);
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
.tabular { font-family: 'JetBrains Mono', monospace; }

.actions-cell { text-align: right !important; }
.action-btns { 
  display: inline-flex; 
  gap: 0.6rem; 
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
  transition: all 0.2s;
}

.view-btn { 
  background: var(--vp-c-brand-soft); 
  color: var(--vp-c-brand) !important; 
  border: 1px solid var(--vp-c-brand);
}
.view-btn:hover { background: var(--vp-c-brand); color: white !important; }

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

.empty-state { padding: 3rem; text-align: center; color: var(--vp-c-text-3); font-style: italic; }
</style>
