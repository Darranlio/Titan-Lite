import matplotlib.pyplot as plt
import seaborn as sns
import io
import matplotlib.dates as mdates

class ChartPainter:
    """
    绘图引擎：负责将枯燥的数据转化为可视化的图表
    支持 '实战模式' 和 '展示模式' 两种风格
    """
    def __init__(self):
        # 尝试设置中文字体，防止中文乱码
        # SimHei 是黑体，Arial 是保底英文
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']
        # 解决负号显示为方块的问题
        plt.rcParams['axes.unicode_minus'] = False

    def draw(self, pair_name, df, z_score, mode="private"):
        """
        绘制双子图：价格走势 + Z-Score 偏离度
        
        :param pair_name: 股票对名称 (如 "茅台 vs 五粮液")
        :param df: 包含 'A' 和 'B' 列的价格 DataFrame
        :param z_score: Z-Score 的 Series
        :param mode: 'private' (交易用) 或 'public' (公众号用)
        :return: 图片的二进制数据 (BytesIO对象)
        """
        
        # --- 1. 风格配置 ---
        if mode == "public":
            # 公版：使用 Seaborn 的白色网格风格，看起来像学术论文
            sns.set_theme(style="whitegrid")
            # 配色：深蓝(A) & 深红(B) & 蓝色(Z)
            colors = ['#2c3e50', '#e74c3c', '#3498db']
        else:
            # 私版：使用暗色网格，适合夜间看盘，高对比度
            sns.set_theme(style="darkgrid")
            # 配色：亮黄(A) & 青色(B) & 洋红(Z)
            colors = ['yellow', 'cyan', 'magenta']

        # 创建画布：10英寸宽，8英寸高，包含两个子图(ax1, ax2)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        
        # --- 2. 子图一：价格归一化对比 ---
        # 归一化逻辑：当前价 / 第一天价。这样起点都是 1.0，方便对比涨幅差异
        norm_A = df['A'] / df['A'].iloc[0]
        norm_B = df['B'] / df['B'].iloc[0]
        
        ax1.plot(df.index, norm_A, label=pair_name.split(' vs ')[0], color=colors[0], linewidth=1.5)
        ax1.plot(df.index, norm_B, label=pair_name.split(' vs ')[1], color=colors[1], linewidth=1.5)
        ax1.legend(loc='upper left')
        ax1.set_title(f"{pair_name} Price Ratio (Normalized)", fontweight='bold')
        ax1.set_ylabel("Relative Value")

        # --- 3. 子图二：Z-Score 统计偏离 ---
        ax2.plot(df.index, z_score, color=colors[2], label='Spread Z-Score', linewidth=1.2)
        
        # --- 4. 模式差异化绘制 ---
        if mode == "private":
            # === 私版独有 ===
            # 画出 ±2.0 的开仓阈值线 (虚线)
            ax2.axhline(2.0, color='red', linestyle='--', alpha=0.8, label='Short Threshold')
            ax2.axhline(-2.0, color='green', linestyle='--', alpha=0.8, label='Long Threshold')
            # 标题醒目，提示交易
            ax2.set_title("TRADING SIGNAL (Action Required)", color='red', fontweight='bold')
            # 填充颜色，强调异常区域
            ax2.fill_between(df.index, z_score, 2.0, where=(z_score>=2), color='red', alpha=0.3)
            ax2.fill_between(df.index, z_score, -2.0, where=(z_score<=-2), color='green', alpha=0.3)
        else:
            # === 公版独有 ===
            # 画出 ±2.0 的灰色区间，代表"正常波动范围"
            ax2.axhspan(-2, 2, color='gray', alpha=0.1, label='95% Confidence Interval')
            ax2.set_title("Statistical Deviation Analysis", fontsize=12)
            # 添加水印：防止盗图，建立品牌
            fig.text(0.5, 0.5, 'Titan-Lite Data Lab', fontsize=40, 
                     color='gray', ha='center', va='center', alpha=0.1, rotation=30)

        # 设置图例
        ax2.legend(loc='upper left')
        ax2.set_ylabel("Standard Deviations")
        
        # 格式化日期轴 (只显示 年-月)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        
        # 调整布局，防止文字重叠
        plt.tight_layout()
        
        # --- 5. 输出图片流 ---
        buf = io.BytesIO()
        # 保存为 PNG 格式，dpi=100 保证清晰度且体积不大
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0) # 指针回到开头
        plt.close(fig) # 关闭画布释放内存
        
        return buf