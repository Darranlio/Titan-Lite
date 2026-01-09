class ContentManager:
    """
    文案生成器：负责将结构化数据转化为人类可读的文本
    实现了 '交易员' 和 '观察者' 两种人格
    """

    def private_report(self, pair, z_score, action, news_fact):
        """
        生成私有交易指令 (面向自己)
        特点：直接、粗暴、带操作建议
        """
        return f"""### ⚡ Titan-Lite 交易指令

**标的**: {pair}
**信号**: {action} ‼️
**Z-Score**: {z_score:.2f} (已突破阈值)

------------------
**舆情速查 (AI去噪)**:
{news_fact}
------------------

**操作建议**:
1. 现价开仓，严格执行配对比例。
2. 若 Z-Score 回归至 0 附近平仓。
3. 若 Z-Score 扩大至 3.0 则止损。
"""

    def public_article(self, pair, z_score, news_fact):
        """
        生成公众号素材 (面向公众)
        特点：客观、学术、合规、无投资建议
        """
        # 计算概率：Z=2.0 对应 95% 置信度
        probability = "95%" if abs(z_score) < 3 else "99%"
        
        return f"""## 📈 市场数据观察日报

**关注对象**: {pair}
**统计现象**: 
今日模型监测显示，两者价差偏离度达到 **{z_score:.2f}** 倍标准差。
从统计学正态分布来看，该事件发生的概率小于 5%，属于历史极端区间。

**背景梳理 (AI Fact Check)**:
{news_fact}

------------------
*声明：*
*本文内容由 Titan-Lite 算法自动生成，仅用于展示统计学模型在金融数据分析中的应用。*
*文中所述不构成任何投资建议，市场有风险，独立判断最重要。*
"""