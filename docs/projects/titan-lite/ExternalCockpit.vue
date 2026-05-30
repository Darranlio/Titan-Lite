<template>
  <div class="cockpit-container">
    <div class="cockpit-grid">
      <a :href="tvUrl" target="_blank" class="cockpit-item tv">
        <div class="icon">📈</div>
        <div class="text">
          <span class="name">TradingView</span>
          <span class="desc">实时 K 线与技术指标</span>
        </div>
      </a>
      
      <a :href="saUrl" target="_blank" class="cockpit-item sa">
        <div class="icon">📑</div>
        <div class="text">
          <span class="name">Seeking Alpha</span>
          <span class="desc">华尔街深度价值研报</span>
        </div>
      </a>
      
      <a :href="twUrl" target="_blank" class="cockpit-item x">
        <div class="icon">🐦</div>
        <div class="text">
          <span class="name">Twitter (X)</span>
          <span class="desc">实时情绪与 $Cashtag</span>
        </div>
      </a>
      
      <a :href="yfUrl" target="_blank" class="cockpit-item yf">
        <div class="icon">💰</div>
        <div class="text">
          <span class="name">Yahoo Finance</span>
          <span class="desc">完整财务报表与统计</span>
        </div>
      </a>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  symbol: String
})

// 处理港股代码兼容性 (如 0700.HK -> HKG:700 for TradingView)
const formattedSymbol = computed(() => {
  if (props.symbol.endsWith('.HK')) {
    const code = props.symbol.split('.')[0].replace(/^0+/, '')
    return `HKG:${code}`
  }
  return props.symbol
})

const tvUrl = computed(() => `https://www.tradingview.com/symbols/${formattedSymbol.value}/`)
const saUrl = computed(() => `https://seekingalpha.com/symbol/${props.symbol.split('.')[0]}`)
const twUrl = computed(() => `https://x.com/search?q=%24${props.symbol.split('.')[0]}`)
const yfUrl = computed(() => `https://finance.yahoo.com/quote/${props.symbol}`)
</script>

<style scoped>
.cockpit-container { margin: 1.5rem 0; }
.cockpit-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.cockpit-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 1rem;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  text-decoration: none !important;
  transition: all 0.2s ease;
}

.cockpit-item:hover {
  border-color: var(--vp-c-brand);
  background: var(--vp-c-bg-alt);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.icon { font-size: 1.5rem; }
.text { display: flex; flex-direction: column; }
.name { font-weight: 700; font-size: 0.95rem; color: var(--vp-c-text-1); }
.desc { font-size: 0.7rem; color: var(--vp-c-text-3); margin-top: 2px; }

/* 品牌色微调 */
.tv:hover { border-color: #2962ff; }
.sa:hover { border-color: #ff8c00; }
.x:hover { border-color: #000000; }
.yf:hover { border-color: #720e9e; }
</style>
