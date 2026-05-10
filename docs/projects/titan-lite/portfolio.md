---
title: 我的基金管理中心
---

<script setup>
import FundManager from './FundManager.vue'
</script>

# 🏦 个人基金管理中心 (Titan-PM)

> 这里是您的私人数字资产库。基于 SQLite 工业级存储，支持单位净值化核算与 DeepSeek AI 组合诊断。

<FundManager />

---

## 💡 投资小贴士
- **单位净值 (NAV)**：反映的是您的投资能力，不受追加或提取本金的影响。初始净值为 `1.0000`。
- **加权成本**：当您分批买入同一股票时，系统会自动计算平均持仓成本。
- **AI 诊断**：建议在运行完“全市场扫描”后进行诊断，AI 会结合最新的宏观全景展望给出调仓建议。
