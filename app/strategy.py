import pandas as pd
from datetime import datetime, timedelta
import os
import json

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
from backtester import backtester
from portfolio_manager import portfolio_manager

class TitanStrategyV2:
    def __init__(self):
        self.bot = WeComBot()
        self.risk = MacroRisk()

    def execute(self):
        print(">>> Titan-Lite v5.7 (Navigation Engine) 启动...")
        is_safe, risk_msg = self.risk.check()
        if not is_safe:
            self.bot.send_markdown(f"# ⛔ 系统熔断\n{risk_msg}", mode="private")
            return

        candidates = valuation_screener.run()
        if not candidates: 
            print(">>> 本次扫描未发现符合条件的潜力标的。")
            return
        
        prioritized_candidates = []
        for item in candidates:
            score, logic = self._fast_ai_filter(item)
            item['priority_score'] = score
            item['fast_logic'] = logic
            prioritized_candidates.append(item)
        
        prioritized_candidates.sort(key=lambda x: x['priority_score'], reverse=True)

        top_n = 3
        deep_pool = prioritized_candidates[:top_n]
        light_pool = prioritized_candidates[top_n:]
        scan_results = {"deep": [], "light": []}

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(self._process_deep_analysis, item) for item in deep_pool]
            for f in futures:
                res = f.result()
                if res: scan_results['deep'].append(res)
            for item in light_pool:
                res = self._process_light_analysis(item)
                if res: scan_results['light'].append(res)

        macro_report_md = self._generate_market_panorama(candidates, scan_results)
        self._save_macro_report(macro_report_md)
        self._trigger_final_build()

    def _fast_ai_filter(self, item):
        symbol = item['symbol']
        print(f"  [FastFilter] 正在评估 {symbol}...")
        prompt = f"你是一位量化快筛专家。基于以下数据，为股票 {symbol} 给出潜力评分 (0-100)。\n价格: {item['current_price']}, 预期涨幅: {item['upside']:.2%}, PE: {item['pe']}, ROE: {item['roe']:.1%}\n请简短回复：\n1. 评分：[分数]\n2. 理由：[一句话核心逻辑]"
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
            resp = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}], temperature=0.1)
            content = resp.choices[0].message.content
            score = 50
            if "评分" in content:
                try: score = int(content.split("评分")[1].split("\n")[0].replace("：", "").strip())
                except: pass
            return score, content
        except: return 50, "快筛调用失败"

    def _process_deep_analysis(self, item):
        symbol = item['symbol']
        news = finnhub_provider.get_company_news(symbol)
        fact_check, fact_score = verification_engine.verify_news(symbol, news)
        div = verification_engine.check_divergence(symbol)
        ins = verification_engine.get_insider_signal(symbol)
        v_context = f"\n[事实核查报告]\n- 真实度: {fact_score}\n- AI结论: {fact_check}\n- 量价表现: {div}\n- 高管行为: {ins}\n"
        decision = agent_bridge.analyze_ticker(symbol, context_extra=v_context)
        if decision:
            self.save_to_web(symbol, item, decision, {'fact_check': fact_check, 'fact_score': fact_score, 'divergence': div, 'insider': ins}, skip_build=True)
            self.push_to_wecom(symbol, item, decision, div)
            return {"symbol": symbol, "action": decision.get('action'), "logic": decision.get('rationale')[:100], "sector": item.get('sector')}
        return None

    def _process_light_analysis(self, item):
        symbol = item['symbol']
        financial_context = f"PE: {item.get('pe', 'N/A')}, ROE: {item.get('roe', 'N/A')}, 预期空间: {item.get('upside', 0):.2%}"
        decision = {
            "action": "观察 (WATCH)" if item['priority_score'] > 60 else "跳过 (SKIP)",
            "rationale": f"【快筛逻辑】：{item['fast_logic']}\n评分未进入前三，执行快筛分析。",
            "reports": {}, "debates": {}
        }
        self.save_to_web(symbol, item, decision, {'fact_check': "快筛", 'fact_score': "-", 'divergence': "未监控", 'insider': "未监控"}, skip_build=True)
        return {"symbol": symbol, "action": decision["action"], "score": item['priority_score'], "sector": item.get('sector')}

    def _generate_market_panorama(self, candidates, scan_results):
        sectors_count = {}
        for c in candidates:
            s = c['sector']
            sectors_count[s] = sectors_count.get(s, 0) + 1
        winners = [f"{r['symbol']}({r['action']})" for r in scan_results['deep']]
        benchmarks = data_provider.get_market_benchmarks()
        sector_perf = data_provider.get_sector_status()
        sorted_perf = sorted(sector_perf.items(), key=lambda x: x[1], reverse=True)
        top_s = ", ".join([f"{k}({v:.2%})" for k, v in sorted_perf[:3]])
        bot_s = ", ".join([f"{k}({v:.2%})" for k, v in sorted_perf[-3:]])
        hot = news_spider.get_market_sentiment_keywords()
        prompt = f"你是一位投资总监(CIO)。请基于以下结果产出执行总览。\n[实战] 样本：{len(candidates)}只。潜力行业：{sectors_count}。结论：{winners}\n[大盘] 指数：{benchmarks}。强弱板块：{top_s} / {bot_s}\n[舆情] {hot}"
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
            resp = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}])
            return resp.choices[0].message.content
        except: return "宏观分析生成失败。"

    def _save_macro_report(self, content):
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        macro_dir = os.path.join(base_path, "docs", "projects", "titan-lite", "reports", "macro")
        os.makedirs(macro_dir, exist_ok=True)
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 1. 保存原子档案 (使用原生 Pager 逻辑)
        full_md = f"---\ntitle: 宏观全景 ({date_str})\nprev: {{ text: '历史档案馆', link: './index' }}\nnext: false\n---\n\n# 🌏 宏观全景研判 ({date_str})\n\n{content}"
        with open(os.path.join(macro_dir, f"{date_str}.md"), "w") as f: f.write(full_md)
        
        # 2. 最新快照 (原生 Pager 指向列表)
        ov_path = os.path.join(base_path, "docs", "projects", "titan-lite", "reports", "market_overview.md")
        with open(ov_path, "w") as f:
            f.write(f"---\ntitle: 全球宏观视角\nprev: {{ text: '我的基金中心', link: '/projects/titan-lite/portfolio' }}\nnext: {{ text: '研报历史库', link: './index' }}\n---\n\n# 🌏 最新宏观全景 ({date_str})\n\n{content}\n\n---\n[📜 查看所有历史宏观报告](./macro/index.md)")
        
        # 3. 重建索引
        self._update_macro_index(macro_dir)

    def _update_macro_index(self, macro_dir):
        files = sorted([f for f in os.listdir(macro_dir) if f.endswith(".md") and f != "index.md"], reverse=True)
        index_path = os.path.join(macro_dir, "index.md")
        content = f"---\ntitle: 宏观档案馆\nprev: {{ text: '研报历史库', link: '../index' }}\nnext: false\n---\n\n# 📜 历史宏观档案\n\n" + "\n".join([f"- [{f.replace('.md', '')} 研判](./{f})" for f in files])
        with open(index_path, "w") as f: f.write(content)

    def _trigger_final_build(self):
        try:
            print("\n>>> [System] 正在同步网页看板...")
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            import subprocess
            proc = subprocess.Popen(f"cd {base_path}/docs && npm run docs:build", shell=True)
            proc.wait()
        except: pass

    def save_to_web(self, symbol, item, decision, verify_data, skip_build=False):
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        symbol_dir = os.path.join(base_path, "docs", "projects", "titan-lite", "reports", symbol)
        os.makedirs(symbol_dir, exist_ok=True)
        date_str = datetime.now().strftime('%Y-%m-%d')
        profile = data_provider.get_company_details(symbol)
        
        meta_path = os.path.join(symbol_dir, "metadata.json")
        current_meta = {"date": date_str, "price": item['current_price'], "rating": decision.get('action', 'HOLD'), "pe": item.get('pe', 0), "roe": item.get('roe', 0), "fact_score": verify_data.get('fact_score', 0), "upside": item.get('upside', 0), "summary_snippet": profile.get('summary', '')[:50] + "..."}
        history = []
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f: history = json.load(f)
            except: pass
        history = [h for h in history if h['date'] != date_str]
        history.insert(0, current_meta)
        history = history[:10]
        with open(meta_path, "w") as f: json.dump(history, f, indent=4)
        
        # 写入具体日度研报 (使用原生 Pager)
        refined = self._refine_report_with_ai(decision, symbol)
        full_md = f"---\ntitle: {symbol} 深度研报 ({date_str})\nprev: {{ text: '{symbol} 看板', link: './index' }}\nnext: false\n---\n\n# 📜 {symbol} 研报档案 - {date_str}\n\n{refined}"
        with open(os.path.join(symbol_dir, f"{date_str}.md"), "w") as f: f.write(full_md)
        
        self._update_symbol_dashboard(symbol, symbol_dir, history, item, decision, profile)
        self.update_report_index(symbol, skip_build=skip_build)

    def _refine_report_with_ai(self, decision, symbol):
        raw_reports = ""
        for name, content in decision.get('reports', {}).items():
            if content: raw_reports += f"### {name}\n{content}\n"
        curr_date = datetime.now().strftime('%Y-%m-%d')
        refine_prompt = f"你是一位顶级分析师。请为 {symbol} 整理研报正文。日期锁定 {curr_date}。严禁废话。第一行必须是Markdown标题。深度标的格式 # 📊 {symbol} 深度研究。快筛标的格式 ## ⚡ 闪电决策简报。"
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
            resp = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "system", "content": "你是一个专业的投研机器人。"},{"role": "user", "content": f"{refine_prompt}\n素材：{decision.get('action')}, {decision.get('rationale')}\n{raw_reports}"}], temperature=0.1)
            return resp.choices[0].message.content.strip()
        except: return f"AI 润色失败。{decision.get('rationale')}"

    def _update_symbol_dashboard(self, symbol, symbol_dir, history, item, decision, profile=None):
        latest = history[0]; first = history[-1]
        change = (latest['price'] - first['price']) / first['price']
        if not profile: profile = data_provider.get_company_details(symbol)
        financials = data_provider.get_financial_highlights(symbol)
        bt = backtester.run_simple_backtest(symbol)
        table = "| 日期 | 价格 | 评级 | PE | 预期涨幅 |\n| :--- | :--- | :--- | :--- | :--- |\n"
        for h in history[:5]: table += f"| {h['date']} | ${h['price']} | {h['rating']} | {h['pe']:.1f} | {h['upside']:.2%} |\n"
        summary = self._get_ai_summary(symbol, decision)
        
        # 个股看板使用原生 Pager 指向档案馆
        md = f"""---
title: {symbol} 总览
prev: {{ text: '研报历史库', link: '../index' }}
next: false
---

# 🚀 {symbol} 投研价值看板

## 1. 🔍 公司业务 DNA
::: info {profile.get('full_name')}
{profile.get('summary')}
:::
## 2. 📌 实时状态
- 当前建议: `{latest['rating']}`
- 现价: `${latest['price']}`
- 涨跌: {change:.2%}
## 3. 📊 财务核心
- 营收增长: {self._fmt_pct(financials.get('rev_growth'))}\n- 净利润率: {self._fmt_pct(financials.get('net_margin'))}\n- FCF: ${self._fmt_large(financials.get('fcf'))}
## 4. 📈 历史回测
{bt.get('summary', '生成中')}
## 5. 📑 指标演变
{table}
## 6. 🧠 研判三段论
{summary}
## 7. 📂 历史深度研报
"""
        for h in history: md += f"- [{h['date']} 深度研判报告](./{h['date']}.md)\n"
        with open(os.path.join(symbol_dir, "index.md"), "w") as f: f.write(md)

    def _get_ai_summary(self, symbol, decision):
        prompt = f"简述 {symbol} 的 1.历史回顾 2.当前状态 3.未来预期。决策：{decision.get('action')}"
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
            resp = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}])
            return resp.choices[0].message.content
        except: return "生成中..."

    def _fmt_pct(self, v): return f"{v*100:.2%}" if v is not None else "N/A"
    def _fmt_large(self, v):
        if v is None: return "N/A"
        if abs(v) > 1e12: return f"{v/1e12:.2f}T"
        if abs(v) > 1e9: return f"{v/1e9:.2f}B"
        return str(v)

    def update_report_index(self, symbol, skip_build=False):
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        reports_root = os.path.join(base_path, "docs", "projects", "titan-lite", "reports")
        index_path = os.path.join(reports_root, "index.md")
        symbols = sorted([d for d in os.listdir(reports_root) if os.path.isdir(os.path.join(reports_root, d)) and d != "macro"])
        
        # 全局索引使用原生 Pager 指向基金和宏观
        md = f"""---
title: 研报档案馆
prev: {{ text: '我的基金中心', link: '/projects/titan-lite/portfolio' }}
next: {{ text: '宏观全景展望', link: './market_overview' }}
---
# 📑 研报历史库

::: info 🌍 宏观视角
- [**全市场宏观全景展望**](./market_overview.md)
:::

---\n## 📈 覆盖个股列表\n"""
        for s in symbols:
            blurb = "暂无简介"; l_date = ""
            meta_path = os.path.join(reports_root, s, "metadata.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r") as f:
                        meta = json.load(f)
                        if meta: blurb = meta[0].get('summary_snippet', '暂无简介'); l_date = meta[0].get('date', '')
                except: pass
            md += f"- [📊 **{s}** 总览看板](./{s}/index.md) — *{blurb}* ({l_date})\n"
        with open(index_path, "w") as f: f.write(md)
        if not skip_build: self._trigger_final_build()

    def push_to_wecom(self, symbol, item, decision, divergence):
        msg = f"# 🚀 深度研判: {symbol}\n**决策**: {decision.get('action')}\n**逻辑**: {decision.get('rationale')[:150]}..."
        self.bot.send_markdown(msg, mode="private")

    def analyze_single_ticker(self, symbol):
        print(f">>> [Single] 专项研判 {symbol}...")
        try:
            curr = data_provider.get_history_price(symbol).iloc[-1]
            y_info = data_provider.get_analyst_info(symbol)
            item = {'symbol': symbol, 'current_price': curr, 'target_price': y_info.get('targetMeanPrice', curr*1.1), 'upside': y_info.get('upside', 0.1), 'pe': y_info.get('peRatioTTM', 0), 'roe': y_info.get('roeTTM', 0), 'sector': y_info.get('sector', 'Unknown')}
            news = finnhub_provider.get_company_news(symbol)
            fact_check, fact_score = verification_engine.verify_news(symbol, news)
            div = verification_engine.check_divergence(symbol)
            ins = verification_engine.get_insider_signal(symbol)
            v_ctx = f"\n[事实核查]\n- 真实度: {fact_score}\n- AI结论: {fact_check}\n- 量价: {div}\n- 高管: {ins}\n"
            dec = agent_bridge.analyze_ticker(symbol, context_extra=v_ctx)
            if dec: self.save_to_web(symbol, item, dec, {'fact_check': fact_check, 'fact_score': fact_score, 'divergence': div, 'insider': ins})
            return True
        except: return False

def run_job(): TitanStrategyV2().execute()
def run_single(symbol): TitanStrategyV2().analyze_single_ticker(symbol)
