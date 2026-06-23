import json
import os
from datetime import datetime
from config import settings

class WeChatWriter:
    """
    Titan-Alpha 自媒体主笔模块
    负责将投研结论转化为符合公众号排版规范的中文推文。
    """
    
    def __init__(self):
        self.disclaimer = (
            "\n\n---\n"
            "**免责声明**：本文内容仅供参考，不构成任何投资建议。投资有风险，入市需谨慎。 "
            "本文所引用的数据均来自公开渠道，AI生成的观点可能存在偏差，请结合自身财务状况做出独立判断。"
        )

    def generate_post(self, symbol, decision, fact_sheet):
        """生成推文草稿"""
        from skills.engine import skill_engine
        prompt = skill_engine.render_skill("wechat_post_writer", {
            "symbol": symbol, 
            "action": decision.get('action'),
            "rationale": decision.get('rationale'),
            "fact_sheet": fact_sheet
        })
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
            resp = client.chat.completions.create(
                model="deepseek-chat", 
                messages=[{"role": "system", "content": "你是一个财经公众号主笔。"},{"role": "user", "content": prompt}], 
                temperature=0.7
            )
            content = resp.choices[0].message.content.strip()
            return content + self.disclaimer
        except Exception as e:
            return f"生成推文失败: {e}"

wechat_writer = WeChatWriter()
