---
# 页面配置
outline: deep
title: Titan-Lite 项目主页
---

# ⚡ Titan-Lite 量化交易系统

> 一个针对 **2C2G 低配云服务器** 优化的轻量级、容器化量化交易系统。
> 
> *“让数学模型代替情绪，在云端 24小时为我打工。”*

![Status](https://img.shields.io/badge/Status-Active_Development-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

## 📂 项目导航

这里是项目的核心文档入口，请根据需要查阅：

| 模块 | 说明 | 链接 |
| :--- | :--- | :--- |
| **📊 架构设计** | 系统的顶层设计、数据流向与数学模型公式 | [查看文档](./design_doc.md) |
| **🧠 策略算法** | 卡尔曼滤波、Z-Score 信号生成逻辑 (施工中) | [查看文档](./strategy.md) |
| **🔌 API 接口** | 后端 FastAPI 接口定义与调用方式 (施工中) | [查看文档](./api.md) |
| **🚀 部署运维** | Docker 常用指令、环境恢复与日志查看 (施工中) | [查看文档](./deploy.md) |

---

## 🛠️ 技术栈概览

本系统采用 **微服务架构**，主要包含以下组件：

- **Quant Core**: 基于 `Python` + `Pandas` + `Kalman Filter` 的策略计算核心。
- **Data Engine**: 封装 `AkShare`，实现带重试机制的数据清洗与存储。
- **Notification**: 集成 **企业微信** Webhook，实现交易信号实时推送。
- **Web UI**: 基于 `VitePress` (即本网站) 的静态知识库与仪表盘。

## 📅 近期开发计划

- [x] **Phase 1**: 基础环境搭建 (Docker, Nginx, Python)
- [x] **Phase 2**: 知识库 Wiki 上线
- [ ] **Phase 3**: 策略回测模块开发 (进行中...)
- [ ] **Phase 4**: 实盘信号对接

---

::: tip 💡 提示
点击左侧侧边栏的菜单，可以快速切换不同章节的文档。
:::