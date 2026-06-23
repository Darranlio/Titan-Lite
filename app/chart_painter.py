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

    def draw_sector_heatmap(self, sector_data: dict, title: str = "Sector Fund Flow Heatmap"):
        """
        绘制行业热力图 (Seaborn Heatmap) - 升级版：更高分辨率与专业布局
        :param sector_data: {'SectorName': fund_flow_value}
        """
        import pandas as pd
        import numpy as np

        if not sector_data:
            return None

        # 转换数据为 DataFrame，按值大小排序以增强可读性
        items = sorted(sector_data.items(), key=lambda x: x[1], reverse=True)

        # 布局优化：自适应行列比
        n = len(items)
        cols = 5 if n > 10 else 4 if n > 4 else n
        rows = (n + cols - 1) // cols

        matrix_data = np.zeros((rows, cols))
        labels = [["" for _ in range(cols)] for _ in range(rows)]

        for i, (name, val) in enumerate(items):
            r, c = i // cols, i % cols
            matrix_data[r, c] = val
            labels[r][c] = f"{name}\n{val:+.1f}%"

        plt.figure(figsize=(14, 2 + rows * 1.5))
        sns.heatmap(matrix_data, annot=np.array(labels), fmt="", cmap="RdYlGn", 
                    center=0, linewidths=2, linecolor='#f8f9fa',
                    cbar_kws={'label': 'Fund Flow (%)', 'orientation': 'horizontal', 'pad': 0.15})
        plt.title(title, fontsize=18, fontweight='bold', pad=20)
        plt.axis('off')

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=200, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        return buf

    def draw_valuation_scatter(self, candidates: list, title: str = "Global Markets: Valuation vs. Upside Matrix"):
        """
        绘制个股价值散点图 (PE vs Upside) - 升级版：高DPI、智能标注与色彩深度
        :param candidates: 包含 symbol, pe, upside 的列表
        """
        import pandas as pd
        df = pd.DataFrame(candidates)
        if df.empty or 'pe' not in df or 'upside' not in df:
            return None

        # 过滤极端异常值以优化坐标轴展示
        plot_df = df[(df['pe'] > 0) & (df['pe'] < 120)].copy()
        if plot_df.empty:
            return None

        plt.figure(figsize=(12, 9))
        sns.set_style("whitegrid")

        # 核心散点绘制
        scatter = plt.scatter(plot_df['pe'], plot_df['upside'] * 100, 
                             s=abs(plot_df['upside'] * 1000) + 100, 
                             c=plot_df['upside'] * 100, 
                             cmap='RdYlGn', alpha=0.7, edgecolors='white', linewidth=1)

        # 添加色彩条
        cbar = plt.colorbar(scatter)
        cbar.set_label('Target Upside (%)', fontsize=12)

        # 智能标注：优先标注潜力最高和最低的标的
        top_candidates = plot_df.sort_values(by='upside', ascending=False).head(15)
        for i, row in top_candidates.iterrows():
            plt.annotate(f"{row['symbol']}\n({row['upside']:.1%})", 
                        (row['pe'], row['upside'] * 100),
                        xytext=(8, 0), textcoords='offset points',
                        fontsize=10, fontweight='bold', alpha=0.9,
                        bbox=dict(boxstyle='round,pad=0.2', fc='yellow', alpha=0.2, ec='none'))

        plt.axhline(0, color='#e74c3c', linestyle='-', linewidth=2, alpha=0.5)
        plt.axvline(15, color='#3498db', linestyle='--', linewidth=1, alpha=0.5, label='Fair PE (15x)')

        plt.xlabel("Price-to-Earnings (PE) Ratio", fontsize=12, fontweight='bold')
        plt.ylabel("Expected Upside (%)", fontsize=12, fontweight='bold')
        plt.title(title, fontsize=18, fontweight='bold', pad=25)

        # 丰富坐标轴信息
        plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:+.0f}%'))

        # 添加战术象限说明
        plt.text(5, plot_df['upside'].max() * 100 * 0.9, "💎 高价值/低估值", color='darkgreen', fontweight='bold', alpha=0.6)
        plt.text(90, plot_df['upside'].min() * 100 * 0.9, "⚠️ 估值溢价区", color='darkred', fontweight='bold', alpha=0.6)

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight') # 300 DPI 极高清晰度
        buf.seek(0)
        plt.close()
        return buf