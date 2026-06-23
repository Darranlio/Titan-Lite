<template>
  <div class="fluid-hero-container" @mousemove="handleMouseMove">
    <!-- Ambient Background Glows -->
    <div class="ambient-glow g1" :style="glow1Style"></div>
    <div class="ambient-glow g2" :style="glow2Style"></div>

    <div class="hero-content">
      <!-- Left: Massive Branding -->
      <div class="brand-wing">
        <div class="logo-area">
          <img src="/logo.svg" class="floating-logo" alt="Logo" />
          <div class="logo-shadow"></div>
        </div>
        <div class="text-area">
          <h1 class="main-title">Digital Asset Lab</h1>
          <p class="tagline">Apex AI & Quant Execution Terminal</p>
          <div class="desc-box">
            <p>您的私人华尔街团队。融合顶尖 AI 算力与机构级量化模型，全天候无情捕捉市场暴利信号，助您实现交易维度的降维打击。</p>
          </div>
          <div class="hero-actions">
            <a href="/projects/titan-lite/portfolio" class="btn-primary">进入基金中心</a>
            <a href="/projects/titan-lite/reports/index" class="btn-secondary">档案馆</a>
          </div>
        </div>
      </div>

      <!-- Right: Minimalist Identity Badge -->
      <div class="author-wing">
        <div class="profile-badge">
          <div class="avatar-box">
            <img src="/avatar.png" class="author-avatar" alt="Author" />
            <div class="status-ring">
              <div class="pulse"></div>
            </div>
          </div>
          <div class="author-info">
            <span class="name">Darranlio</span>
            <span class="role">美团无人机</span>
            <div class="bio-short">算法工程师</div>
            <div class="mini-links">
              <button @click="copyEmail" :class="{ 'active': emailCopied }">
                {{ emailCopied ? '1059390428@qq.com' : '📧 Email' }}
              </button>
              <a href="https://github.com/Darranlio" target="_blank">🐙 GitHub</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const emailCopied = ref(false)
const mouseX = ref(0)
const mouseY = ref(0)

const copyEmail = () => {
  const email = '1059390428@qq.com'
  navigator.clipboard.writeText(email)
  emailCopied.value = true
  setTimeout(() => { emailCopied.value = false }, 3000)
}

const handleMouseMove = (e) => {
  mouseX.value = e.clientX
  mouseY.value = e.clientY
}

const glow1Style = computed(() => ({
  transform: `translate(${mouseX.value * 0.02}px, ${mouseY.value * 0.02}px)`
}))
const glow2Style = computed(() => ({
  transform: `translate(${mouseX.value * -0.03}px, ${mouseY.value * -0.03}px)`
}))
</script>

<style scoped>
.fluid-hero-container {
  position: relative;
  width: 100%;
  min-height: 400px;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 3rem 0;
  overflow: hidden;
  margin-top: -1rem;
}

/* Ambient Visuals */
.ambient-glow {
  position: absolute;
  width: 500px;
  height: 500px;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.12;
  pointer-events: none;
  z-index: 0;
}
.g1 { background: var(--vp-c-brand); top: -10%; left: 10%; }
.g2 { background: #bd34fe; bottom: -10%; right: 10%; }

.hero-content {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1250px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 4rem;
  padding: 0 2rem;
}

/* Branding Side */
.brand-wing {
  display: flex;
  align-items: center;
  gap: 2.5rem;
}

.logo-area {
  position: relative;
  overflow: hidden; /* 关键：确保流光只在 Logo 范围内 */
  border-radius: 30px; /* 匹配 Logo 的大致形状 */
  padding: 5px;
}

.floating-logo {
  width: 160px; /* 从 130 放大到 160 */
  height: 160px;
  filter: drop-shadow(0 0 50px rgba(0, 163, 255, 0.5));
  animation: float 5s ease-in-out infinite;
  position: relative;
  z-index: 2;
}

/* 增加流光扫过效果 */
.logo-area::after {
  content: '';
  position: absolute;
  top: 0; left: -100%;
  width: 50%;
  height: 100%;
  background: linear-gradient(
    to right, 
    transparent, 
    rgba(255, 255, 255, 0.3), 
    transparent
  );
  transform: skewX(-25deg);
  animation: shimmer 4s infinite;
  z-index: 3;
}

@keyframes shimmer {
  0% { left: -100%; opacity: 0; }
  30% { opacity: 1; }
  60% { left: 200%; opacity: 0; }
  100% { left: 200%; opacity: 0; }
}

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(5deg); }
}

.main-title {
  font-size: 3.8rem; /* 稍微再大一点点 */
  font-weight: 900;
  margin: 0;
  line-height: 1.2; /* 增加行高，防止 g 等字母底部被截断 */
  padding-bottom: 0.5rem; /* 增加底部留白 */
  background: linear-gradient(
    120deg, 
    var(--vp-c-text-1) 0%, 
    var(--vp-c-brand) 50%, 
    var(--vp-c-text-1) 100%
  );
  background-size: 200% auto;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: fluid-text 8s linear infinite;
}

@keyframes fluid-text {
  to { background-position: 200% center; }
}

.tagline {
  font-size: 1.4rem;
  font-weight: 600;
  color: var(--vp-c-text-2);
  margin-top: 0.5rem;
}

.desc-box {
  margin: 1.2rem 0 2rem;
  font-size: 1rem;
  color: var(--vp-c-text-3);
  max-width: 450px;
}

.hero-actions {
  display: flex;
  gap: 1rem;
}

.btn-primary {
  padding: 0.7rem 1.8rem;
  background: var(--vp-c-brand);
  color: white !important;
  border-radius: 12px;
  font-weight: 800;
  text-decoration: none !important;
  box-shadow: 0 8px 20px rgba(0, 163, 255, 0.2);
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.btn-primary:hover {
  transform: translateY(-4px) scale(1.05);
  box-shadow: 0 15px 30px rgba(0, 163, 255, 0.4);
  filter: brightness(1.1);
}

.btn-secondary {
  padding: 0.7rem 1.8rem;
  background: var(--vp-c-bg-alt);
  border: 1px solid var(--vp-c-divider);
  color: var(--vp-c-text-1) !important;
  border-radius: 12px;
  font-weight: 800;
  text-decoration: none !important;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: var(--vp-c-bg-soft);
  border-color: var(--vp-c-brand);
  transform: translateY(-4px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

/* Author Badge */
.profile-badge {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1.2rem 1.5rem;
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(8px);
  border: 1px solid var(--vp-c-divider);
  border-radius: 20px;
  transition: all 0.5s cubic-bezier(0.165, 0.84, 0.44, 1);
  position: relative;
}

.profile-badge:hover {
  transform: translateY(-3px);
  border-color: var(--vp-c-brand-soft);
  background: rgba(255, 255, 255, 0.04);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.avatar-box {
  position: relative;
  width: 74px;
  height: 74px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 18px;
  background: var(--vp-c-bg);
  padding: 2px;
  overflow: hidden; /* 关键：裁剪掉外部的方形边缘 */
}

/* 真正的流光：五彩斑斓的液态流动 */
.avatar-box::before {
  content: '';
  position: absolute;
  width: 160%;
  height: 160%;
  background: conic-gradient(
    from 0deg,
    transparent 0%,
    transparent 30%,
    #00a3ff 40%, /* 科技蓝 */
    #bd34fe 50%, /* 极客紫 */
    #ff3e00 60%, /* 能量橙 */
    transparent 70%,
    transparent 100%
  );
  animation: rotate-liquid 3s linear infinite;
}

@keyframes rotate-liquid {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 内部遮罩，确保只有 1px 的边框在流水 */
.author-avatar {
  width: 70px;
  height: 70px;
  border-radius: 16px;
  object-fit: cover;
  position: relative;
  z-index: 1;
  background: var(--vp-c-bg);
}

.status-ring {
  position: absolute;
  bottom: -1px;
  right: -1px;
  width: 12px;
  height: 12px;
  background: #238636;
  border: 2px solid var(--vp-c-bg);
  border-radius: 50%;
  z-index: 2;
}

.status-ring .pulse {
  position: absolute;
  top: -1px; left: -1px; width: 12px; height: 12px;
  border: 1.5px solid #238636;
  border-radius: 50%;
  animation: pulse-ring 3s cubic-bezier(0.24, 0, 0.38, 1) infinite;
}

@keyframes pulse-ring {
  0% { transform: scale(1); opacity: 0; }
  50% { opacity: 0.4; }
  100% { transform: scale(2.2); opacity: 0; }
}

.author-info {
  display: flex;
  flex-direction: column;
}

.name {
  font-size: 1.2rem;
  font-weight: 800;
  color: var(--vp-c-text-1);
}

.role {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--vp-c-brand);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.bio-short {
  font-size: 0.8rem;
  color: var(--vp-c-text-3);
  margin: 0.4rem 0 0.8rem;
}

.mini-links {
  display: flex;
  gap: 0.8rem;
}

.mini-links a, .mini-links button {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--vp-c-text-2);
  text-decoration: none;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}

.mini-links button.active { color: #238636; }

@media (max-width: 1024px) {
  .hero-content {
    flex-direction: column;
    text-align: center;
    gap: 3rem;
  }
  .brand-wing {
    flex-direction: column;
    gap: 1.5rem;
  }
  .hero-actions { justify-content: center; }
}
</style>
