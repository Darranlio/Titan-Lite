import os
import sys
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from config import settings
from langchain_core.callbacks import BaseCallbackHandler
from sys_logger import sys_logger

class ConsoleStreamHandler(BaseCallbackHandler):
    """
    实时打印 Agent 思考过程的处理器 (精简版)
    并同步推送到系统日志缓冲区
    """
    def on_chat_model_start(self, serialized, messages, **kwargs):
        # 1. 尝试从 LangGraph 元数据中提取当前 Node (Agent) 的名称
        metadata = kwargs.get("metadata", {})
        node_name = metadata.get("langgraph_node", "")
        
        # 2. 如果没拿到，尝试从 serialized 中提取
        if not node_name:
            node_name = serialized.get("name", "")

        display_name = node_name if node_name else "Agent"
        model_name = serialized.get("kwargs", {}).get("model", "DeepSeek")
        
        msg = f"🧠 {display_name} ({model_name}) 正在深度思考..."
        sys_logger.info(msg)

    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = serialized.get("name", "Unknown Tool")
        if tool_name in ["_get_current_time"]: return
        sys_logger.info(f"🛠️ 正在调用工具: {tool_name} (输入: {input_str[:100]}...)")
        print(f"  [Tool] 正在调用工具: {tool_name}...", flush=True)

    def on_tool_end(self, output, **kwargs):
        pass # 减少数据打印，只看调用

class AgentBridge:
    """
    Titan-Lite 与 TradingAgents 的桥接层 (增强日志版)
    """
    def __init__(self):
        # 映射配置
        os.environ["OPENAI_API_KEY"] = settings.LLM_API_KEY
        os.environ["OPENAI_BASE_URL"] = settings.LLM_BASE_URL
        os.environ["DEEPSEEK_API_KEY"] = settings.LLM_API_KEY
        
        # 初始化配置
        self.config = DEFAULT_CONFIG.copy()
        self.config["llm_provider"] = "deepseek" if "deepseek" in settings.LLM_BASE_URL.lower() else settings.LLM_PROVIDER
        
        # 针对不同 Provider 指定最佳模型
        if "deepseek" in settings.LLM_BASE_URL.lower() or self.config["llm_provider"] == "deepseek":
            self.config["deep_think_llm"] = "deepseek-chat"
            self.config["quick_think_llm"] = "deepseek-chat"
            print(">>> 已检测到 DeepSeek API，正在启动深度逻辑模式...")
        elif settings.LLM_PROVIDER == "google":
            self.config["deep_think_llm"] = "gemini-2.0-flash"
            self.config["quick_think_llm"] = "gemini-2.0-flash"
        
        self.config["checkpoint_enabled"] = False 
        self.config["max_debate_rounds"] = 1 # 针对 2G 内存和速度优化，设为 1 轮
        self.config["max_recur_limit"] = 50 # 限制递归次数，防止死循环
        self.config["output_language"] = "Chinese" # <--- 关键：确保 PM 和分析师最终输出中文
        
        # 增加实时日志处理器
        self.callbacks = [ConsoleStreamHandler()]
        
        # 注入配置
        # 强制锁定 temperature 为 0，确保金融决策的一致性
        llm_kwargs = {"temperature": 0, "top_p": 0.1}
        
        self.agent_graph = TradingAgentsGraph(
            debug=True, 
            config=self.config,
            callbacks=self.callbacks,
            **llm_kwargs
        )


    def analyze_ticker(self, symbol, date=None, context_extra=""):
        if date is None:
            from datetime import datetime
            date = datetime.now().strftime("%Y-%m-%d")

        print(f"\n" + "="*50)
        print(f">>> [Agent] 启动深度研判: {symbol} @ {date}")
        print("="*50 + "\n")

        try:
            # 1. 调用强大的多智能体图 (TradingAgents)
            # final_state: 完整的状态机字典
            # rating: 提取出来的评级字符串 (e.g., "BUY")
            final_state, rating = self.agent_graph.propagate(symbol, date)
            
            # 2. 构建结构化的决策对象
            decision = {
                "action": rating,
                "rationale": final_state.get("final_trade_decision", "无详细理由"),
                "fact_sheet": final_state.get("fact_sheet", "No fact sheet generated."),
                "reports": {
                    'market': final_state.get('market_report'),
                    'sentiment': final_state.get('sentiment_report'),
                    'news': final_state.get('news_report'),
                    'fundamentals': final_state.get('fundamentals_report'),
                },
                "debates": {
                    'investment': final_state.get('investment_debate_state'),
                    'risk': final_state.get('risk_debate_state'),
                }
            }

            if context_extra:
                decision['rationale'] = f"{context_extra}\n{decision.get('rationale', '')}"
            
            print(f"\n>>> [Agent] {symbol} 研判完成！生成决策: {decision.get('action')}")
            return decision

        except Exception as e:
            # 尝试 2: 降级方案 - 如果多智能体撞了配额，直接进行单兵研判
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "insufficient_quota" in str(e).lower():
                print(f"⚠️ 多智能体配额超限，正在启动单兵备用大脑 (Solo Agent)...")
                return self.solo_fallback_analyze(symbol, context_extra)

            print(f"Agent 分析失败 {symbol}: {e}")
            return None

    def solo_fallback_analyze(self, symbol, context):
        """
        单兵研判：只发一次请求，极大节省配额 (使用 DeepSeek + 中文输出)
        """
        from openai import OpenAI
        client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL
        )

        prompt = f"""
        你是一位资深的量化投资专家。请根据以下数据为股票 {symbol} 提供一份详尽的中文投研建议：
        {context}
        要求：
        1. 给出明确的操作建议 (买入/持有/卖出)。
        2. 详细阐述核心逻辑（涵盖基本面、技术面和风险点）。
        3. 必须使用中文回答。
        """
        try:
            resp = client.chat.completions.create(
                model="deepseek-chat", 
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            content = resp.choices[0].message.content
            def extract_rating(content):
                content_up = content.upper()
                if "STRONG BUY" in content_up or "强烈买入" in content: return "Strong Buy"
                if "BUY" in content_up or "买入" in content: return "Buy"
                if "STRONG SELL" in content_up or "强烈卖出" in content: return "Strong Sell"
                if "SELL" in content_up or "卖出" in content: return "Sell"
                if "OVERWEIGHT" in content_up or "增持" in content: return "Overweight"
                if "UNDERWEIGHT" in content_up or "减持" in content: return "Underweight"
                return "Hold"

            rating = extract_rating(content)

            return {
                "action": rating,
                "rationale": content,
                "debate_summary": "配额限制，已启动备用单兵大脑生成中文研判。"
            }
        except Exception as e:
            print(f"备用大脑也哑火了: {e}")
            return None


agent_bridge = AgentBridge()
