---
outline: deep
title: Titan-Lite 交易系统
---

<script setup>
import ControlPanel from './ControlPanel.vue'
</script>

<div class="project-hero">
  <img src="/logo.svg" class="project-logo" alt="Titan Logo" />
  <h1>⚡ Titan-Lite 量化研报系统</h1>
  <p class="tagline">基于 DeepSeek 认知博弈架构的个人投资决策终端</p>
</div>

---

## 📂 快速操作面板 (Control Panel)

<ControlPanel />

---

## 📖 项目导航

这里是系统的核心模块入口，请点击查阅详细研报或设计规范：

| 模块 | 说明 | 链接 |
| :--- | :--- | :--- |
| **🏦 我的基金** | 个人资产管理、净值核算、AI 组合诊断 | [进入中心](./portfolio.md) |
| **📑 研报档案** | 深度个股研报、动态 Dashboard、历史评级 | [进入档案馆](./reports/index.md) |
| **📊 架构设计** | 系统的顶层设计、数据流向与数学模型公式 | [查看文档](./design/design_doc.md) |
| **🧠 策略算法** | 认知博弈、多智能体辩论与宏观分析逻辑 | [查看文档](./design/strategy.md) |
| **🔌 API 接口** | 后端 FastAPI 接口定义与调用方式 | [查看文档](./design/api.md) |
| 🚀 部署运维 | Docker 常用指令、环境恢复与日志查看 | [查看文档](./design/deploy.md) |
| **📖 使用手册** | 系统日常操作、命令速查 | [查看文档](./design/usage_guide.md) |

---

## 👨‍💻 关于作者 (About Author)

<div class="author-card">
  <img src="/avatar.png" class="author-avatar" alt="Author Avatar" />
  <div class="author-info">
    <strong>Darranlio</strong>
    <p>美团无人机感知算法工程师 | 量化投资探索者</p>
    <div class="author-links">
      <a href="mailto:1059390428@qq.com">📧 联系我</a> | 
      <a href="https://github.com/Darranlio" target="_blank">🐙 GitHub</a>
    </div>
  </div>
</div>

<style scoped>
.project-hero {
  text-align: center;
  padding: 4rem 0;
  background: radial-gradient(circle at top, var(--vp-c-bg-soft) 0%, transparent 70%);
  border-radius: 24px;
  margin-bottom: 3rem;
  border: 1px solid var(--vp-c-divider);
}
.project-logo {
  width: 140px;
  margin: 0 auto 2rem;
  filter: drop-shadow(0 0 30px rgba(0, 163, 255, 0.3));
  transition: transform 0.3s ease;
}
.project-logo:hover {
  transform: scale(1.05);
}
.project-hero h1 {
  font-size: 3rem;
  margin-bottom: 0.75rem;
  font-weight: 800;
  background: linear-gradient(120deg, #41d1ff 30%, #bd34fe);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.tagline {
  font-size: 1.3rem;
  color: var(--vp-c-text-2);
  max-width: 600px;
  margin: 0 auto;
}

.author-card {
  margin-top: 5rem;
  padding: 2rem;
  background: var(--vp-c-bg-alt);
  border-radius: 16px;
  display: flex;
  align-items: center;
  gap: 2rem;
  border: 1px solid var(--vp-c-divider);
  transition: border-color 0.3s;
}
.author-card:hover {
  border-color: var(--vp-c-brand);
}
.author-avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  border: 3px solid var(--vp-c-brand);
  object-fit: cover;
  flex-shrink: 0;
  background: var(--vp-c-bg);
}
.author-info strong {
  font-size: 1.4rem;
  display: block;
  margin-bottom: 0.5rem;
  color: var(--vp-c-text-1);
}
.author-info p {
  font-size: 1rem;
  color: var(--vp-c-text-2);
  margin-bottom: 1.2rem;
}
.author-links {
  display: flex;
  gap: 1.5rem;
}
.author-links a {
  text-decoration: none;
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--vp-c-brand);
}
.author-links a:hover {
  text-decoration: underline;
}
</style>