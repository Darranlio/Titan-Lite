# 🚀 Titan-Lite 部署与运维手册 (V3.0)

## 1. 环境依赖
- **OS**: Linux (Ubuntu 22.04+ 推荐)
- **Runtime**: Docker & Docker Compose
- **Memory**: 最小 2G (推荐 4G 以获得更好的构建速度)

## 2. 快速部署

### 2.1 准备配置文件
在 `app/` 目录下创建 `.env` 文件：
```bash
LLM_API_KEY=sk-xxxx
DEEPSEEK_API_KEY=sk-xxxx
LLM_BASE_URL=https://api.deepseek.com
FINNHUB_API_KEY=xxxx
FMP_API_KEY=xxxx
WECOM_CORP_ID=xxxx
WECOM_CORP_SECRET=xxxx
```

### 2.2 启动服务
使用 Docker Compose 启动双容器架构（量化核心 + 知识库）：
```bash
docker-compose up -d --build
```

## 3. 运维常用指令

### 3.1 查看实时分析日志
```bash
docker logs -f titan_core
```

### 3.2 手动触发静态页构建
```bash
docker exec -it titan_core bash -c "cd /app/docs && npm run docs:build"
```

### 3.3 数据库与缓存清理
如果遇到 yfinance 数据陈旧，可以删除缓存：
```bash
rm -rf ~/.tradingagents/cache/*
```

## 4. 端口映射
- **8000**: FastAPI 后端接口
- **8080**: VitePress 研报档案馆

---
*Last Updated: 2026-05-10 | 基于 Docker-Compose 的一键式部署架构*
