# ⚙️ Orchestrator

| 🏷️ 属性 | 📄 内容 |
| :--- | :--- |
| **模块编号** |   4.3 |
| **版本** |   v4.0 |
| **状态** | 🟢 定稿 |

---

## 1. 核心架构理念 (Core Architecture)

Orchestrator 的核心价值在于将 Titan-Lite 的三项核心能力（扫描、研判、审计）标准化。系统通过 **Task (任务)** 承载业务目标，每个 Task 由一系列具有依赖关系的 **Action (动作)** 组成。

引入 **类型化上下文 (Typed Context)**、**显式注册机制** 以及 **分片锁与活跃资源集合 (Active Resources Shard Lock)**，能有效防止因大模型高吞吐导致的写冲突，更从架构层面保障了投研资产的强一致性。

*   **解耦化 (Decoupling)**：Action 仅关注单一数据维度的获取或处理，Action 之间不直接通信，所有交互均通过 Context 完成。
*   **流程化 (Workflow-driven)**：Task 通过 DSL 定义 Action 的执行拓扑（串行/并行），通过静态依赖检查确保闭环。
*   **标准化 (Standardization)**：统一通过 `ActionContext` 进行数据交换，支持生产级的强壮性与容错能力。

### 1.1 执行模式：双模引擎 (Execution Patterns)
Orchestrator 支持两种调用范式，共享同一套原子动作库与分片锁机制，确保数据强一致性：

1.  **交互模式 (Direct Action Mode)**：
    *   **场景**：用户在 UI 点击“录入交易”、“立即同步账本”或“查询实时金价”。
    *   **特性**：跳过 Workflow 引擎，由 API 直接触发单个 Action。通常为阻塞/半阻塞调用，支持立即返回执行结果。
2.  **任务模式 (Orchestrated Task Mode)**：
    *   **场景**：每日定时研报生成、全量市场扫描、持仓深度审计。
    *   **特性**：由 Workflow 引擎驱动，严格按照 DAG 拓扑执行。通常为异步非阻塞调用，通过 `job_id` 追踪状态。

---

## 2. 任务体系 (Task Management)

### 2.1 任务定义 (Workflow DSL)
Task 是业务逻辑的顶层封装。采用结构化配置定义执行序列，支持并行组 (`Group`) 和串行链 (`Chain`)。

```json
{
  "task_id": "DEEP_DIVE_v1",
  "steps": [
    { "id": "step1", "actions": ["FETCH_FINANCIALS", "FETCH_NEWS"], "mode": "PARALLEL" },
    { "id": "step2", "actions": ["VERIFY_FACTS"], "depends_on": "step1" },
    { "id": "step3", "actions": ["GENERATE_REPORT"], "depends_on": "step2" }
  ]
}
```

### 2.2 静态拓扑校验器 (DAG Validator)
为了保障 Workflow 的合法性，在启动前必须通过 `WorkflowValidator` 进行核验：

1.  **循环依赖检测**：使用 **Kahn 算法 (入度统计)** 确保 Task 无环。
2.  **数据契约闭环验证**：追踪 `provided_assets` 集合。初始输入为 `{symbol}`。
3.  **核验逻辑**：遍历拓扑排序序列，确保每个 Action 所需的 `inputs` 均已在之前的步骤中产出。

### 2.3 当前核心任务列表 (Current Tasks)

| 任务 ID | 业务名称 | 核心逻辑流 |
| :--- | :--- | :--- |
| **T1** | **市场全量扫描** | 获取行业 -> 并行扫描成分股 -> 财务/龙头过滤 -> 整合社交热度标的 |
| **T2** | **个股深度研判** | 并行抓取财务估值与新闻 -> AI 事实提取 -> 预期涨幅计算 -> 生成结构化报告 |
| **T3** | **持仓健康审计** | **同步账本 (SYNC)** -> **净值核算 (NAV)** -> 宏观对齐 -> 逻辑验证 -> 组合诊断 |

---

## 3. 原子动作库 (Action Library)

### 3.1 动作注册机制 (Action Registration)
Action 是系统最小的执行单元。每一个 Action 必须显式声明其输入输出，并继承 `BaseAction`。

```python
@ActionRegistry.register("FETCH_FINANCIALS")
class FetchFinancialsAction(BaseAction):
    inputs = ["symbol"]
    outputs = ["financial_data"]
    
    async def run(self, ctx):
        # 执行单一职责逻辑 (Reader/Analyzer 调用)
        return {"financial_data": data}
```

### 3.2 深度设计优化补丁 (Action Optimizations)
针对 Action 执行过程中的健壮性优化：

*   **命名空间隔离**：`payload_by_action` 以 `Action_Name` 为存储 Key，彻底解决长链路 DAG 中的数据覆盖风险。
*   **幂等性与中间态缓存**：引入基于 `Action_Name + Input_Params_Hash` 的轻量级本地缓存（如 SQLite KV），支持高成本动作（如 AI 辩论）的断点续传，保护 API 配额。

### 3.3 动作清单索引 (Action Inventory)

| 动作 ID | 分类 | 输入 | 输出 |
| :--- | :--- | :--- | :--- |
| `SYNC_LEDGER` | **账本维护** | None | `raw_transactions` |
| `RECORD_TRADE` | **账本维护** | `symbol`, `side`, `qty`, `price` | `tx_status` |
| `CALC_NAV` | **组合核算** | `raw_transactions` | `portfolio_status` |
| `FETCH_SECTORS` | 数据采集 | None | `sectors_list` |
| `FETCH_SECTOR_STOCKS`| 数据采集 | `sector` | `raw_stocks_df` |
| `FILTER_FINANCIALS` | 数据处理 | `raw_stocks_df` | `filtered_stocks_df` |
| `FETCH_FMP_DATA` | 机构数据 | `symbol` | `fmp_metrics` |
| `LLM_NEWS_ANALYZE` | AI 推理 | `news_list` | `news_analysis` |
| `GENERATE_REPORT` | 内容生成 | `valuation_report`, `news_analysis` | `final_report_md` |

---

## 4. 数据契约：ActionContext (协程安全)

### 4.1 设计思想
*   **写时复制 (Copy-on-Write)**：Action 读取到的数据快照在执行期间不可变。
*   **命名空间隔离**：物理隔离并行 Actions 的输出，确保数据溯源清晰。
*   **协程安全**：内置 `asyncio.Lock` 保证高并发状态更新的原子性。

### 4.2 数据模型
```python
class ActionContext(BaseModel):
    job_id: str
    ticker: str
    payload_by_action: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    _lock: asyncio.Lock = Field(default_factory=asyncio.Lock, exclude=True)
```

---

## 5. 开发里程碑与计划 (MVP)

1.  **Phase 1**: 实现 `ActionRegistry` 与具有命名空间隔离的 `ActionContext`。
2.  **Phase 2**: 实现 `WorkflowValidator` (Kahn 算法) 与 `TitanWorkflowEngine` 的异步调度系统。
3.  **Phase 3**: 迁移 T2 深度研判任务，对接外部 Interfaces 模块。
