---
layout: home
prev: false
next: false

hero:
  name: "Digital Asset Lab"
  text: "Professional Quant & AI Solutions"
  tagline: "基于 DeepSeek 认知博弈架构的个人投资决策终端"
  image:
    src: /logo.svg
    alt: Digital Asset Lab
  actions:
    - theme: brand
      text: 🏦 我的基金中心
      link: /projects/titan-lite/portfolio
    - theme: alt
      text: 📑 研报档案馆
      link: /projects/titan-lite/reports/index

---

<script setup>
import ControlPanel from './projects/titan-lite/ControlPanel.vue'
</script>

<div class="author-panel-bridge">
  <div class="author-identity">
    <img src="/avatar.png" class="author-large-avatar" alt="Darranlio" />
    <div class="author-meta">
      <span class="author-name-text">Darranlio</span>
      <span class="author-title-text">美团 UAV 感知算法工程师 | 量化投资探索者</span>
    </div>
  </div>
  <div class="author-contact-actions">
    <a href="javascript:void(0)" @click="window.alert('Email: sakuraperception@gmail.com')" class="contact-action-link">📧 Email</a>
    <a href="https://github.com/Darranlio" target="_blank" class="contact-action-link">🐙 GitHub</a>
  </div>
</div>

---

## 📂 快速操作面板 (Quick Action)
<ControlPanel />

---

## 🛠️ 系统核心入口 (Core Modules)

| 核心模块 | 描述 | 状态 |
| :--- | :--- | :--- |
| [**🏦 我的基金**](/projects/titan-lite/portfolio) | 个人资产管理、单位净值核算、AI 组合诊断 | 🟢 实时运行 |
| [**📑 研报档案**](/projects/titan-lite/reports/index) | 深度个股研报、动态 Dashboard、历史评级 | 🟢 自动更新 |
| [**🌏 宏观视角**](/projects/titan-lite/reports/market_overview) | 全球资金流向研判、行业景气度透视 | 🟢 每日更新 |
| [**🏛️ 系统原理**](/projects/titan-lite/design/architecture_theory) | 认知博弈、分级研判与净值化原理 | 📜 核心文档 |
| [**🛠️ 施工细节**](/projects/titan-lite/design/ui_logic_spec) | UI布局、按钮逻辑与数据库规范 | 🛠️ 施工蓝图 |
| [**🔌 API 接口**](/projects/titan-lite/design/api) | 后端 FastAPI 接口定义与调用方式 | 📖 技术手册 |

<style>
:root {
  --vp-home-hero-image-image-size: 200px; 
}

/* 恢复 Hero 区域居中 (默认样式) */
.VPHero {
  text-align: center !important;
}

.VPHero .image-src {
  filter: drop-shadow(0 0 60px rgba(0, 163, 255, 0.4));
}

.VPHero .name {
  background: -webkit-linear-gradient(120deg, #41d1ff 30%, #bd34fe);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* 仅作者面板左对齐 */
.author-panel-bridge {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 750px;
  margin: 1rem 0 4rem; /* 核心：左边距 0，右边距 auto 实现左对齐 */
  padding: 1.5rem 2rem;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.15);
  backdrop-filter: blur(10px);
  z-index: 10;
  position: relative;
}

.author-identity {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.author-large-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: 3px solid var(--vp-c-brand);
  background: var(--vp-c-bg);
}

.author-meta {
  display: flex;
  flex-direction: column;
  text-align: left; /* 内部文字左对齐 */
}

.author-name-text {
  font-size: 1.2rem;
  font-weight: 800;
  color: var(--vp-c-text-1);
}

.author-title-text {
  font-size: 0.9rem;
  color: var(--vp-c-text-2);
}

.author-contact-actions {
  display: flex;
  gap: 1rem;
}

.contact-action-link {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--vp-c-brand);
  text-decoration: none;
  padding: 0.4rem 1rem;
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.contact-action-link:hover {
  background: var(--vp-c-brand);
  color: white;
}

/* 响应式：移动端居中 */
@media (max-width: 960px) {
  .author-panel-bridge {
    margin: 1rem auto 3rem;
    flex-direction: column;
    text-align: center;
    gap: 1.5rem;
  }
  .author-meta {
    text-align: center;
  }
}
</style>
