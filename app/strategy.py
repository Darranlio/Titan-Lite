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
        print(">>> Titan-Lite v5.0 (Tiered Analysis & Parallel) 启动...")

        # 1. 宏观风控
        is_safe, risk_msg = self.risk.check()
        if not is_safe:
            self.bot.send_markdown(f"# ⛔ 系统熔断\n{risk_msg}", mode="private")
            return

        # 2. 标的发现与估值初筛
        candidates = valuation_screener.run()
        if not candidates: 
            print(">>> 本次扫描未发现符合条件的潜力标的。")
            return
        
        print(f">>> 初筛完成，找到 {len(candidates)} 只潜力股。进入 AI 闪电快筛阶段...")

        # 3. 分级研判：第一步 - AI 闪电快筛 (Fast Filter)
        prioritized_candidates = []
        for item in candidates:
            score, logic = self._fast_ai_filter(item)
            item['priority_score'] = score
            item['fast_logic'] = logic
            prioritized_candidates.append(item)
        
        # 按分数排序
        prioritized_candidates.sort(key=lambda x: x['priority_score'], reverse=True)

        # 4. 深度研判循环 (仅针对 Top 3)
        # 其余标的仅保留快筛结果
        top_n = 3
        deep_pool = prioritized_candidates[:top_n]
        light_pool = prioritized_candidates[top_n:]

        print(f">>> 快筛完成。将对 Top {top_n} 进行多智能体深研，其余 {len(light_pool)} 只保留简报。")

        # 使用并发执行 (针对 2C2G 服务器，开启 2 个 worker)
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as executor:
            # A. 处理深研标的
            for item in deep_pool:
                executor.submit(self._process_deep_analysis, item)
            
            # B. 处理简报标的 (极速完成)
            for item in light_pool:
                self._process_light_analysis(item)

        # 5. 所有研判完成后，进行全站构建
        self._trigger_final_build()

    def _fast_ai_filter(self, item):
        """
        AI 闪电快筛：30秒内决定该股是否值得投入 10分钟深研
        """
        symbol = item['symbol']
        print(f"  [FastFilter] 正在评估 {symbol}...")
        
        prompt = f"""
        你是一位量化快筛专家。基于以下数据，为股票 {symbol} 给出潜力评分 (0-100)。
        价格: {item['current_price']}, 预期涨幅: {item['upside']:.2%}, PE: {item['pe']}, ROE: {item['roe']:.1%}
        
        请简短回复：
        1. 评分：[分数]
        2. 理由：[一句话核心逻辑]
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.LLM_API_KEY, base_path=settings.LLM_BASE_URL)
            resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            content = resp.choices[0].message.content
            # 简单提取分数 (实际建议使用正则)
            score = 50
            if "评分" in content:
                try: score = int(content.split("评分")[1].split("\n")[0].replace("：", "").strip())
                except: pass
            return score, content
        except:
            return 50, "快筛调用失败"

    def _process_deep_analysis(self, item):
        """执行耗时的多智能体深研"""
        symbol = item['symbol']
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
            }, skip_build=True)
            self.push_to_wecom(symbol, item, decision, divergence_msg)

    def _process_light_analysis(self, item):
        """生成极简版报告，不消耗多智能体配额"""
        symbol = item['symbol']
        # 伪造一个极简 decision
        decision = {
            "action": "WATCH" if item['priority_score'] > 60 else "SKIP",
            "rationale": f"快筛结果：{item['fast_logic']}\n注意：该股排在 Top 3 之外，系统自动跳过了深度 Agent 辩论。",
            "reports": {},
            "debates": {}
        }
        self.save_to_web(symbol, item, decision, {
            'fact_check': "未进行深度核查",
            'fact_score': "-",
            'divergence': "未监控",
            'insider': "未监控"
        }, skip_build=True)

    def _trigger_final_build(self):
        """触发统一的网页构建"""
        try:
            print("\n>>> [System] 正在执行全站网页同步构建 (批处理优化模式)...")
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            import subprocess
            # 使用同步等待确保构建完成
            proc = subprocess.Popen(f"cd {base_path}/docs && npm run docs:build", shell=True)
            proc.wait() 
            print(">>> [System] 网页看板刷新成功。")
        except Exception as e:
            print(f"构建触发失败: {e}")

    def save_to_web(self, symbol, item, decision, verify_data, skip_build=False):
        """
        将决策报告保存为 Markdown (V3.0)
        """
        import json
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        symbol_dir = os.path.join(base_path, "docs", "projects", "titan-lite", "reports", symbol)
        os.makedirs(symbol_dir, exist_ok=True)

        date_str = datetime.now().strftime('%Y-%m-%d')
        report_path = os.path.join(symbol_dir, f"{date_str}.md")
        metadata_path = os.path.join(symbol_dir, "metadata.json")

        # 1. 收集本次研报的核心元数据
        current_metadata = {
            "date": date_str,
            "price": item['current_price'],
            "rating": decision.get('action', 'HOLD'),
            "pe": item.get('pe', 0),
            "roe": item.get('roe', 0),
            "fact_score": verify_data.get('fact_score', 0),
            "upside": item.get('upside', 0)
        }

        # 2. 更新历史元数据
        history = []
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        
        # 避免同日期重复记录
        history = [h for h in history if h['date'] != date_str]
        history.append(current_metadata)
        history = sorted(history, key=lambda x: x['date'], reverse=True)[:10]
        
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)

        # 3. AI 翻译与教育润色
        print(f">>> [AI] 正在处理 {symbol} 报告润色...")
        refined_content = self._refine_report_with_ai(decision, symbol)

        # 4. 写入日度深度报告
        full_report = f"""---
title: {symbol} 研报 ({date_str})
---
# 📜 {symbol} 研报档案 - {date_str}
[返回总览页](./index.md)

{refined_content}
"""
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(full_report)

        # 5. 更新个股总览页 (Dashboard)
        self._update_symbol_dashboard(symbol, symbol_dir, history, item, decision)
        
        # 6. 更新全局索引
        self.update_report_index(symbol, skip_build=skip_build)

    def _refine_report_with_ai(self, decision, symbol):
        """调用 AI 进行研报美化"""
        raw_reports = ""
        reports = decision.get('reports', {})
        if reports:
            for name, content in reports.items():
                if content: raw_reports += f"[{name}]\n{content}\n"
        
        raw_debates = ""
        debates = decision.get('debates', {})
        if debates:
            for d_name, d_state in debates.items():
                if d_state and d_state.get('history'):
                    raw_debates += f"[{d_name} Debate]\n{d_state['history']}\n"

        refine_prompt = f"""
        你是一位顶级的华尔街投研总监。请将以下素材整理成一份精美的中文研报。
        
        [素材]
        {raw_reports}
        {raw_debates}
        最终决策：{decision.get('action')}
        理由：{decision.get('rationale')}

        要求：
        - 专业排版、使用 Emoji。
        - 重要术语增加【💡 投资课堂】。
        - 如果素材中没有详细报告(reports为空)，请基于核心理由生成一份简明概要。
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
            resp = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": refine_prompt}])
            return resp.choices[0].message.content
        except:
            return f"AI 润色失败。原始理由：{decision.get('rationale')}"

    def _update_symbol_dashboard(self, symbol, symbol_dir, history, item, decision):
        """生成个股动态总览页 (index.md)"""
        latest = history[0]
        first = history[-1]
        price_change = (latest['price'] - first['price']) / first['price']
        change_color = "green" if price_change >= 0 else "red"

        # 生成指标演变表 (最近 5 次)
        table_rows = "| 日期 | 价格 | 评级 | PE | 事实分 | 预期涨幅 |\n| :--- | :--- | :--- | :--- | :--- | :--- |\n"
        for h in history[:5]:
            table_rows += f"| {h['date']} | ${h['price']} | {h['rating']} | {h['pe']:.1f} | {h['fact_score']} | {h['upside']:.2%} |\n"

        # 调用 AI 生成三段论总结 (历史、现状、未来)
        summary_prompt = f"""
        基于 {symbol} 的最新研判和历史数据，请提供简短的：
        1. 历史回顾 (过去跟踪的表现)
        2. 当前状态 (核心矛盾)
        3. 未来预期 (关键触发点)
        各 100 字以内，使用专业投资术语。
        最新决策：{decision.get('action')}
        理由：{decision.get('rationale')}
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
            resp = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": summary_prompt}])
            analysis_text = resp.choices[0].message.content
        except:
            analysis_text = "分析生成中..."

        dashboard_content = f"""---
title: {symbol} 动态总览
---

# 🚀 {symbol} 投资价值动态总览

## 1. 📌 实时状态卡片 (Status Card)
::: tip 核心指标
- **最新评级**: `{latest['rating']}`
- **当前价格**: `${latest['price']}`
- **首探至今涨跌**: <span style="color:{change_color}">{price_change:.2%}</span> (自 {first['date']} 始)
- **分析师预期**: `${item['target_price']}` (预期空间: {item['upside']:.2%})
:::

## 2. 📊 指标演变追踪 (Evolution Trace)
{table_rows}

## 3. 🧠 深度研判三段论 (Three-Act Analysis)
{analysis_text}

## 4. 📂 历史深度研报档案
"""
        # 添加历史研报链接
        for h in history:
            dashboard_content += f"- [{h['date']} 深度研判报告](./{h['date']}.md)\n"

        dashboard_content += f"\n--- \n*本 Dashboard 随研报自动更新 | Titan-Lite V3.0*"
        
        with open(os.path.join(symbol_dir, "index.md"), "w", encoding="utf-8") as f:
            f.write(dashboard_content)

    def update_report_index(self, symbol, skip_build=False):
        """
        动态重建全局个股索引 index.md，确保移除占位符并指向最新的 Dashboard
        """
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        reports_root = os.path.join(base_path, "docs", "projects", "titan-lite", "reports")
        index_path = os.path.join(reports_root, "index.md")
        
        # 获取所有个股子目录
        symbols = [d for d in os.listdir(reports_root) if os.path.isdir(os.path.join(reports_root, d))]
        symbols.sort() # 按字母排序

        new_content = "# 📑 历史投研报告库\n\n"
        new_content += "这里存放由 Titan-Lite V3.0 系统自动生成的深度研报与个股档案馆。\n\n---\n\n"
        new_content += "## 📈 覆盖个股列表 (Symbol Coverage)\n\n"

        if not symbols:
            new_content += "> 🔄 **目前列表为空**。请在主页运行深度研判生成报告。\n"
        else:
            for s in symbols:
                # 尝试从该目录的 metadata.json 中获取最后更新时间
                last_update = datetime.now().strftime('%Y-%m-%d')
                meta_path = os.path.join(reports_root, s, "metadata.json")
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r") as f:
                            import json
                            history = json.load(f)
                            if history: last_update = history[0]['date']
                    except: pass
                
                new_content += f"- [📊 **{s}** 个股总览看板](./{s}/index.md) — *更新于 {last_update}*\n"

        with open(index_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        # 触发构建
        if not skip_build:
            self._trigger_final_build()


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
