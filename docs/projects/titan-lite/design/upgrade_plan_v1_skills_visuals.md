# 🏗️ Titan-Lite 智力中枢与视觉化研报升级计划书 (V1)

| 🏷️ 属性 | 📄 内容 |
| :--- | :--- |
| **版本** | v1.0 |
| **状态** | 🟢 已存档 (Active Planning) |
| **关联模块** | Core Engine (4.4), Orchestrator (4.3), Persistence (4.5) |

## 1. 总体设计原则 (Core Principles)
*   **Skill-Centric (技能中心化)**：将 Prompt 从 Action 代码中剥离，沉淀为独立的专家剧本。实现“行动与智力”的深度解耦。
*   **Visual-Augmented (视觉增强)**：通过自动化绘图 Action 补齐专业研报的视觉缺口。
*   **Stateless Conductor (无状态指挥)**：保持 Orchestrator 的轻量化，仅负责调度，不存储智力逻辑。
*   **Delta-Driven (变量驱动)**：强制 AI 执行增量分析，重点在于“发生了什么变化”，而非“现状是什么”。

---

## 2. 分阶段实施路线图 (Implementation Roadmap)

### 第一阶段：智力底座 - Skill Engine 开发
**目标**：在 `Core Engine (4.4)` 层建立标准化的技能加载与渲染机制。

*   **任务 1.1**：创建 `app/skills/engine.py`。
    *   实现 `SkillEngine` 类：支持 Markdown 模板读取、变量 `{{var}}` 注入。
    *   实现 `ContextMixer`：根据当前日期动态混合“季节性常识（知识锚点）”。
*   **任务 1.2**：建立硬核常识库 `app/skills/knowledge_anchors.json`。
    *   内容：定义 Q1-Q4 的软性季节性倾向，作为可选的 Prior，非硬编码。
*   **自测验证方案**：
    *   编写 `tests/test_skill_engine.py`。
    *   **用例 1**：模拟不同月份，检查是否正确注入对应的季节性参考。
    *   **用例 2**：验证多变量替换，确保 `{{candidates}}` 等实时数据无缝填充。

### 第二阶段：视觉工厂 - Chart Painter 升级
**目标**：在 `Writers (4.5)` 层扩展资产生成能力，支持专业图表。

*   **任务 2.1**：实现行业热力图 Action (`FETCH_SECTOR_HEATMAP`)。
    *   集成 A 股行业流向 (AkShare) 与美股 ETF 表现 (yfinance)。生成 Bloomberg 风格的高清 PNG。
*   **任务 2.2**：实现个股价值散点图 Action (`VALUATION_SCATTER`)。
    *   利用 Discovery 阶段的 `candidates` 列表，展示 PE vs. Upside。
*   **自测验证方案**：
    *   编写 `scripts/debug_charts.py`。
    *   **用例**：手动传入模拟数据，验证图片是否成功生成并保存至 `docs/projects/titan-lite/reports/assets/`。

### 第三阶段：剧本编写 - "CIO Macro" 专家剧本
**目标**：编写第一份具备实战决策能力的技能说明书。

*   **任务 3.1**：起草 `app/skills/cio_macro_strategy.md`。
    *   逻辑要求：包含跨市场联动分析、变量分析指令、**明确的买卖决策模板**。
*   **自测验证方案**：
    *   **人工评审**：由用户审核逻辑深度，确保报告不再“假大空”。

### 第四阶段：流水线手术 - Orchestrator 链路集成
**目标**：按照 4.3 节定义，在任务拓扑中接入新节点，实现全链路贯通。

*   **任务 4.1**：修改 `app/orchestrator/workflows.py`。
    *   在 `market_scan` 任务中插入 `visualization_phase` 节点。
*   **任务 4.2**：改造 `app/orchestrator/actions.py` 中的 `PanoramaAction`。
    *   切换为调用 `SkillEngine.render_skill()`。
*   **自测验证方案**：
    *   **影子运行**：启动完整的 `Global` 扫描。
    *   **最终验收**：研报必须包含图表引用，且结尾有明确的 **“本周买入与调仓建议”** 列表。

---

## 3. 防御性约束与安全边界

1.  **路径安全**：严禁污染根目录，所有资产必须按 `user_id` 物理隔离。
2.  **降级保护**：若 Skill 加载失败，必须记录异常并 Fallback 到基础提示词，确保流程不中断。
3.  **依赖预检**：在执行前必须确认 `matplotlib`、`seaborn` 等库已安装。

---
*Last Updated: 2026-06-06 | Infrastructure Upgrade Task Force*
