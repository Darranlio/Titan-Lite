<script setup>
import { ref } from 'vue'

const status = ref('')
const loading = ref(false)

const runAnalysis = async () => {
  loading.value = true
  status.value = '正在启动 Titan-Lite V2.1 深度扫描与研判...'
  try {
    // 这里的 URL 换成你服务器的真实 IP
    const response = await fetch('http://your-server-ip:8000/run', {
      method: 'POST'
    })
    const data = await response.json()
    status.value = '分析已触发！请在 5-10 分钟后刷新页面查看新研报。'
  } catch (error) {
    status.value = '启动失败，请检查后端服务是否在线。'
    console.error(error)
  } finally {
    loading.value = false
  }
}
</script>

<div class="control-panel">
  <h2>🚀 策略控制台</h2>
  <p>点击下方按钮手动触发全市场深度研判。系统将自动进行：标的发现 -> 估值筛选 -> AI 事实核查 -> 多智能体辩论。</p>
  
  <button 
    @click="runAnalysis" 
    :disabled="loading"
    class="run-btn"
  >
    {{ loading ? '研判进行中...' : '立即运行深度分析' }}
  </button>

  <p v-if="status" class="status-msg">{{ status }}</p>
</div>

<style scoped>
.control-panel {
  padding: 1.5rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  background-color: var(--vp-c-bg-soft);
  margin: 2rem 0;
}
.run-btn {
  background-color: var(--vp-c-brand);
  color: white;
  padding: 0.6rem 1.2rem;
  border-radius: 4px;
  font-weight: bold;
  cursor: pointer;
  transition: opacity 0.2s;
  margin-top: 1rem;
}
.run-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.status-msg {
  margin-top: 1rem;
  font-size: 0.9rem;
  color: var(--vp-c-brand);
}
</style>
