FROM python:3.12-slim

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# 换成阿里云镜像源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

# 安装基础系统依赖
RUN apt-get update && apt-get install -y \
    fonts-wqy-microhei \
    git \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# === 优化步骤：先安装所有依赖 (利用缓存) ===
COPY requirements.txt .
COPY trading_agents_src/pyproject.toml ./trading_agents_src/
# 创建占位文件以满足 pip 安装 pyproject.toml 时的基础要求
RUN touch ./trading_agents_src/README.md && mkdir -p ./trading_agents_src/tradingagents

# 使用清华源加速下载，并合并安装主项目与子模块依赖
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
    -r requirements.txt \
    ./trading_agents_src

# === 拷贝代码 ===
COPY . .

# 以可编辑模式重新安装子模块 (此时依赖已全部在缓存中，瞬间完成)
RUN pip install -e ./trading_agents_src -i https://pypi.tuna.tsinghua.edu.cn/simple

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
