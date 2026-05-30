<template>
  <div class="artifacts-container">
    <div class="artifact-card">
      <div class="title">🚀 Titan-Alpha 产出资产 (Artifacts)</div>
      <div class="buttons">
        <button @click="copyWeChatPost" class="btn post-btn">
          {{ copied ? '✅ 已复制' : '📝 提取公众号草稿' }}
        </button>
        <button @click="viewTradeJSON" class="btn json-btn">
          🛠️ 查看交易指令 (JSON)
        </button>
        <a :href="csvUrl" download class="btn csv-btn">
          📊 下载估值模型 (CSV)
        </a>
      </div>
    </div>

    <!-- Trade JSON Modal -->
    <div v-if="showModal" class="modal-overlay" @click="showModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>机器可读交易指令 (trade.json)</h3>
          <button @click="showModal = false" class="close-btn">&times;</button>
        </div>
        <pre class="json-viewer">{{ tradeJSON }}</pre>
        <button @click="copyTradeJSON" class="btn sm-btn">复制 JSON</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  symbol: String,
  date: String
})

const copied = ref(false)
const showModal = ref(false)
const tradeJSON = ref('')

// 注意：在 VitePress 中，我们要构建相对于静态文件的路径
// 假设 reports 目录在 build 后可以通过链接访问
const baseUrl = `/projects/titan-lite/reports/${props.symbol}`
const csvUrl = `${baseUrl}/valuation_model.csv`
const tradeUrl = `${baseUrl}/trade.json`
const postUrl = `${baseUrl}/wechat_post.md`

const copyWeChatPost = async () => {
  try {
    const response = await fetch(postUrl)
    const text = await response.text()
    await navigator.clipboard.writeText(text)
    copied.value = true
    setTimeout(() => copied.value = false, 2000)
  } catch (e) {
    alert("提取失败，请确保报告已生成。")
  }
}

const viewTradeJSON = async () => {
  try {
    const response = await fetch(tradeUrl)
    const data = await response.json()
    tradeJSON.value = JSON.stringify(data, null, 4)
    showModal.value = true
  } catch (e) {
    alert("加载指令失败。")
  }
}

const copyTradeJSON = () => {
  navigator.clipboard.writeText(tradeJSON.value)
  alert("JSON 已复制")
}
</script>

<style scoped>
.artifacts-container { margin: 2rem 0; }
.artifact-card {
  background: var(--vp-c-bg-soft);
  border: 2px solid var(--vp-c-brand);
  border-radius: 12px;
  padding: 1.5rem;
}
.artifact-card .title {
  font-weight: 800;
  margin-bottom: 1.2rem;
  color: var(--vp-c-brand);
}
.buttons { display: flex; gap: 1rem; flex-wrap: wrap; }
.btn {
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-size: 0.9rem;
  text-decoration: none !important;
}
.post-btn { background: #43a047; color: white; }
.json-btn { background: var(--vp-c-bg-alt); color: var(--vp-c-text-1); border: 1px solid var(--vp-c-divider); }
.csv-btn { background: var(--vp-c-brand-soft); color: var(--vp-c-brand); }

.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.6);
  display: flex; justify-content: center; align-items: center;
  z-index: 1000;
}
.modal-content {
  background: var(--vp-c-bg);
  padding: 2rem;
  border-radius: 16px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  position: relative;
}
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: var(--vp-c-text-3); }
.json-viewer {
  background: #1e1e1e;
  color: #dcdcdc;
  padding: 1rem;
  border-radius: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  overflow-x: auto;
  margin-bottom: 1.5rem;
}
.sm-btn { background: var(--vp-c-brand); color: white; padding: 0.4rem 1rem; }
</style>
