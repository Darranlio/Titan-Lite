# === 阶段 1: 构建 (Builder) ===
FROM node:18-alpine as builder

# 设置工作目录
WORKDIR /app

# 先复制 package.json 安装依赖 (利用 Docker 缓存层)
COPY package.json ./

# === 关键修改：换成淘宝镜像源 ===
RUN npm config set registry https://registry.npmmirror.com

RUN npm install

# 复制所有文档源码
COPY . .

# 执行编译命令 (Markdown -> HTML/CSS/JS)
# 产物会生成在 .vitepress/dist 目录下
RUN npm run docs:build

# === 阶段 2: 运行 (Runner) ===
FROM nginx:alpine

# 从上一阶段复制编译好的静态文件到 Nginx 目录
COPY --from=builder /app/.vitepress/dist /usr/share/nginx/html

# 复制自定义的 Nginx 配置 (包含密码锁逻辑)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 注意：.htpasswd 密码文件将在 docker-compose 中挂载，不打入镜像以保安全
