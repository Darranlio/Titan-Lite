# 🔌 Titan-Lite API 接口手册 (V3.0)

## 1. 基础信息
- **Base URL**: `http://localhost:8000` (或服务器内网IP)
- **协议**: HTTP/1.1 (FastAPI)
- **Content-Type**: `application/json`

## 2. 核心接口

### 2.1 触发批量深度研判 (Daily Batch)
自动运行全套流程：初筛 -> 鉴伪 -> AI 研判 -> 生成报告。
- **Endpoint**: `/run`
- **Method**: `POST`
- **Response**:
  ```json
  { "msg": "batch strategy triggered" }
  ```

### 2.2 专项个股研判 (Single Analysis)
针对特定 Ticker 进行深度分析，跳过初筛。
- **Endpoint**: `/analyze/{symbol}`
- **Method**: `POST`
- **Example**: `POST /analyze/NVDA`
- **Response**:
  ```json
  {
    "status": "success",
    "symbol": "NVDA"
  }
  ```

### 2.3 简单价格预测 (Forecast)
基于历史数据的统计学价格趋势预测。
- **Endpoint**: `/forecast/{symbol}`
- **Method**: `GET`
- **Response**:
  ```json
  {
    "symbol": "NVDA",
    "forecast": "...",
    "confidence": 0.85
  }
  ```

## 3. 内部 Agent 接口 (Internal)
系统内部通过 `AgentBridge` 与多智能体图交互。
- **Method**: `agent_bridge.analyze_ticker(symbol, context_extra)`
- **Return**: 返回包含 `reports` 和 `debates` 历史的深度字典。

## 4. 调试与日志
- **Console Log**: 开启 `debug=True` 后，实时输出 Agent 的思考链路。
- **Message Log**: 所有 AI 交互记录存放在 `logs/[SYMBOL]/message_tool.log`。

---
*V3.0 接口已全面适配 DeepSeek OpenAI 兼容模式。*
