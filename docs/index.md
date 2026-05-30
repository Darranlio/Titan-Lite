---
layout: home
prev: false
next: false
---

<script setup>
import ControlPanel from './projects/titan-lite/ControlPanel.vue'
import UnifiedHero from './projects/titan-lite/UnifiedHero.vue'
</script>

<UnifiedHero />

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
</style>
