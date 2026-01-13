# 🧠 核心策略算法 (Strategy Engine)

::: info 文档元数据
- **策略名称**: Dynamic Pair Trading with Kalman Filter
- **适应周期**: 1H (小时线) / 1D (日线)
- **状态**: 🟡 开发中 (In Development)
- **最后更新**: 2026-01-12
:::

## 1. 策略概述 (Overview)

本系统采用 **统计套利 (Statistical Arbitrage)** 中的配对交易策略。

传统的配对交易通常使用 **最小二乘法 (OLS)** 也就是简单的线性回归 ($y = \beta x + \alpha$) 来计算两只股票的价差。但 OLS 有一个致命弱点：**它假设 $\beta$ (对冲比率) 是恒定不变的**。

然而在真实市场中，两家公司的基本面关系是动态变化的。因此，Titan-Lite 引入 **卡尔曼滤波 (Kalman Filter)** 算法。它不仅仅利用过去的数据，而是像卫星导航一样，根据每一个新的观测值，**在线更新 (Online Update)** 当前的对冲比率。

> **核心优势**: 不需要滑动窗口 (Rolling Window)，天然没有“窗口期滞后”的问题，对市场结构突变反应极快。

---

## 2. 数学模型推导 (Mathematical Model)

我们将两只股票 $Y$ (标的资产) 和 $X$ (对冲资产) 的价格关系建模为线性状态空间模型。

### 2.1 状态方程 (State Equation)
我们假设两只股票之间的对冲比率 $\beta$ (即斜率) 不是常数，而是一个遵循**随机游走 (Random Walk)** 的变量。

$$
\beta_t = \beta_{t-1} + \omega_t, \quad \omega_t \sim \mathcal{N}(0, Q)
$$

* $\beta_t$: $t$ 时刻的隐藏状态（真实的对冲比率）。
* $\omega_t$: 过程噪声 (Process Noise)，代表对冲比率随时间变化的剧烈程度。
* $Q$: 过程噪声的协方差（超参数）。

### 2.2 观测方程 (Observation Equation)
我们观测到的市场价格 $Y_t$ 是由 $X_t$ 和当前的 $\beta_t$ 决定的，并带有一定的测量误差。

$$
Y_t = \beta_t \cdot X_t + \alpha_t + v_t, \quad v_t \sim \mathcal{N}(0, R)
$$

为了简化计算，我们通常将截距 $\alpha$ 也并入状态向量中。此时状态向量 $\theta_t = [\beta_t, \alpha_t]^T$。

* $Y_t$: 股票 A 的价格。
* $X_t$: 股票 B 的价格（或一篮子股票）。
* $v_t$: 测量噪声 (Measurement Noise)。

---

## 3. 算法实现逻辑 (Implementation)

在 2C2G 的服务器上，我们不能每次都读取几年的历史数据进行全量计算。我们需要一个**增量式 (Incremental)** 的过滤器。

### 3.1 Python 伪代码 (Online Kalman Filter)

以下是用于生产环境的精简版代码，基于 `numpy` 实现，去除了对重型库的依赖。

```python
import numpy as np

class OnlineKalmanFilter:
    def __init__(self, delta=1e-4, R=1e-3):
        """
        初始化卡尔曼滤波器
        :param delta: 过程噪声系数 (控制 beta 变化的灵活性)
        :param R: 测量噪声方差
        """
        # 1. 状态均值 (State Mean): [beta, alpha]
        self.state_mean = np.zeros(2)
        
        # 2. 状态协方差 (State Covariance): P
        self.P = np.zeros((2, 2))
        
        # 3. 过程噪声协方差 (Process Noise Covariance): Q
        self.Q = delta / (1 - delta) * np.eye(2)
        
        # 4. 测量噪声方差 (Measurement Noise Variance): R
        self.R = R

    def update(self, price_y, price_x):
        """
        输入最新的价格，更新对冲比率，并返回当前的价差信号
        :param price_y: 标的资产价格 (Stock A)
        :param price_x: 对冲资产价格 (Stock B)
        """
        # 构建观测矩阵 H = [price_x, 1]
        H = np.array([price_x, 1.0])
        
        # --- 预测步骤 (Predict) ---
        # 假设随机游走，先验估计等于后验估计
        # P_predict = P_prev + Q
        self.P = self.P + self.Q
        
        # --- 更新步骤 (Update) ---
        # 1. 计算观测误差 (Innovation / Residual)
        y_hat = H @ self.state_mean
        error = price_y - y_hat
        
        # 2. 计算观测误差的方差 (Variance of Prediction Error)
        S = H @ self.P @ H.T + self.R
        
        # 3. 计算卡尔曼增益 (Kalman Gain)
        K = self.P @ H.T / S
        
        # 4. 更新状态估计 (Update State Mean)
        # beta_new = beta_old + K * error
        self.state_mean = self.state_mean + K * error
        
        # 5. 更新状态协方差 (Update State Covariance)
        # P_new = (I - K * H) * P_old
        self.P = (np.eye(2) - np.outer(K, H)) @ self.P
        
        # --- 结果导出 ---
        beta = self.state_mean[0]
        alpha = self.state_mean[1]
        
        # 返回：当前误差(Spread)，误差标准差(用于计算Z-Score)
        return error, np.sqrt(S), beta
```

## 4. 信号生成与交易规则 (Trading Rules)

有了卡尔曼滤波器输出的实时误差（Spread）和方差，我们可以计算标准分（Z-Score）。

### 4.1 Z-Score 计算
不同于均线策略需要回看 N 天计算标准差，卡尔曼滤波器直接输出了预测误差的方差 $S_t$。

$$
Z_t = \frac{e_t}{\sqrt{S_t}} = \frac{Y_t - (\beta_t X_t + \alpha_t)}{\sqrt{S_t}}
$$

### 4.2 交易阈值 (Thresholds)

| 信号类型 | 阈值条件 | 操作指令 | 逻辑解释 |
| :--- | :--- | :--- | :--- |
| **Open Long** | $Z < -2.0$ | 买入 Y，卖出 X | 价差过低，预期回归 |
| **Open Short** | $Z > +2.0$ | 卖出 Y，买入 X | 价差过高，预期回归 |
| **Close Position** | $|Z| < 0.5$ | 平掉所有仓位 | 均值回归完成，落袋为安 |
| **Stop Loss** | $|Z| > 3.5$ | **强制止损** | 模型失效（脱锚），防止黑天鹅 |

---

## 5. 风险控制 (Risk Management)

### 5.1 协整性校验 (Cointegration Check)
并不是所有股票对都能做配对交易。系统会在每日收盘后运行 **Engle-Granger Two-Step Method**。
* 若 `p-value > 0.05`，说明两只股票关系破裂，次日**禁止开新仓**。

### 5.2 宏观熔断
当市场处于极端恐慌状态时（如 2015 年股灾或 2024 年微盘股崩盘），统计规律会失效。

* **监控指标**: 沪深 300 指数波动率。
* **动作**: 若波动率飙升，自动降低杠杆或停止运行。

---

## 6. 下一步开发计划 (Roadmap)

- [ ] 实现 `DataAdaptor` 对接实盘 Tick 数据流。
- [ ] 编写回测脚本，验证该逻辑在 2023-2024 年的表现。
- [ ] 参数优化：寻找最佳的 $Q$ (过程噪声) 和 $R$ (测量噪声) 值。