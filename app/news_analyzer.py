from openai import OpenAI
from data_provider import data_provider
from config import settings

class NewsAnalyzer:
    def __init__(self):
        # 使用配置
        self.client = OpenAI(
            api_key=settings.LLM_API_KEY, 
            base_url=settings.LLM_BASE_URL
        )

    def analyze(self, pair_name, code_a, code_b):
        # 调用适配器获取原始新闻
        news_a = data_provider.get_news_summary(code_a)
        news_b = data_provider.get_news_summary(code_b)
        
        prompt = f"""
        你是一个客观的金融分析师。
        股票A: {news_a}
        股票B: {news_b}
        请用【一句话】概括这两只股票近期的客观利好或利空事实。
        严禁预测。如果没有大事，回答“无重大舆情”。
        """
        try:
            resp = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            return resp.choices[0].message.content
        except:
            return "AI分析不可用"