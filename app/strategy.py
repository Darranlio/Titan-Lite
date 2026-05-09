import pandas as pd
from datetime import datetime, timedelta
import os

from config import settings
from data_provider import data_provider
from wecom import WeComBot
from macro_risk import MacroRisk
from news_spider import news_spider
from valuation_screener import valuation_screener
from agent_bridge import agent_bridge
from verification_engine import verification_engine
from finnhub_provider import finnhub_provider
from fmp_provider import fmp_provider

class TitanStrategyV2:
    def __init__(self):
        self.bot = WeComBot()
        self.risk = MacroRisk()

    def execute(self):
        print(">>> Titan-Lite v4.1 (Verification Layer) 启动...")

        # 1. 宏观风控
        is_safe, risk_msg = self.risk.check()
        if not is_safe:
            self.bot.send_markdown(f"# ⛔ 系统熔断\n{risk_msg}", mode="private")
            return

        # 2. 标的发现与估值筛选 (FMP 数据)
        candidates = valuation_screener.run()
        if not candidates: return

        # 3. 深度研判循环
        for item in candidates:
            symbol = item['symbol']
            
            # --- V2.1 真伪鉴别层 ---
            news = finnhub_provider.get_company_news(symbol)
            fact_check, fact_score = verification_engine.verify_news(symbol, news)
            divergence_msg = verification_engine.check_divergence(symbol)
            insider_msg = verification_engine.get_insider_signal(symbol)
            
            # 将鉴伪结果注入 Agent 上下文
            v_context = f"\n[事实核查报告]\n- 真实度: {fact_score}\n- AI结论: {fact_check}\n- 量价表现: {divergence_msg}\n- 高管行为: {insider_msg}\n"
            
            # 调用 TradingAgents
            decision = agent_bridge.analyze_ticker(symbol, context_extra=v_context)
            
            if decision:
                # 4. 结果整理与可视化
                self.save_to_web(symbol, item, decision, {
                    'fact_check': fact_check,
                    'fact_score': fact_score,
                    'divergence': divergence_msg,
                    'insider': insider_msg
                })
                
                # 5. 推送核心决策
                self.push_to_wecom(symbol, item, decision, divergence_msg)

    def save_to_web(self, symbol, item, decision, verify_data):
        """
        将决策报告保存为 Markdown，由 VitePress 渲染 (V2.1 增强版)
        """
        report_path = f"docs/projects/titan-lite/reports/{symbol}.md"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        content = f"""---
title: {symbol} 深度研判报告
date: {datetime.now().strftime('%Y-%m-%d')}
---

# 📊 {symbol} 深度研判报告 ({datetime.now().strftime('%Y-%m-%d')})

## 1. 估值概览 (Valuation)
- **当前价格**: ${item['current_price']}
- **FMP 目标均价**: ${item['target_price']}
- **预期涨幅**: {item['upside']:.2%}
- **PE/ROE**: {item['pe']:.1f} / {item['roe']:.1%}

## 2. 🛡️ 真伪鉴别 (Verification Layer)
- **事实核查评分**: `{verify_data['fact_score']}`
- **事实核查结论**: {verify_data['fact_check']}
- **量价背离监控**: **{verify_data['divergence']}**
- **高管行为监控**: {verify_data['insider']}

## 3. 🧠 智能体研判 (Agent Decision)
- **最终决策**: **{decision.get('action', 'HOLD')}**
- **建议理由**: 
> {decision.get('rationale', '无理由')}

## 4. ⚖️ 辩论摘要
{decision.get('debate_summary', '详情见日志')}

---
*本报告由 Titan-Lite V2.1 机构级系统自动生成。*
"""
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)
        self.update_report_index(symbol)

    def update_report_index(self, symbol):
        index_path = "docs/projects/titan-lite/reports/index.md"
        line = f"- [{symbol} 研判报告](./{symbol}.md) - {datetime.now().strftime('%Y-%m-%d')}\n"
        
        if not os.path.exists(index_path):
            with open(index_path, "w") as f:
                f.write("# 📑 历史研研报列表\n\n")
        
        with open(index_path, "a") as f:
            f.write(line)

    def push_to_wecom(self, symbol, item, decision, divergence):
        msg = f"""# 🚀 深度研判: {symbol}
**最终决策**: {decision.get('action')}
**量价验证**: {divergence[:50]}...
---
**核心逻辑**: {decision.get('rationale')[:150]}...
"""
        self.bot.send_markdown(msg, mode="private")

    def analyze_single_ticker(self, symbol):
        """
        针对指定个股运行深度研判 (跳过初筛)
        """
        print(f">>> [V2.1 Single] 针对 {symbol} 启动专项研判...")
        
        # 1. 获取基础数据
        try:
            current_price = data_provider.get_history_price(symbol).iloc[-1]
            estimates = fmp_provider.get_analyst_estimates(symbol)
            metrics = fmp_provider.get_key_metrics(symbol)
            
            item = {
                'symbol': symbol,
                'current_price': round(current_price, 2),
                'target_price': round(estimates.get('estimatedPriceAvg', current_price * 1.1), 2),
                'upside': (estimates.get('estimatedPriceAvg', current_price * 1.1) - current_price) / current_price,
                'pe': metrics.get('peRatioTTM', 0),
                'roe': metrics.get('roeTTM', 0)
            }
        except Exception as e:
            print(f"获取 {symbol} 基础数据失败: {e}")
            return False

        # 2. 鉴伪与研判 (复用流程)
        news = finnhub_provider.get_company_news(symbol)
        fact_check, fact_score = verification_engine.verify_news(symbol, news)
        divergence_msg = verification_engine.check_divergence(symbol)
        insider_msg = verification_engine.get_insider_signal(symbol)
        
        v_context = f"\n[事实核查报告]\n- 真实度: {fact_score}\n- AI结论: {fact_check}\n- 量价表现: {divergence_msg}\n- 高管行为: {insider_msg}\n"
        
        decision = agent_bridge.analyze_ticker(symbol, context_extra=v_context)
        
        if decision:
            self.save_to_web(symbol, item, decision, {
                'fact_check': fact_check,
                'fact_score': fact_score,
                'divergence': divergence_msg,
                'insider': insider_msg
            })
            return True
        return False

def run_job():
    TitanStrategyV2().execute()

def run_single(symbol):
    return TitanStrategyV2().analyze_single_ticker(symbol)
