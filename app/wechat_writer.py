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
        prompt = f"""
你是一位拥有百万粉丝的财经公众号主笔，擅长将复杂的投研逻辑转化为通俗易懂、具有煽动性但又不失合规性的深度好文。

[任务]：为股票 {symbol} 撰写一篇微信公众号推文。

[素材库]：
1. 核心决策：{decision.get('action')}
2. 投资逻辑：{decision.get('rationale')}
3. 事实清单：{fact_sheet}

[排版要求]：
1. **标题**：起一个吸引眼球但不标题党的标题（如：【深度】英伟达再创历史：是泡沫终点还是AI新时代的起点？）。
2. **正文**：
   - 使用 Markdown 格式。
   - 分为：[引言]、[核心逻辑]、[数据亮点]、[风险警示] 四个板块。
   - 使用微信风格的排版：多用空行、适当使用表情符号、金句加粗。
3. **金句**：每篇推文必须包含至少一句“压舱石”级别的投资金句。

[合规护栏]：
- 严禁承诺收益（如“必涨”、“稳赚”）。
- 严禁使用过于绝对的字眼。
- 语言风格：专业、睿智、略带温度。

请开始你的创作：
"""
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
