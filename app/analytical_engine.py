import logging
from typing import Dict, Any, List
from openai import OpenAI
from config import settings

logger = logging.getLogger("TitanAnalytical")

class AnalyticalEngine:
    """
    Titan-Lite Core Engine: Analytical Domain.
    Responsible for information distillation, translation, and Fact Sheet generation.
    """
    def __init__(self):
        self.client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)

    def translate_business_summary(self, summary_en: str) -> str:
        """
        Translates English business summary to professional Chinese.
        Moved from DataProvider to satisfy Hexagonal purity.
        """
        if not summary_en or summary_en == 'No summary available.' or summary_en == '获取失败':
            return "暂无业务简介"
            
        try:
            prompt = f"请将以下这段股票业务简介翻译为专业的金融中文。要求：准确、精炼、符合中文表达习惯。\n\n原文：\n{summary_en}"
            resp = self.client.chat.completions.create(
                model="deepseek-chat", 
                messages=[{"role": "user", "content": prompt}], 
                temperature=0.1
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return summary_en

    def generate_fact_sheet(self, ticker: str, verification_data: Dict[str, Any]) -> str:
        """
        Formalizes a Fact Sheet based on objective verification data.
        Ensures LLM reasoning is grounded in consistent data.
        """
        fact_score = verification_data.get('fact_score', '-')
        fact_check = verification_data.get('fact_check', '未核查')
        divergence = verification_data.get('divergence', '无信号')
        insider = verification_data.get('insider', '无记录')
        supply_chain = verification_data.get('supply_chain', '未分析')
        leadership = verification_data.get('leadership', '未分析')
        
        # Structure the Fact Sheet in a consistent format for the Reasoning Engine
        fact_sheet = f"""[FACT SHEET - {ticker}]
- 社交媒体真实度评分: {fact_score}
- 核心事实核查结论: {fact_check}
- 量价背离信号: {divergence}
- 高管/内部人行为: {insider}
- 上下游产业链: {supply_chain}
- 领导人性格特质: {leadership}
"""
        return fact_sheet

    def analyze_company_context(self, ticker: str) -> Dict[str, str]:
        """
        Performs qualitative analysis on the company's supply chain and leadership.
        """
        try:
            from skills.engine import skill_engine
            prompt = skill_engine.render_skill("analytical_industry_researcher", {"ticker": ticker})
            resp = self.client.chat.completions.create(
                model="deepseek-chat", 
                messages=[{"role": "user", "content": prompt}], 
                temperature=0.3
            )
            content = resp.choices[0].message.content.strip()
            
            supply_chain = "未知"
            leadership = "未知"
            for line in content.split('\n'):
                if line.startswith('产业链：'):
                    supply_chain = line.replace('产业链：', '').strip()
                elif line.startswith('领导人：'):
                    leadership = line.replace('领导人：', '').strip()
            return {"supply_chain": supply_chain, "leadership": leadership}
        except Exception as e:
            logger.error(f"Company context analysis failed for {ticker}: {e}")
            return {"supply_chain": "获取失败", "leadership": "获取失败"}

# Singleton export
analytical_engine = AnalyticalEngine()
