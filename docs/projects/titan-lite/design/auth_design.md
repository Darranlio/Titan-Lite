# 🔐 Multi-User & Auth - 权限管理模块详细设计

| 🏷️ 属性 | 📄 内容 |
| :--- | :--- |
| **模块编号** | 5.0 |
| **状态** | 🟢 详细设计完成 (Ready for Implementation) |
| **核心范式** | Identity-Agnostic Core (身份无关内核) |

## 1. 模块综述 (Overview)

本模块负责在多用户/云端部署场景下，确保身份的安全认证与数据的严格隔离。

## 2. 身份无关内核模式 (The Identity-Agnostic Core Pattern)

```mermaid
graph LR
    subgraph External [外部网络]
        Client(Web / App Client)
    end
    
    subgraph Interfaces [边界层: Auth 拦截]
        Gateway[API Gateway / Auth Middleware]
        JWT[JWT 解析器]
    end
    
    subgraph Core [隔离内核: 身份无关]
        Orchestrator[Orchestrator]
        Engine[Core Engine]
        Persistence[Persistence / Readers]
    end

    Client -->|携带 Token 请求| Gateway
    Gateway <-->|校验/签发| JWT
    Gateway -->|剥离 Token, 注入 UserContext| Orchestrator
    Orchestrator -->|透传 UserContext| Engine
    Engine -->|携带 UserContext 读写| Persistence
```

## 3. 认证与授权 (AuthN & AuthZ)

### 3.1 基于角色的访问控制 (RBAC Transition State)

| 用户角色 (Role) | 发现子域权限 | 决策子域权限 (Debate) | 管理子域权限 | 并发/负载限制 |
| :--- | :--- | :--- | :--- | :--- |
| **BASIC** | 基础行业推演 | 标准双主体博弈 | 基础盈亏追踪 | 单一串行任务 |
| **PRO** | 深度产业链扫描 | 多维度/多空红队博弈 | 全局风险敏感度诊断 | 允许并行调度 |
| **ADMIN** | 全部开放 | 全部开放 | 全部开放 + 系统监控 | 无限制 |

## 4. 数据隔离机制 (Data Isolation Mechanism)

系统核心绝不跨租户读取数据。隔离机制不仅体现在文件系统，还体现在数据库查询层面。

```mermaid
sequenceDiagram
    participant Eng as Core Engine
    participant Persist as Persistence
    participant FS as File System / DB

    Eng->>Persist: 请求保存研报 (携带 UserContext: uid=101)
    Note over Persist: 路径路由拦截
    Persist->>Persist: 拼接路径: /data/101/reports/
    Persist->>FS: 写入 /data/101/reports/AAPL.md
    
    Eng->>Persist: 请求查询持仓 (携带 UserContext: uid=101)
    Note over Persist: SQL 语句拦截
    Persist->>Persist: 强制追加 WHERE user_id = 101
    Persist->>FS: 执行隔离查询
```
