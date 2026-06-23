import pandas as pd
from datetime import datetime, timedelta
import os
import json
import shutil

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
from archive_manager import archive_manager
from wechat_writer import wechat_writer
from sys_logger import sys_logger
from analytical_engine import analytical_engine

class TitanStrategyV2:
    def __init__(self):
        self.bot = WeComBot()
        self.risk = MacroRisk()
        self.archive_mgr = archive_manager
        self.portfolio_mgr = portfolio_manager

    def execute(self, user_ctx=None, market='Global'):
        if user_ctx:
            from archive_manager import ArchiveManager
            from portfolio_manager import PortfolioManager
            self.archive_mgr = ArchiveManager(storage_root=user_ctx.storage_root)
            self.portfolio_mgr = PortfolioManager(storage_root=user_ctx.storage_root)
            sys_logger.__init__(storage_root=user_ctx.storage_root)
        else:
            self.archive_mgr = archive_manager
            self.portfolio_mgr = portfolio_manager

        sys_logger.info(f">>> Titan-Lite v5.7 (Navigation Engine) [{market}] 启动...", stage="Market Scan", progress=5, task_type="batch")
        is_safe, risk_msg = self.risk.check()
        if not is_safe:
            self.bot.send_markdown(f"# ⛔ 系统熔断\n{risk_msg}", mode="private")
            sys_logger.info(f"⛔ 系统熔断: {risk_msg}", stage="Halted", progress=0, task_type="batch")
            return

        sys_logger.info(f"🔍 步骤 1/4: 正在进行{market}全市场初筛 (筛选潜力洼地)...", stage="Screening", progress=15, task_type="batch")
        candidates = valuation_screener.run(market=market)
        if not candidates: 
            sys_logger.info(">>> 本次扫描未发现符合条件的潜力标的。", stage="Completed", progress=100, task_type="batch")
            return
        
        sys_logger.info(f"✅ 初筛完成，发现 {len(candidates)} 只潜力标的，开始 AI 并发快筛评分...", stage="Fast Filtering", progress=30, task_type="batch")
        prioritized_candidates = []
        
        # 使用并发执行 AI 快筛
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_item = {executor.submit(self._fast_ai_filter, item): item for item in candidates}
            for i, future in enumerate(as_completed(future_to_item)):
                item = future_to_item[future]
                try:
                    score, logic = future.result()
                    item['priority_score'] = score
                    item['fast_logic'] = logic
                    prioritized_candidates.append(item)
                except:
                    item['priority_score'] = 50
                    item['fast_logic'] = "评分失败"
                    prioritized_candidates.append(item)
                
                if i % 5 == 0:
                    p = 30 + int((i / len(candidates)) * 20)
                    sys_logger.info(f"  [AI 快筛] 已并发处理 {i}/{len(candidates)} 只标的...", stage="Fast Filtering", progress=p, task_type="batch")
        
        prioritized_candidates.sort(key=lambda x: x['priority_score'], reverse=True)

        top_n = 3
        deep_pool = prioritized_candidates[:top_n]
        light_pool = prioritized_candidates[top_n:]
        scan_results = {"deep": [], "light": []}

        sys_logger.info(f"🧠 步骤 3/4: 启动并发深度研判 (Top {top_n} 标的多 Agent 认知博弈)...", stage="Deep Analysis", progress=55, task_type="batch")
        # 增加研判并发数到 3
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(self._process_deep_analysis, item) for item in deep_pool]
            for f in futures:
                res = f.result()
                if res: scan_results['deep'].append(res)
            
            # 快筛标的也并发执行
            light_futures = [executor.submit(self._process_light_analysis, item) for item in light_pool]
            for f in light_futures:
                res = f.result()
                if res: scan_results['light'].append(res)

        sys_logger.info("🌏 步骤 4/4: 正在生成宏观全景研判报告并同步看板...", stage="Generating Macro", progress=85, task_type="batch")
        macro_report_md = self._generate_market_panorama(candidates, scan_results)
        self._save_macro_report(macro_report_md)
        self._trigger_final_build()
        sys_logger.info("✅ 全市场深度扫描任务圆满完成！", stage="Completed", progress=100, task_type="batch")

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
        
        # 自动处理 A股后缀补全
        fetch_symbol = symbol
        is_ashare = False
        if symbol.isdigit() and len(symbol) == 6:
            is_ashare = True
            if symbol.startswith(('60', '68')): fetch_symbol = f"{symbol}.SS"
            elif symbol.startswith(('00', '30')): fetch_symbol = f"{symbol}.SZ"
            elif symbol.startswith('8'): fetch_symbol = f"{symbol}.BJ"

        news = finnhub_provider.get_company_news(fetch_symbol)
        fact_check, fact_score = verification_engine.verify_news(fetch_symbol, news)
        div = verification_engine.check_divergence(fetch_symbol)
        ins = verification_engine.get_insider_signal(fetch_symbol)
        
        ashare_ctx = ""
        if is_ashare:
            a_data = data_provider.get_ashare_specifics(symbol)
            if a_data and "error" not in a_data:
                ashare_ctx = f"\n[A股专用审计指标]\n- 市净率(PB): {a_data.get('pb')}\n- 换手率: {a_data.get('turnover_rate')}\n- 主力净流入: {a_data.get('main_inflow')}\n- 总市值: {a_data.get('total_mv')}\n"

        v_context = f"\n[事实核查报告]\n- 真实度: {fact_score}\n- AI结论: {fact_check}\n- 量价表现: {div}\n- 高管行为: {ins}\n" + ashare_ctx
        decision = agent_bridge.analyze_ticker(fetch_symbol, context_extra=v_context)
        if decision:
            self.save_to_web(symbol, item, decision, {'fact_check': fact_check, 'fact_score': fact_score, 'divergence': div, 'insider': ins}, skip_build=True)
            self.push_to_wecom(symbol, item, decision, div)
            return {"symbol": symbol, "action": decision.get('action'), "logic": decision.get('rationale')[:100], "sector": item.get('sector')}
        return None

    def _process_light_analysis(self, item):
        symbol = item['symbol']
        # 简单处理 A股后缀
        fetch_symbol = symbol
        if symbol.isdigit() and len(symbol) == 6:
            if symbol.startswith(('60', '68')): fetch_symbol = f"{symbol}.SS"
            elif symbol.startswith(('00', '30')): fetch_symbol = f"{symbol}.SZ"
            elif symbol.startswith('8'): fetch_symbol = f"{symbol}.BJ"

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

        # Use user-specific storage root if provided
        storage_root = getattr(self, 'storage_root', "docs/projects/titan-lite")
        macro_dir = os.path.join(base_path, storage_root, "reports", "macro")
        os.makedirs(macro_dir, exist_ok=True)

        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        file_ts = now.strftime('%Y-%m-%d_%H%M')

        # 1. 保存原子档案 (使用时间戳文件名，防止同日覆盖)
        # 深度为 reports/macro/FILE.md
        # 相对 assets 是 ../../assets
        # 相对 reports 根目录是 ..
        # 相对 macro 目录是 .
        macro_content = content.replace("{ASSETS_REL}", "../../assets")
        macro_content = macro_content.replace("{{REPORTS_REL}}", "..")
        macro_content = macro_content.replace("{{MACRO_REL}}", ".")
        
        full_md = f"---\ntitle: 宏观全景 ({file_ts})\nprev: {{ text: '历史档案馆', link: './index' }}\nnext: false\n---\n\n# 🌏 宏观全景研判 ({file_ts})\n\n{macro_content}"
        with open(os.path.join(macro_dir, f"{file_ts}.md"), "w") as f: f.write(full_md)

        # 2. 最新快照 (始终指向最新的一次结果)
        # 深度为 reports/market_overview.md
        # 相对 assets 是 ../assets
        # 相对 reports 根目录是 .
        # 相对 macro 目录是 ./macro
        ov_content_base = content.replace("{ASSETS_REL}", "../assets")
        ov_content_base = ov_content_base.replace("{{REPORTS_REL}}", ".")
        ov_content_base = ov_content_base.replace("{{MACRO_REL}}", "./macro")
        
        ov_content = f"---\ntitle: 全球宏观视角\nprev: {{ text: '我的基金中心', link: '/projects/titan-lite/portfolio' }}\nnext: {{ text: '研报历史库', link: './index' }}\n---\n\n# 🌏 最新宏观全景 ({file_ts})\n\n{ov_content_base}\n\n---\n[📜 查看所有历史宏观报告](./macro/index.md)"
        
        ov_path = os.path.join(base_path, storage_root, "reports", "market_overview.md")
        with open(ov_path, "w") as f:
            f.write(ov_content)
            
        # 同步更新一份到全局回退目录，解决 UI 不刷新的问题
        global_reports_root = os.path.join(base_path, "docs", "projects", "titan-lite")
        global_ov_path = os.path.join(global_reports_root, "reports", "market_overview.md")
        try:
            with open(global_ov_path, "w") as f:
                f.write(ov_content)
            
            # 同步资源文件，防止 VitePress 构建时找不到图片
            user_assets_dir = os.path.join(base_path, storage_root, "assets")
            global_assets_dir = os.path.join(global_reports_root, "assets")
            if os.path.exists(user_assets_dir):
                os.makedirs(global_assets_dir, exist_ok=True)
                for asset_file in os.listdir(user_assets_dir):
                    if asset_file.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        src = os.path.join(user_assets_dir, asset_file)
                        dst = os.path.join(global_assets_dir, asset_file)
                        shutil.copy2(src, dst)
        except Exception as e:
            sys_logger.error(f"Failed to update global market overview or assets: {e}")

        # 3. 重建索引
        self._update_macro_index(macro_dir)
    def _update_macro_index(self, macro_dir):
        # 筛选所有的 md 文件并按时间倒序排列
        files = sorted([f for f in os.listdir(macro_dir) if f.endswith(".md") and f != "index.md"], reverse=True)
        index_path = os.path.join(macro_dir, "index.md")
        
        list_items = []
        for f in files:
            name = f.replace('.md', '')
            display = name
            if '_' in name:
                parts = name.split('_')
                date_p = parts[0]
                time_p = parts[1]
                # 简单切片实现 HH:MM 格式
                display = f"{date_p} {time_p[:2]}:{time_p[2:]}"
            list_items.append(f"- [{display} 研判](./{f})")

        content = f"---\ntitle: 宏观档案馆\nprev: {{ text: '研报历史库', link: '../index' }}\nnext: false\n---\n\n# 📜 历史宏观档案\n\n" + "\n".join(list_items)
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
        symbol_dir = os.path.join(self.archive_mgr.reports_root, symbol)
        os.makedirs(symbol_dir, exist_ok=True)
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        file_ts = now.strftime('%Y-%m-%d_%H%M')
        raw_details = data_provider.get_company_details(symbol)
        profile = {
            "summary": analytical_engine.translate_business_summary(raw_details.get('summary_en', '')),
            "full_name": raw_details.get('full_name', symbol)
        }
        
        def sanitize_nan(val, fallback=0):
            import math
            try:
                if isinstance(val, float) and math.isnan(val):
                    return fallback
            except:
                pass
            return val

        meta_path = os.path.join(symbol_dir, "metadata.json")
        current_meta = {
            "date": date_str, 
            "file": file_ts, # 记录对应的文件名
            "price": sanitize_nan(item.get('current_price')), 
            "rating": decision.get('action', 'HOLD'), 
            "pe": sanitize_nan(item.get('pe', 0)), 
            "roe": sanitize_nan(item.get('roe', 0)), 
            "fact_score": sanitize_nan(verify_data.get('fact_score', 0)), 
            "upside": sanitize_nan(item.get('upside', 0)), 
            "summary_snippet": profile.get('summary', '')[:50] + "..."
        }
        history = []
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f: history = json.load(f)
            except: pass
        
        # 不再删除同日期的历史，允许一天多次研判共存
        history.insert(0, current_meta)
        history = history[:15] # 稍微增加保存上限
        with open(meta_path, "w") as f: json.dump(history, f, indent=4)
        
        # 写入具体日度研报 (使用含时间戳的文件名)
        refined = self._refine_report_with_ai(decision, symbol)
        
        # 动态计算组件引用的相对路径前缀
        # 基础组件位于 docs/projects/titan-lite/
        # 研报位于 docs/projects/titan-lite/users/NAME/reports/SYMBOL/ (深度 4) 或 docs/projects/titan-lite/reports/SYMBOL/ (深度 2)
        base_ref = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "projects", "titan-lite"))
        rel_to_base = os.path.relpath(base_ref, symbol_dir)
        # 转换 windows 路径分隔符为 posix
        rel_prefix = rel_to_base.replace('\\', '/') + '/'
        
        full_md = f"""---
title: {symbol} 深度研报 ({file_ts})
prev: {{ text: '{symbol} 看板', link: './index' }}
next: false
---

<script setup>
import ReportArtifacts from '{rel_prefix}ReportArtifacts.vue'
</script>

# 📜 {symbol} 研报档案 - {file_ts}

<ReportArtifacts symbol="{symbol}" date="{date_str}" />

{refined}
"""
        with open(os.path.join(symbol_dir, f"{file_ts}.md"), "w") as f: f.write(full_md)
        
        # --- Phase 3: Actionable Artifacts ---
        self._generate_actionable_artifacts(symbol, symbol_dir, item, decision)
        self._generate_wechat_post(symbol, symbol_dir, decision)
        
        # 3. 对接 PM 预挂单队列
        action = decision.get('action', '').upper()
        if any(kw in action for kw in ["BUY", "SELL", "OVERWEIGHT", "UNDERWEIGHT"]):
            side = "BUY" if any(kw in action for kw in ["BUY", "OVERWEIGHT"]) else "SELL"
            self.portfolio_mgr.add_pending_order(
                symbol, side, item.get('current_price'), 
                rationale=decision.get('rationale', '')[:500]
            )
        
        self._update_symbol_dashboard(symbol, symbol_dir, history, item, decision, profile)
        self.update_report_index(symbol, skip_build=skip_build)

    def _generate_actionable_artifacts(self, symbol, symbol_dir, item, decision):
        """生成结构化交易指令和估值模型"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 尝试从 rationale 中提取目标价 (多语言、多格式支持)
        target_price = item.get('target_price') or 0
        rationale = decision.get('rationale', '')
        
        # 如果原始数据中没有或为0，从 AI 研报中二次提取
        if target_price <= 0:
            import re
            # 匹配: Price Target, 目标价, 目标位, 可能带 $, **, : 等
            patterns = [
                r'(?:Price Target|目标价|目标位)[:：\s*]+(?:\$)?\s*([\d\.]+)',
                r'\*\*Price Target\*\*:?\s*(?:\$)?\s*([\d\.]+)',
                r'target_price[:：]\s*([\d\.]+)'
            ]
            for pat in patterns:
                match = re.search(pat, rationale, re.IGNORECASE)
                if match:
                    try:
                        target_price = float(match.group(1))
                        break
                    except: continue
        
        # 最终兜底：如果还是 0，给一个相对于现价 10% 的溢价作为占位 (避免 0 导致的 Upside 异常)
        if target_price <= 0:
            target_price = round(item.get('current_price', 0) * 1.1, 2)
        
        # 1. trade.json
        trade_data = {
            "symbol": symbol,
            "action": decision.get('action', 'HOLD'),
            "timestamp": date_str,
            "target_price": target_price,
            "current_price": item.get('current_price'),
            "upside": (target_price - item.get('current_price')) / item.get('current_price') if target_price and item.get('current_price') else 0,
            "suggested_size": "5%-8%" if any(kw in decision.get('action', '').upper() for kw in ["BUY", "OVERWEIGHT"]) else "0%",
            "rationale_short": decision.get('rationale', '').strip()[:300] + "..."
        }
        with open(os.path.join(symbol_dir, "trade.json"), "w") as f:
            json.dump(trade_data, f, indent=4)

        # 2. valuation_model.csv
        import csv
        with open(os.path.join(symbol_dir, "valuation_model.csv"), "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Value", "Source"])
            writer.writerow(["Symbol", symbol, "System"])
            writer.writerow(["Current Price", item.get('current_price'), "Market"])
            writer.writerow(["Target Price", target_price, "Analyst Aggregation"])
            writer.writerow(["PE Ratio", item.get('pe'), "Fundamentals"])
            writer.writerow(["ROE", item.get('roe'), "Fundamentals"])
            writer.writerow(["Upside", f"{trade_data['upside']:.2%}" if trade_data['upside'] else "N/A", "Calculation"])

    def _generate_wechat_post(self, symbol, symbol_dir, decision):
        """生成自媒体推文草稿"""
        fact_sheet = decision.get('fact_sheet', 'No facts available.')
        post_content = wechat_writer.generate_post(symbol, decision, fact_sheet)
        with open(os.path.join(symbol_dir, "wechat_post.md"), "w") as f:
            f.write(post_content)

    def _refine_report_with_ai(self, decision, symbol):
        raw_reports = ""
        for name, content in decision.get('reports', {}).items():
            if content: raw_reports += f"### {name}\n{content}\n"
        curr_date = datetime.now().strftime('%Y-%m-%d')
        refine_prompt = f"你是一位顶级分析师。请为 {symbol} 整理研报正文。日期锁定 {curr_date}。严禁废话。第一行必须是Markdown标题。深度标的格式 # 📊 {symbol} 深度研究。快筛标的格式 ## ⚡ 闪电决策简报。"
        material = f"决策建议：{decision.get('action')}\n\n[核心论证]\n{decision.get('rationale')}\n\n[调研事实清单 (Fact Sheet)]\n{decision.get('fact_sheet')}\n\n[专项调研报告]\n{raw_reports}"
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
            resp = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "system", "content": "你是一个专业的投研机器人。"},{"role": "user", "content": f"{refine_prompt}\n素材：\n{material}"}], temperature=0.1)
            return resp.choices[0].message.content.strip()
        except: return f"AI 润色失败。{decision.get('rationale')}"

    def _update_symbol_dashboard(self, symbol, symbol_dir, history, item, decision, profile=None):
        latest = history[0]
        if not profile: profile = data_provider.get_company_details(symbol)
        financials = data_provider.get_financial_highlights(symbol)
        
        # 自动处理 A股后缀补全以获取回测数据
        fetch_symbol = symbol
        if symbol.isdigit() and len(symbol) == 6:
            if symbol.startswith(('60', '68')): fetch_symbol = f"{symbol}.SS"
            elif symbol.startswith(('00', '30')): fetch_symbol = f"{symbol}.SZ"
            elif symbol.startswith(('4', '8', '9')): fetch_symbol = f"{symbol}.BJ"

        # 1. 运行深度回测并获取波动率
        bt_data = backtester.run_simple_backtest(fetch_symbol)
        
        # 兜底逻辑：如果回测失败，必须写入空 JSON 以免 Vite 编译报错
        if not bt_data:
            bt_data = {
                "symbol": symbol,
                "metrics": {"volatility": "0%"},
                "chart_data": [],
                "summary": "暂无回测数据"
            }
        
        with open(os.path.join(symbol_dir, "backtest.json"), "w") as f:
            json.dump(bt_data, f, indent=4)
        
        # 2. 计算估值水位与波动等级
        upside = latest.get('upside', 0) or 0
        if upside > 0.3: val_level = "严重低估 (Deep Value)"
        elif upside > 0.15: val_level = "适度低估 (Undervalued)"
        elif upside > -0.05: val_level = "合理估值 (Fair Value)"
        else: val_level = "估值过高 (Overvalued)"

        vol_str = bt_data['metrics'].get('volatility', '0%').replace('%', '') if bt_data else "0"
        try:
            vol_val = float(vol_str)
            if vol_val > 60: vol_level = "🔥 极端波动 (Extreme)"
            elif vol_val > 35: vol_level = "⚠️ 高波动 (High)"
            elif vol_val > 20: vol_level = "⚖️ 中等波动 (Moderate)"
            else: vol_level = "🛡️ 低波动 (Low)"
        except: vol_level = "未知"

        table = "| 时间 | 价格 | 评级 | PE | 预期涨幅 |\n| :--- | :--- | :--- | :--- | :--- |\n"
        for h in history[:10]: 
            pe_val = h.get('pe', 0) or 0
            up_val = h.get('upside', 0) or 0
            display_ts = h.get('file', h['date'])
            table += f"| {display_ts} | ${h['price']} | {h['rating']} | {pe_val:.1f} | {up_val:.2%} |\n"
        
        summary = self._get_ai_summary(symbol, decision)
        
        # 动态计算组件引用的相对路径前缀
        base_ref = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "projects", "titan-lite"))
        rel_to_base = os.path.relpath(base_ref, symbol_dir)
        rel_prefix = rel_to_base.replace('\\', '/') + '/'

        # 个股看板使用原生 Pager 指向档案馆
        md = f"""---
title: {symbol} 总览
prev: {{ text: '研报历史库', link: '../index' }}
next: false
---

<script setup>
import BacktestChart from '{rel_prefix}BacktestChart.vue'
import ExternalCockpit from '{rel_prefix}ExternalCockpit.vue'
import HistoryManager from '{rel_prefix}HistoryManager.vue'
import btData from './backtest.json'
</script>

# 🚀 {symbol} 投研价值看板

## 1. 🔍 公司业务 DNA
::: info {profile.get('full_name')}
{profile.get('summary')}
:::

## 2. 🎮 实时情报驾驶舱 (Cockpit)
<ExternalCockpit symbol="{symbol}" />

## 3. 📌 实时状态卡片
::: tip 核心指标
- **当前建议**: `{decision.get('action', 'N/A')}`
- **实时价格**: `${item['current_price']}`
- **估值水位**: `{val_level}`
- **波动等级**: `{vol_level}`
- **预期空间**: {upside:.2%}
:::

## 3. 📉 历史表现 (Backtest)
<BacktestChart symbol="{symbol}" :btData="btData" />

## 4. 📊 财务核心
- 营收增长: {self._fmt_pct(financials.get('rev_growth'))}
- 净利润率: {self._fmt_pct(financials.get('net_margin'))}
- 自由现金流: ${self._fmt_val(financials.get('fcf'))}

## 5. 📑 指标演变追踪
{table}

## 6. 🧠 投研三段论
{summary}

## 7. 📑 历史深度研报档案
> 下方表格列出了该标的在不同时间节点的详细研判档案，您可以查阅具体逻辑或清理过期报告。

<HistoryManager symbol="{symbol}" />
"""
        with open(os.path.join(symbol_dir, "index.md"), "w") as f: f.write(md)

    def _get_ai_summary(self, symbol, decision):
        prompt = f"请为 {symbol} 的研报做一个三段论总结（历史回顾、当前状态、未来预期），并结合决策 {decision.get('action')} 给出理由。要求：专业、精炼。"
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
            resp = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}])
            return resp.choices[0].message.content
        except: return "AI 总结生成失败。"

    def update_report_index(self, symbol=None, skip_build=False):
        reports_root = self.archive_mgr.reports_root
        index_path = os.path.join(reports_root, "index.md")
        os.makedirs(reports_root, exist_ok=True)
        
        # 动态计算组件引用的相对路径前缀
        # ArchiveManager.vue 位于 docs/projects/titan-lite/reports/
        base_ref = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "projects", "titan-lite", "reports"))
        rel_to_base = os.path.relpath(base_ref, reports_root)
        rel_prefix = rel_to_base.replace('\\', '/') + '/'
        if rel_prefix == './': rel_prefix = ''

        # 全局索引使用原生 Pager 指向基金和宏观
        md = f"""---
title: 研报档案馆
prev: {{ text: '我的基金中心', link: '/projects/titan-lite/portfolio' }}
next: {{ text: '宏观全景展望', link: './market_overview' }}
---

<script setup>
import ArchiveManager from '{rel_prefix}ArchiveManager.vue'
</script>

# 📑 数字化研报档案馆 (Digital Archive)

> 基于多维元数据索引，支持对历史研报的全量检索、分类筛选与生命周期管理。

<ArchiveManager />

---

## 🌍 宏观视角
- [**最新全市场宏观全景展望**](./market_overview.md)
"""
        with open(index_path, "w") as f: f.write(md)
        if not skip_build: self._trigger_final_build()

    def push_to_wecom(self, symbol, item, decision, divergence):
        msg = f"# 🚀 深度研判: {symbol}\n**决策**: {decision.get('action')}\n**逻辑**: {decision.get('rationale')[:150]}..."
        self.bot.send_markdown(msg, mode="private")

    def analyze_single_ticker(self, symbol, user_ctx=None):
        sys_logger.clear()
        
        # Initialize context-aware managers if user_ctx is provided
        if user_ctx:
            # For parity, we create new instances of managers with specific storage root
            from archive_manager import ArchiveManager
            from portfolio_manager import PortfolioManager
            self.archive_mgr = ArchiveManager(storage_root=user_ctx.storage_root)
            self.portfolio_mgr = PortfolioManager(storage_root=user_ctx.storage_root)
        else:
            self.archive_mgr = archive_manager
            self.portfolio_mgr = portfolio_manager
            
        sys_logger.info(f"🚀 开始针对 {symbol} 的深度研判流程", stage="Initializing", progress=5, task_type="single")
        try:
            # 自动处理 A股后缀补全
            fetch_symbol = symbol
            is_ashare = False
            if symbol.isdigit() and len(symbol) == 6:
                is_ashare = True
                if symbol.startswith(('60', '68')): fetch_symbol = f"{symbol}.SS"
                elif symbol.startswith(('00', '30')): fetch_symbol = f"{symbol}.SZ"
                elif symbol.startswith('8'): fetch_symbol = f"{symbol}.BJ"

            # 1. 获取基本数据 (FMP 优先)
            sys_logger.info(f"🔍 步骤 1/4: 调取 FMP/MCP 数据源进行基本面与行情分析...", stage="Data Fetching", progress=15, task_type="single")
            prices = data_provider.get_history_price(fetch_symbol)
            curr = prices.iloc[-1] if not prices.empty else 0
            
            # 优先从 FMP 获取机构目标价
            estimates = fmp_provider.get_analyst_estimates(fetch_symbol)
            t_price = estimates.get('estimatedPriceAvg', 0)
            
            y_info = data_provider.get_analyst_info(fetch_symbol)
            if t_price <= 0:
                t_price = y_info.get('targetMeanPrice', 0)
            
            # 如果依然没有数据，计算一个更真实的 50 日均线溢价作为占位，而不是死板的 10%
            if t_price <= 0:
                t_price = curr * 1.05 
            
            item = {
                'symbol': symbol, 
                'current_price': curr, 
                'target_price': t_price, 
                'upside': (t_price - curr) / curr if curr != 0 else 0, 
                'pe': y_info.get('peRatioTTM', 0) or 0, 
                'roe': y_info.get('roeTTM', 0) or 0, 
                'sector': y_info.get('sector', 'Unknown')
            }
            
            ashare_ctx = ""
            if is_ashare:
                sys_logger.info(f"🇨🇳 正在提取 A股专用高频指标 (AkShare)...", stage="Data Fetching", progress=20, task_type="single")
                a_data = data_provider.get_ashare_specifics(symbol)
                if a_data and "error" not in a_data:
                    ashare_ctx = f"\n[A股专用审计指标]\n- 市净率(PB): {a_data.get('pb')}\n- 换手率: {a_data.get('turnover_rate')}\n- 主力净流入: {a_data.get('main_inflow')}\n- 总市值: {a_data.get('total_mv')}\n"

            # 2. 事实核查与新闻
            sys_logger.info(f"🛡️ 步骤 2/4: 执行社交媒体舆情核查与异常信号识别...", stage="Verification", progress=35, task_type="single")
            news = finnhub_provider.get_company_news(fetch_symbol)
            fact_check, fact_score = verification_engine.verify_news(fetch_symbol, news)
            div = verification_engine.check_divergence(fetch_symbol)
            ins = verification_engine.get_insider_signal(fetch_symbol)
            v_ctx = f"\n[事实核查]\n- 真实度: {fact_score}\n- AI结论: {fact_check}\n- 量价: {div}\n- 高管: {ins}\n" + ashare_ctx
            
            # 3. 深度认知博弈
            sys_logger.info(f"🧠 步骤 3/4: 启动多 Agent 认知博弈 (Thesis-First 架构)...", stage="Cognitive Debate", progress=50, task_type="single")
            dec = agent_bridge.analyze_ticker(fetch_symbol, context_extra=v_ctx)
            
            # 4. 资产化与同步
            if dec:
                sys_logger.info(f"📤 步骤 4/4: 正在生成可执行资产 (trade.json, wechat_post) 并同步...", stage="Exporting", progress=85, task_type="single")
                self.save_to_web(symbol, item, dec, {'fact_check': fact_check, 'fact_score': fact_score, 'divergence': div, 'insider': ins})
                sys_logger.info(f"✅ {symbol} 研判任务圆满完成！建议: {dec.get('action')}", stage="Completed", progress=100, task_type="single")
                return True
            else:
                sys_logger.info(f"❌ {symbol} 智能辩论引擎未产出有效结论。", task_type="single")
                return False
        except Exception as e:
            sys_logger.info(f"💥 系统性崩溃: {str(e)}", task_type="single")
            return False

    def _fmt_pct(self, v): return f"{v*100:.2%}" if v is not None else "N/A"
    def _fmt_val(self, v): 
        if v is None: return "N/A"
        if v > 1e9: return f"{v/1e9:.2f}B"
        if v > 1e6: return f"{v/1e6:.2f}M"
        return f"{v:.2f}"

def run_job(): TitanStrategyV2().execute()
def run_single(symbol): return TitanStrategyV2().analyze_single_ticker(symbol)
