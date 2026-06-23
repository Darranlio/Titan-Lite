<template>
  <div class="artifacts-container">
    <div class="artifact-card">
      <div class="title">🚀 Titan-Alpha 产出资产 (Artifacts)</div>
      <div class="buttons">
        <button @click="viewWeChatPost" class="btn post-btn">
          📝 提取公众号草稿
        </button>
        <button @click="viewTradeJSON" class="btn json-btn">
          🛠️ 查看交易指令 (JSON)
        </button>
        <a :href="csvUrl" download class="btn csv-btn">
          📊 下载估值模型 (CSV)
        </a>
      </div>
    </div>

    <!-- WeChat Post Modal -->
    <div v-if="showPostModal" class="modal-overlay" @click="showPostModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>公众号推文草稿 (wechat_post.md)</h3>
          <button @click="showPostModal = false" class="close-btn">&times;</button>
        </div>
        <div class="post-viewer">
          <pre>{{ postContent }}</pre>
        </div>
        <div class="modal-footer">
          <button @click="copyPostContent" class="btn post-btn">
            {{ postCopied ? '✅ 已复制全文' : '📋 复制全文' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Trade JSON Modal -->
    <div v-if="showJSONModal" class="modal-overlay" @click="showJSONModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>机器可读交易指令 (trade.json)</h3>
          <button @click="showJSONModal = false" class="close-btn">&times;</button>
        </div>
        <pre class="json-viewer">{{ tradeJSON }}</pre>
        <div class="modal-footer">
          <button @click="copyTradeJSON" class="btn sm-btn">复制 JSON</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { showToast } from './hooks/useUI.js'

const props = defineProps({
  symbol: String,
  date: String
})

const showPostModal = ref(false)
const postContent = ref('')
const postCopied = ref(false)

const showJSONModal = ref(false)
const tradeJSON = ref('')

const csvUrl = ref('')
const tradeUrl = ref('')
const postUrl = ref('')

onMounted(() => {
  // 动态构建路径，兼容 /reports/ 和 /users/xxx/reports/
  const path = window.location.pathname
  const isUserReport = path.includes('/users/')
  
  let baseUrl = ''
  if (isUserReport) {
    // 提取 /projects/titan-lite/users/xxx/reports/symbol/
    const parts = path.split('/')
    const userIndex = parts.indexOf('users')
    const username = parts[userIndex + 1]
    baseUrl = `/projects/titan-lite/users/${username}/reports/${props.symbol}`
  } else {
    baseUrl = `/projects/titan-lite/reports/${props.symbol}`
  }

  csvUrl.value = `${baseUrl}/valuation_model.csv`
  tradeUrl.value = `${baseUrl}/trade.json`
  postUrl.value = `${baseUrl}/wechat_post.md`
})

const viewWeChatPost = async () => {
  try {
    const response = await fetch(postUrl.value)
    if (!response.ok) throw new Error()
    postContent.value = await response.text()
    showPostModal.value = true
  } catch (e) {
    showToast("无法加载公众号草稿，请检查文件是否存在。", "error")
  }
}

const copyPostContent = async () => {
  try {
    await navigator.clipboard.writeText(postContent.value)
    postCopied.value = true
    setTimeout(() => postCopied.value = false, 2000)
    showToast("全文已复制到剪贴板", "success")
  } catch (e) {
    showToast("复制失败", "error")
  }
}

const viewTradeJSON = async () => {
  try {
    const response = await fetch(tradeUrl.value)
    if (!response.ok) throw new Error()
    const data = await response.json()
    tradeJSON.value = JSON.stringify(data, null, 4)
    showJSONModal.value = true
  } catch (e) {
    showToast("无法加载交易指令，请确认 trade.json 已生成。", "error")
  }
}

const copyTradeJSON = () => {
  navigator.clipboard.writeText(tradeJSON.value)
  showToast("JSON 已复制", "success")
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
  transition: all 0.2s;
}
.btn:hover { transform: translateY(-1px); filter: brightness(1.1); }

.post-btn { background: #43a047; color: white; }
.json-btn { background: var(--vp-c-bg-alt); color: var(--vp-c-text-1); border: 1px solid var(--vp-c-divider); }
.csv-btn { background: var(--vp-c-brand-soft); color: var(--vp-c-brand); display: flex; align-items: center; }

.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.7);
  display: flex; justify-content: center; align-items: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}
.modal-content {
  background: var(--vp-c-bg);
  padding: 1.5rem;
  border-radius: 16px;
  max-width: 800px;
  width: 90%;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  position: relative;
  box-shadow: 0 20px 40px rgba(0,0,0,0.3);
}
.modal-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--vp-c-divider);
}
.modal-header h3 { margin: 0; font-size: 1.2rem; }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: var(--vp-c-text-3); }

.post-viewer, .json-viewer {
  background: var(--vp-c-bg-alt);
  padding: 1rem;
  border-radius: 8px;
  overflow-y: auto;
  flex: 1;
  font-family: var(--vp-font-family-mono);
  font-size: 0.9rem;
  line-height: 1.6;
}

.post-viewer pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  color: var(--vp-c-text-1);
}

.json-viewer {
  background: #1e1e1e;
  color: #dcdcdc;
  margin: 0;
}

.modal-footer {
  margin-top: 1.2rem;
  display: flex;
  justify-content: flex-end;
}

.sm-btn { background: var(--vp-c-brand); color: white; padding: 0.5rem 1.5rem; }
</style>

