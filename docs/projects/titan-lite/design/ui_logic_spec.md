# 🛠️ Titan-Lite 施工细节与 UI 逻辑规范

## 1. 首页控制中心 (`ControlPanel.vue`)

### 1.1 布局规划
- **左对齐 Hero 区**：品牌 Logo、愿景、作者面板。
- **两列网格**：左侧为“全市场扫描”卡片，右侧为“个股专项研判”卡片。

### 1.2 功能按钮逻辑
- **[开始全市场扫描]**：
    - **API**: `POST /run`
    - **后端行为**：触发 `strategy.execute()`。执行分级研判流水线。
    - **UI反馈**：按钮进入 Loading 状态，状态文字提示“正在启动...耗时5-10分钟”。
- **[深度研判] (个股)**：
    - **API**: `POST /analyze/{ticker}`
    - **后端行为**：调用 `strategy.analyze_single_ticker(symbol)`。跳过初筛和快筛，直奔多智能体深研。

---

## 2. 基金管理中心 (`FundManager.vue`)

### 2.1 资产看板
- **NAV 仪表盘**：显示单位净值、总市值、累计盈亏。
- **SVG 净值图**：基于 `nav_history` 表数据，动态绘制折线图。

### 2.2 交易功能
- **按钮 [提交成交]**：
    - **API**: `POST /portfolio/trade`
    - **表单项**：Symbol, Side(BUY/SELL), Quantity, Price.
    - **数据流**：写入 SQLite `transactions` 流水表 -> 触发 `positions` 持仓表重算 -> 异步更新 `nav_history`。

### 2.3 智能诊断
- **按钮 [生成深度诊断报告]**：
    - **API**: `GET /portfolio/diagnosis`
    - **逻辑**：读取当前持仓 + 最新的 `market_overview.md` -> 喂给 DeepSeek -> 渲染 Markdown 诊断结果。

---

## 3. 档案馆自动生成逻辑 (`strategy.py`)

### 3.1 目录结构实现
- `reports/[SYMBOL]/index.md`: **个股 Dashboard**。
    - 包含：公司 DNA、财务红绿灯、回测 Alpha、指标演变表。
    - **导航**：底部放置 `[⬅️ 返回研报历史库]`，与 Pager 并列。
- `reports/[SYMBOL]/YYYY-MM-DD.md`: **日度深度报告**。
    - 包含：专家透视、多空博弈、投资课堂。
    - **导航**：底部放置 `[⬅️ 返回 [SYMBOL] 看板]`，与 Pager 并列。

### 3.2 宏观全景生成
- **汇总时机**：在所有个股扫描完成后。
- **数据源**：聚合本次所有标的的板块分布 + 外部大盘指数表现。
- **文件**：`reports/market_overview.md` (最新快照) 和 `reports/macro/YYYY-MM-DD.md` (历史)。

---

## 4. 数据库规范 (`vault.db`)
- **transactions**: 交易流水
- **positions**: 当前持仓（含加权成本）
- **nav_history**: 每日净值快照
- **research_reports**: 结构化研报（含 Markdown 文本和 Agent 原始 JSON）

---
*所有代码修改必须严格遵守本施工文档定义的 API 映射与数据结构。*
