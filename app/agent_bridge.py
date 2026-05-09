import os
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from config import settings

class AgentBridge:
    """
    Titan-Lite 与 TradingAgents 的桥接层
    """
    def __init__(self):
        # 将 Titan-Lite 的配置映射到 TradingAgents 环境变量
        if settings.LLM_PROVIDER == "google":
            os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
        else:
            os.environ["OPENAI_API_KEY"] = settings.LLM_API_KEY or "dummy-key-for-init"
            os.environ["OPENAI_BASE_URL"] = settings.LLM_BASE_URL
        
        # 初始化配置
        self.config = DEFAULT_CONFIG.copy()
        self.config["llm_provider"] = settings.LLM_PROVIDER
        
        # 如果是 Google，指定模型名称
        if settings.LLM_PROVIDER == "google":
            self.config["deep_think_llm"] = "gemini-2.0-flash"
            self.config["quick_think_llm"] = "gemini-2.0-flash"
        
        self.config["checkpoint_enabled"] = False 
        self.config["max_debate_rounds"] = 1 # 针对 2G 内存和速度优化，设为 1 轮
        
        # 调试模式
        self.agent_graph = TradingAgentsGraph(debug=False, config=self.config)


    def analyze_ticker(self, symbol, date=None, context_extra=""):
        """
        调用多智能体进行深度分析
        :param symbol: 股票代码
        :param date: 分析日期 (None 为今天)
        :param context_extra: 额外的上下文（如事实核查报告）
        """
        if date is None:
            from datetime import datetime
            date = datetime.now().strftime("%Y-%m-%d")
            
        print(f">>> [Agent] 启动多智能体深度研判: {symbol} @ {date}")
        
        # 将鉴伪报告注入到 TradingAgents 的全局 context 中
        if context_extra:
            print(f"--- 注入鉴伪报告 ---")
            # 注意：这里我们可以通过环境变量或临时修改 config 的方式注入
            # 更优雅的方式是修改 TradingAgents 的 prompt 模板，这里先通过注入Rationale占位
            pass

        try:
            # 调用 TradingAgents 核心逻辑
            # 返回: (final_state, decision_dict)
            _, decision = self.agent_graph.propagate(symbol, date)
            
            # 如果有鉴伪报告，将其合并到 decision 中供 Web 显示
            if context_extra:
                decision['rationale'] = f"{context_extra}\n{decision.get('rationale', '')}"
                
            return decision
        except Exception as e:
            print(f"Agent 分析失败 {symbol}: {e}")
            return None

agent_bridge = AgentBridge()
