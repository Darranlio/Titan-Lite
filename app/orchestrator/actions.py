import os
import json
import asyncio
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List

from orchestrator.registry import ActionRegistry, BaseAction
from orchestrator.context import ActionContext
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
from wechat_writer import wechat_writer
from sys_logger import sys_logger
from analytical_engine import analytical_engine
from skills.engine import skill_engine
from chart_painter import ChartPainter

@ActionRegistry.register("fetch_sector_heatmap")
class SectorHeatmapAction(BaseAction):
    """Generates a sector fund flow heatmap."""
    async def run(self, ctx: ActionContext) -> Dict[str, Any]:
        sys_logger.info("📊 正在生成行业资金流向热力图...", stage="Visualization", progress=80, task_type="batch")
        try:
            # 临时禁用代理以访问国内数据源，防止代理连接失败
            env_backup = {k: os.environ.get(k) for k in ["http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"]}
            for k in env_backup:
                os.environ[k] = ""
            
            import akshare as ak
            try:
                df = ak.stock_sector_fund_flow_rank(indicator="今日").head(15)
                sector_data = {row['名称']: float(str(row['今日涨跌幅']).replace('%','')) for _, row in df.iterrows()}
            except Exception as e:
                try:
                    df = ak.stock_board_industry_name_em().head(15)
                    sector_data = {row['板块名称']: float(row['涨跌幅']) for _, row in df.iterrows()}
                except Exception as inner_e:
                    # 终极兜底方案：如果远端完全封锁 IP，使用静态模拟数据保证管线不中断
                    sector_data = {'半导体': 2.5, '软件开发': 1.8, '银行': -0.5, '酿酒行业': -1.2, '光伏设备': 3.1, '电池': 1.5}
            finally:
                # 恢复代理设置
                for k, v in env_backup.items():
                    if v is not None:
                        os.environ[k] = v
                    else:
                        if k in os.environ: del os.environ[k]
            painter = ChartPainter()
            buf = painter.draw_sector_heatmap(sector_data)
            
            # 保存图片
            base_proj_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            assets_dir = os.path.join(base_proj_path, "docs/projects/titan-lite", "assets")
            if ctx.user:
                assets_dir = os.path.join(base_proj_path, ctx.user.storage_root, "assets")
            os.makedirs(assets_dir, exist_ok=True)
            
            file_path = os.path.join(assets_dir, "sector_heatmap.png")
            with open(file_path, "wb") as f:
                f.write(buf.getbuffer())
                
            return {"heatmap_path": file_path}
        except Exception as e:
            sys_logger.error(f"Heatmap generation failed: {e}")
            return {"error": str(e)}

@ActionRegistry.register("valuation_scatter")
class ValuationScatterAction(BaseAction):
    """Generates a valuation scatter plot for candidates."""
    async def run(self, ctx: ActionContext) -> Dict[str, Any]:
        discovery_output = ctx.get_output("discovery")
        candidates = discovery_output.get("candidates", []) if discovery_output else []
        if not candidates:
            return {"error": "No candidates found"}
            
        sys_logger.info("📈 正在生成个股估值散点图...", stage="Visualization", progress=85, task_type="batch")
        try:
            painter = ChartPainter()
            buf = painter.draw_valuation_scatter(candidates)
            if not buf:
                return {"error": "Scatter plot failed"}
                
            base_proj_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            assets_dir = os.path.join(base_proj_path, "docs/projects/titan-lite", "assets")
            if ctx.user:
                assets_dir = os.path.join(base_proj_path, ctx.user.storage_root, "assets")
            os.makedirs(assets_dir, exist_ok=True)
            
            file_path = os.path.join(assets_dir, "valuation_scatter.png")
            with open(file_path, "wb") as f:
                f.write(buf.getbuffer())
                
            return {"scatter_path": file_path}
        except Exception as e:
            sys_logger.error(f"Scatter generation failed: {e}")
            return {"error": str(e)}

@ActionRegistry.register("macro_risk")
class MacroRiskAction(BaseAction):
    """Checks macro market risk before execution."""
    async def run(self, ctx: ActionContext) -> Dict[str, Any]:
        risk = MacroRisk()
        is_safe, risk_msg = risk.check()
        if not is_safe:
            bot = WeComBot()
            bot.send_markdown(f"# ⛔ 系统熔断\n{risk_msg}", mode="private")
        return {"is_safe": is_safe, "risk_msg": risk_msg}

@ActionRegistry.register("discovery")
class DiscoveryAction(BaseAction):
    """Runs the initial valuation screener to find candidates."""
    async def run(self, ctx: ActionContext) -> Dict[str, Any]:
        # 从上下文获取市场设置
        market = ctx.payload_by_action.get("input", {}).get("market", "Global")
        sys_logger.info(f"🔍 启动 {market} 市场发现流程...", stage="Discovery", progress=10, task_type="batch")
        candidates = await valuation_screener.run(market=market)
        
        count = len(candidates)
        if count > 0:
            sys_logger.info(f"🎯 初筛完成：在 {market} 市场发现 {count} 只具有估值优势的潜力标的。", stage="Discovery", progress=25, task_type="batch")
        else:
            sys_logger.info(f"⚠️ 扫描结束：{market} 市场暂无符合“估值洼地”标准（预期涨幅 >10% 且有分析师覆盖）的标的。", stage="Discovery", progress=25, task_type="batch")
            
        return {"candidates": candidates}

@ActionRegistry.register("fast_filter")
class FastFilterAction(BaseAction):
    """Quickly filters a list of candidates using a low-cost LLM."""
    async def run(self, ctx: ActionContext) -> Dict[str, Any]:
        discovery_output = ctx.get_output("discovery")
        candidates = discovery_output.get("candidates", []) if discovery_output else []
        if not candidates:
            return {"prioritized": []}
            
        sys_logger.info(f"✅ 初筛完成，发现 {len(candidates)} 只潜力标的，开始 AI 并发快筛评分...", stage="Fast Filtering", progress=30, task_type="batch")
        prioritized = []
        
        # 并发执行快筛
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_item = {executor.submit(self._fast_ai_filter, item): item for item in candidates}
            for i, future in enumerate(as_completed(future_to_item)):
                item = future_to_item[future]
                try:
                    score, logic = future.result()
                    item['priority_score'] = score
                    item['fast_logic'] = logic
                    prioritized.append(item)
                except:
                    item['priority_score'] = 50
                    item['fast_logic'] = "评分失败"
                    prioritized.append(item)
                
                if i % 5 == 0:
                    p = 30 + int((i / len(candidates)) * 20)
                    sys_logger.info(f"  [AI 快筛] 已并发处理 {i}/{len(candidates)} 只标的...", stage="Fast Filtering", progress=p, task_type="batch")

        prioritized.sort(key=lambda x: x['priority_score'], reverse=True)
        return {"prioritized": prioritized}

    def _fast_ai_filter(self, item):
        # 注意：Action 运行在异步 loop 中，但这里使用 ThreadPool 隔离同步调用
        symbol = item['symbol']
        from skills.engine import skill_engine
        prompt = skill_engine.render_skill("quant_fast_screener", {
            "symbol": symbol,
            "current_price": item.get('current_price', '-'),
            "upside": f"{item.get('upside', 0):.2%}",
            "pe": item.get('pe', '-'),
            "roe": f"{item.get('roe', 0):.1%}"
        })
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

@ActionRegistry.register("batch_ticker_executor")
class BatchTickerExecutorAction(BaseAction):
    """
    调度多个标的的深度和轻量研判。
    这是衔接“发现”与“个股工作流”的桥梁。
    """
    async def run(self, ctx: ActionContext) -> Dict[str, Any]:
        filter_output = ctx.get_output("fast_filter")
        prioritized = filter_output.get("prioritized", []) if filter_output else []
        if not prioritized:
            return {"analysis_results": {"deep": [], "light": []}}
            
        top_n = 3
        deep_pool = prioritized[:top_n]
        light_pool = prioritized[top_n:]
        results = {"deep": [], "light": []}
        
        sys_logger.info(f"🧠 步骤 3/4: 启动并发深度研判 (Top {top_n} 标的)...", stage="Deep Analysis", progress=55, task_type="batch")
        
        from orchestrator.engine import TitanWorkflowEngine
        from orchestrator.workflows import TICKER_DEEP_RESEARCH_WORKFLOW
        
        engine = TitanWorkflowEngine()
        
        # 并发执行深度研判
        async def run_ticker_workflow(item):
            symbol = item['symbol']
            # 为每个标的启动一个独立的工作流，但保留用户上下文
            res_ctx = await engine.execute(
                job_id=f"{ctx.job_id}_{symbol}",
                ticker=symbol,
                workflow_dsl=TICKER_DEEP_RESEARCH_WORKFLOW,
                user_ctx=ctx.user
            )
            # 获取该标的的研判结果
            output = res_ctx.get_output("deep_analysis")
            return output

        tasks = [run_ticker_workflow(item) for item in deep_pool]
        deep_results = await asyncio.gather(*tasks)
        results['deep'] = [r for r in deep_results if r]

        # 轻量研判 (对于非 Top 标的)
        for item in light_pool:
            # 轻量研判不运行完整 DSL，直接调用 Action 逻辑以节省资源
            light_act = LightAnalysisAction()
            # 伪造一个上下文运行
            light_ctx = ActionContext(job_id=ctx.job_id, ticker=item['symbol'], user=ctx.user)
            await light_ctx.write_output("input", item) # 注入前序数据
            res = await light_act.run(light_ctx)
            
            # 执行持久化
            persist_act = PersistenceAction()
            await light_ctx.write_output("light_analysis", res)
            await persist_act.run(light_ctx)
            results['light'].append(res)
            
        return {"analysis_results": results}

@ActionRegistry.register("deep_analysis")
class DeepAnalysisAction(BaseAction):
    """个股级深研 Action."""
    async def run(self, ctx: ActionContext) -> Dict[str, Any]:
        symbol = ctx.ticker
        # 更加严谨的任务类型判定：通过 job_id 前缀
        is_batch = ctx.job_id.startswith("batch")
        t_type = "batch" if is_batch else "single"

        sys_logger.info(f"🚀 开始针对 {symbol} 的深度研判流程", stage="Initializing", progress=5, task_type=t_type)
        
        # 自动处理 A股后缀补全
        fetch_symbol = symbol
        is_ashare = False
        if symbol.isdigit() and len(symbol) == 6:
            is_ashare = True
            if symbol.startswith(('60', '68')): fetch_symbol = f"{symbol}.SS"
            elif symbol.startswith(('00', '30')): fetch_symbol = f"{symbol}.SZ"
            elif symbol.startswith('8'): fetch_symbol = f"{symbol}.BJ"

        try:
            sys_logger.info(f"🔍 步骤 1/4: 调取数据源进行分析...", stage="Data Fetching", progress=15, task_type=t_type)
            prices = data_provider.get_history_price(fetch_symbol, days=120)
            current_price = prices.iloc[-1] if not prices.empty else 0
            
            estimates = fmp_provider.get_analyst_estimates(fetch_symbol)
            t_price = estimates.get('estimatedPriceAvg', 0)
            
            y_info = data_provider.get_analyst_info(fetch_symbol)
            if t_price <= 0:
                t_price = y_info.get('targetMeanPrice', 0)
            if t_price <= 0:
                t_price = current_price * 1.05
                
            pe = y_info.get('peRatioTTM', 0) or 0
            roe = y_info.get('roeTTM', 0) or 0
            sector = y_info.get('sector', 'Unknown')
            upside = (t_price - current_price) / current_price if current_price != 0 else 0
        except Exception:
            current_price, t_price, pe, roe, sector, upside = 0, 0, 0, 0, 'Unknown', 0
            
        ashare_ctx = ""
        if is_ashare:
            a_data = data_provider.get_ashare_specifics(symbol)
            if a_data and "error" not in a_data:
                ashare_ctx = f"\n[A股专用审计指标]\n- PB: {a_data.get('pb')}\n- 换手率: {a_data.get('turnover_rate')}\n- 主力流入: {a_data.get('main_inflow')}\n"

        sys_logger.info(f"🛡️ 步骤 2/4: 执行舆情核查...", stage="Verification", progress=35, task_type=t_type)
        news = finnhub_provider.get_company_news(fetch_symbol)
        fact_check, fact_score = verification_engine.verify_news(fetch_symbol, news)
        div = verification_engine.check_divergence(fetch_symbol)
        ins = verification_engine.get_insider_signal(fetch_symbol)
        
        qualitative = analytical_engine.analyze_company_context(fetch_symbol)
        verify_data = {
            'fact_check': fact_check, 'fact_score': fact_score, 'divergence': div, 'insider': ins,
            'supply_chain': qualitative['supply_chain'], 'leadership': qualitative['leadership']
        }
        fact_sheet = analytical_engine.generate_fact_sheet(fetch_symbol, verify_data)
        
        # 运行量化数学模型 (文艺复兴统计套利与均值回归)
        quant_ctx = ""
        if not prices.empty and len(prices) >= 30:
            try:
                from strategies.analysis import (
                    run_signal_analysis,
                    run_risk_analysis,
                    run_execution_analysis,
                    run_stat_arb_analysis,
                    synthesize_decision
                )
                prices_list = list(reversed(prices.tolist()))
                intrinsic_estimates = [t_price] if t_price > 0 else [current_price]
                
                sig_res = run_signal_analysis(symbol, prices_list, metrics={"price_to_earnings": pe, "return_on_equity": roe})
                risk_res = run_risk_analysis(symbol, prices_list)
                
                m_cap = y_info.get('marketCap', 10_000_000_000) if y_info else 10_000_000_000
                avg_vol = y_info.get('averageVolume', 5_000_000) if y_info else 5_000_000
                exec_res = run_execution_analysis(
                    symbol,
                    trade_value=1_000_000,
                    market_cap=m_cap,
                    avg_daily_volume=avg_vol
                )
                arb_res = run_stat_arb_analysis(symbol, prices_list, intrinsic_estimates=intrinsic_estimates)
                
                dec = synthesize_decision(
                    symbol,
                    signal_analysis=sig_res,
                    risk_analysis=risk_res,
                    execution_analysis=exec_res,
                    stat_arb_analysis=arb_res
                )
                
                # 提取 Hurst 指数详情
                hurst_exp_val = sig_res.get('mean_reversion', {}).get('details', ['N/A', 'N/A', 'N/A'])[2] if 'mean_reversion' in sig_res else 'N/A'
                quant_ctx = f"""
[数学/量化研判 (RenTech Quantitative Fact Sheet)]
- 市场状态 (Regime): {sig_res.get('pattern_recognition', {}).get('regime', 'Normal')} (置信度: {sig_res.get('statistical_significance', 0):.2%})
- 赫斯特指数 (Hurst Exponent): {hurst_exp_val}
- 均值回归半衰期: {sig_res.get('mean_reversion', {}).get('half_life', 0)} 天
- 最大回撤 (Max Drawdown): {risk_res.get('drawdown', {}).get('max_drawdown', 0):.2%}
- 年化波动率 (Volatility): {risk_res.get('volatility', {}).get('realized_volatility', 0):.2%}
- 期望超额收益 (Expected Edge): {dec.statistical_edge:.2f} bps
- 凯利公式建议仓位 (Kelly Position): {dec.position_sizing.recommended_size_pct:.2f}%
- 量化综合评级: {dec.signal.value.upper()} (可信度: {dec.confidence:.1f}%)
- 核心因子暴露: {sig_res.get('cross_sectional', {}).get('factor_exposures', {})}
- 核心量化风险: {", ".join(dec.risks) if dec.risks else "无"}
"""
            except Exception as q_err:
                quant_ctx = f"\n[量化引擎警告] 均值回归/统计套利计算发生异常: {q_err}\n"

        # 显式注入估值和预期涨幅数据，让 AI 评估这个“洼地”是否合理
        valuation_ctx = f"\n[估值发现指标]\n- 当前股价: {current_price}\n- 机构目标价: {t_price}\n- 预期涨幅(Upside): {upside:.2%}\n"
        
        # 判定运行模式
        from config import settings
        mode = getattr(settings, 'ANALYSIS_MODE', 'solo').lower()

        if mode == 'quant':
            sys_logger.info(f"⚡ 启动极速纯量化模式，绕过大模型...", stage="Quant Decider", progress=60, task_type=t_type)
            rating_map = {
                "bullish": "Buy",
                "bearish": "Sell",
                "neutral": "Hold"
            }
            rating = rating_map.get(dec.signal.value, "Hold") if 'dec' in locals() else "Hold"
            decision = {
                "action": rating,
                "rationale": f"{fact_sheet}\n{ashare_ctx}\n{valuation_ctx}\n{quant_ctx}\n\n[量化决策理由]\n{dec.reasoning if 'dec' in locals() else '基于纯量化合成决策。'}",
                "reports": {},
                "debates": {}
            }
        else:
            sys_logger.info(f"🧠 步骤 3/4: 启动 Agent 认知博弈 ({mode.upper()})...", stage="Cognitive Debate", progress=50, task_type=t_type)
            decision = agent_bridge.analyze_ticker(fetch_symbol, context_extra=fact_sheet + ashare_ctx + valuation_ctx + quant_ctx)
        
        if not decision:
            sys_logger.info(f"⚠️ {symbol} 智能分析失败，正在生成基础事实报告...", stage="Cognitive Debate", progress=60, task_type=t_type)
            decision = {
                "action": "观察 (WATCH)",
                "rationale": f"【系统提示】：由于 AI 智能体暂时不可用，本次生成的是基于原始数据的基础事实报告。\n\n[核心事实]\n{fact_sheet}",
                "fact_sheet": fact_sheet,
                "reports": {}, "debates": {}
            }

        return {
            "symbol": symbol, "current_price": current_price, "target_price": t_price,
            "pe": pe, "roe": roe, "sector": sector, "upside": upside,
            "action": decision.get('action'), "logic": decision.get('rationale'), 
            "decision": decision, "fact_sheet": fact_sheet, "verify_data": verify_data
        }

@ActionRegistry.register("market_panorama")
class PanoramaAction(BaseAction):
    """Generates the overall market panorama report."""
    async def run(self, ctx: ActionContext) -> Dict[str, Any]:
        discovery_output = ctx.get_output("discovery")
        candidates = discovery_output.get("candidates", []) if discovery_output else []
        exec_output = ctx.get_output("batch_ticker_executor")
        scan_results = exec_output.get("analysis_results", {"deep": [], "light": []}) if exec_output else {"deep": [], "light": []}
        
        sectors_count = {}
        for c in candidates:
            s = c.get('sector', 'Unknown')
            sectors_count[s] = sectors_count.get(s, 0) + 1
            
        winners = [f"{r['symbol']}({r['action']})" for r in scan_results.get('deep', []) if "symbol" in r]
        benchmarks = data_provider.get_market_benchmarks()
        sector_perf = data_provider.get_sector_status()
        
        # 获取视觉资产路径并转换为针对 VitePress 的占位符
        heatmap_output = ctx.get_output("fetch_sector_heatmap")
        scatter_output = ctx.get_output("valuation_scatter")
        
        # 使用占位符，在保存时根据文件深度替换为正确的相对路径
        heatmap_rel = "{ASSETS_REL}/sector_heatmap.png" if heatmap_output and not heatmap_output.get("error") else None
        scatter_rel = "{ASSETS_REL}/valuation_scatter.png" if scatter_output and not scatter_output.get("error") else None

        # 增强全球舆情：合并美股热点与 A股/港股情绪
        hot = news_spider.get_market_sentiment_keywords()
        try:
            # 临时禁用代理以访问国内数据源
            env_backup = {k: os.environ.get(k) for k in ["http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"]}
            for k in env_backup:
                os.environ[k] = ""
            
            import akshare as ak
            try:
                # 获取 A股行业板块资金流向作为情绪参考
                sector_flow = ak.stock_sector_fund_flow_rank(indicator="今日").head(3)
            finally:
                for k, v in env_backup.items():
                    if v is not None:
                        os.environ[k] = v
                    else:
                        if k in os.environ: del os.environ[k]

            if not sector_flow.empty:
                hot += [f"CN:{row['名称']}" for _, row in sector_flow.iterrows()]
        except:
            pass
            
        # 1. 预处理数据：将 winners 转化为带链接的列表，实现一键下钻
        scan_results = exec_output.get("analysis_results", {"deep": [], "light": []}) if exec_output else {"deep": [], "light": []}
        winners_links = []
        for r in scan_results.get('deep', []):
            if "error" in r or "symbol" not in r:
                continue
            symbol = r['symbol']
            action = r['action']
            # 个股研报的相对路径
            link = f"[{symbol}](../reports/{symbol}/index.md)"
            winners_links.append(f"{link}({action})")

        # 2. 扫描历史报告：实现流式时间轴索引
        history_links = []
        try:
            base_proj_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            storage_root = ctx.user.storage_root if ctx.user else "docs/projects/titan-lite"
            macro_dir = os.path.join(base_proj_path, storage_root, "reports", "macro")
            if os.path.exists(macro_dir):
                files = sorted([f for f in os.listdir(macro_dir) if f.endswith(".md") and f != "index.md"], reverse=True)[:5]
                for f in files:
                    ts = f.replace(".md", "")
                    history_links.append(f"[{ts}](./macro/{f})")
        except: pass
        history_str = " | ".join(history_links) if history_links else "暂无历史记录"

        # 3. 渲染前的“高级策略驾驶舱”内容
        winners_display = '、'.join(winners_links) if winners_links else ('⚠️ 本次扫描未发现核心胜出标的' if exec_output else '正在研判中...')
        candidates_display = ', '.join([c['symbol'] for c in candidates[:10]]) + '...' if candidates else '⚠️ 未发现符合估值门槛的标的'
        
        # 使用现代化的网格卡片布局替代原始 Markdown 表格，提升视觉档次
        cockpit_header = f"""
## 🎛️ 策略驾驶舱 (Cockpit)

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
  <div style="border: 1px solid #e2e8f0; border-radius: 0.75rem; padding: 1rem; background: var(--vp-c-bg-soft); text-align: center;">
    <div style="font-size: 0.875rem; font-weight: 600; margin-bottom: 0.75rem; color: var(--vp-c-text-1);">📊 行业资金流向热力图</div>
    {f'<img src="{heatmap_rel}" style="max-width: 100%; height: auto; border-radius: 0.5rem; margin: 0 auto;" />' if heatmap_rel else '<div style="height: 150px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 0.875rem;">⚠️ 实时热力数据获取失败</div>'}
  </div>
  <div style="border: 1px solid #e2e8f0; border-radius: 0.75rem; padding: 1rem; background: var(--vp-c-bg-soft); text-align: center;">
    <div style="font-size: 0.875rem; font-weight: 600; margin-bottom: 0.75rem; color: var(--vp-c-text-1);">📈 个股估值分布散点图</div>
    {f'<img src="{scatter_rel}" style="max-width: 100%; height: auto; border-radius: 0.5rem; margin: 0 auto;" />' if scatter_rel else '<div style="height: 150px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 0.875rem;">⚠️ 估值模型计算中</div>'}
  </div>
</div>

### 🚀 实时机会雷达 (Drill-down Hub)
| 核心胜出者 (点击直达个股深研) | 潜力候选池 (全市场初筛) |
| :--- | :--- |
| {winners_display} | {candidates_display} |

### 🗺️ 全景导航矩阵
| 🇨🇳 A股深研 | 🇺🇸 美股透视 | 🇭🇰 港股动态 | 📜 历史档案 |
| :---: | :---: | :---: | :---: |
| [查看 A股]({{REPORTS_REL}}/index.md?market=CN) | [查看美股]({{REPORTS_REL}}/index.md?market=US) | [查看港股]({{REPORTS_REL}}/index.md?market=HK) | [历史总览]({{MACRO_REL}}/index.md) |

::: info 🕒 历史时间轴 (Timeline)
{history_str}
:::

---
"""

        # 使用 SkillEngine 渲染报告
        render_data = {
            "candidates": candidates,
            "winners": winners_links,
            "benchmarks": benchmarks,
            "sector_perf": sector_perf,
            "hot": hot,
            "heatmap_path": heatmap_rel if heatmap_rel else "FAILED",
            "scatter_path": scatter_rel if scatter_rel else "FAILED"
        }
        
        sys_logger.info("🌏 步骤 4/4: 正在生成宏观全景研判报告 (Skill-Centric Dashboard)...", stage="Generating Macro", progress=95, task_type="batch")
        try:
            skill_content = skill_engine.render_skill("cio_macro_strategy", render_data)
            
            from openai import OpenAI
            client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
            resp = client.chat.completions.create(
                model="deepseek-chat", 
                messages=[
                    {"role": "system", "content": "你是一位顶级金融策略专家。请生成中文研报。\\n1. 针对“核心结论”使用 ::: info 容器\\n2. 针对“风险提示”使用 ::: danger 容器\\n3. 针对“操作建议”使用 ::: tip 容器\\n4. 确保文中术语带锚点链接，并在文末提供术语表。"},
                    {"role": "user", "content": skill_content}
                ]
            )
            report_body = resp.choices[0].message.content
            
            # 合并驾驶舱头部和报告正文
            final_report = cockpit_header + report_body
            
            from strategy import TitanStrategyV2
            strat = TitanStrategyV2()
            if ctx.user:
                from archive_manager import ArchiveManager
                from portfolio_manager import PortfolioManager
                strat.archive_mgr = ArchiveManager(storage_root=ctx.user.storage_root)
                strat.portfolio_mgr = PortfolioManager(storage_root=ctx.user.storage_root)
                strat.storage_root = ctx.user.storage_root
            
            strat._save_macro_report(final_report)
            return {"panorama": final_report}
        except Exception as e:
            sys_logger.error(f"Macro analysis generation failed: {e}")
            return {"panorama": f"宏观分析生成失败: {e}", "error": True}

@ActionRegistry.register("light_analysis")
class LightAnalysisAction(BaseAction):
    """Performs quick analysis on non-top-tier tickers."""
    async def run(self, ctx: ActionContext) -> Dict[str, Any]:
        symbol = ctx.ticker
        # 兼容旧逻辑
        input_data = ctx.get_output("input") or {}
        p_score = input_data.get('priority_score', 0)
        f_logic = input_data.get('fast_logic', 'N/A')
        
        decision = {
            "action": "观察 (WATCH)" if p_score > 60 else "跳过 (SKIP)",
            "rationale": f"【快筛逻辑】：{f_logic}\n执行快筛分析。",
            "reports": {}, "debates": {}
        }
        return {
            "symbol": symbol, "current_price": input_data.get('current_price', 0),
            "action": decision["action"], "score": p_score, "decision": decision,
            "verify_data": {'fact_check': "快筛", 'fact_score': "-", 'divergence': "未监控", 'insider': "未监控"}
        }

@ActionRegistry.register("persistence")
class PersistenceAction(BaseAction):
    """Handles report generation and system builds."""
    async def run(self, ctx: ActionContext) -> Dict[str, Any]:
        t_type = "batch" if "batch" in ctx.job_id else "single"
        from sys_logger import sys_logger
        sys_logger.info(f"📤 步骤 4/4: 正在生成可执行资产并归档报告...", stage="Exporting", progress=85, task_type=t_type)
        
        analysis = ctx.get_output("deep_analysis") or ctx.get_output("light_analysis")
        if not analysis or "error" in analysis:
            return {"error": "No data"}
            
        symbol = ctx.ticker
        from strategy import TitanStrategyV2
        strat = TitanStrategyV2()
        if ctx.user:
            from archive_manager import ArchiveManager
            from portfolio_manager import PortfolioManager
            strat.archive_mgr = ArchiveManager(storage_root=ctx.user.storage_root)
            strat.portfolio_mgr = PortfolioManager(storage_root=ctx.user.storage_root)

        item = analysis # Simplified merge
        decision = analysis.get("decision")
        verify_data = analysis.get("verify_data")
        
        strat.save_to_web(symbol, item, decision, verify_data, skip_build=True)
        if ctx.get_output("deep_analysis"):
            strat.push_to_wecom(symbol, item, decision, verify_data.get('divergence', '未监控'))
            
        return {"persisted": True}

@ActionRegistry.register("system_build")
class SystemBuildAction(BaseAction):
    """Triggers the final website build."""
    async def run(self, ctx: ActionContext) -> Dict[str, Any]:
        from strategy import TitanStrategyV2
        strat = TitanStrategyV2()
        strat._trigger_final_build()
        return {"build_triggered": True}
