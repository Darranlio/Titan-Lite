---
# 页面配置
outline: deep
title: Titan-Lite 项目主页
---

<script setup>
import ControlPanel from './ControlPanel.vue'
</script>

# ⚡ Titan-Lite 量化交易系统

> 一个针对 **2C2G 低配云服务器** 优化的轻量级、容器化量化交易系统。
> 
> *“让数学模型代替情绪，在云端 24小时为我打工。”*

![Status](https://img.shields.io/badge/Status-Active_Development-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

## 📂 项目导航

<ControlPanel />

这里是项目的核心文档入口，请根据需要查阅：

| 模块 | 说明 | 链接 |
| :--- | :--- | :--- |
| **📑 研报档案** | 深度个股研报、动态 Dashboard、历史评级 | [进入档案馆](./reports/index.md) |
| **📊 架构设计** | 系统的顶层设计、数据流向与数学模型公式 | [查看文档](./design/design_doc.md) |
| **🧠 策略算法** | 卡尔曼滤波、Z-Score 信号生成逻辑 | [查看文档](./design/strategy.md) |
| **🔌 API 接口** | 后端 FastAPI 接口定义与调用方式 | [查看文档](./design/api.md) |
| 🚀 部署运维 | Docker 常用指令、环境恢复与日志查看 | [查看文档](./design/deploy.md) |
| **📖 使用手册** | 系统日常操作、命令速查 | [查看文档](./design/usage_guide.md) |

---

::: tip 💡 提示
点击左侧侧边栏的菜单，可以快速切换不同章节的文档。
:::