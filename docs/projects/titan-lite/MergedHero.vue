<template>
  <div class="merged-hero-container">
    <!-- Left: Branding & Action -->
    <div class="hero-left">
      <div class="brand-horizontal-wrapper">
        <!-- Big Logo on the absolute left -->
        <img src="/logo.svg" class="hero-logo-large" alt="Logo" />
        
        <!-- All text and buttons grouped to align together -->
        <div class="brand-text-content">
          <h1 class="hero-title">
            <span class="clip">Digital Asset Lab</span>
          </h1>
          <p class="hero-tagline">Professional Quant & AI Solutions</p>
          <p class="hero-sub">基于 DeepSeek 认知博弈架构的个人投资决策终端</p>
          
          <div class="hero-actions">
            <a href="/projects/titan-lite/portfolio" class="btn-brand">🏦 我的基金中心</a>
            <a href="/projects/titan-lite/reports/index" class="btn-alt">📑 研报档案馆</a>
          </div>
        </div>
      </div>
    </div>

    <!-- Right: Author Card -->
    <div class="hero-right">
      <AuthorCard />
    </div>
  </div>
</template>

<script setup>
import AuthorCard from './AuthorCard.vue'
</script>

<style scoped>
.merged-hero-container {
  display: flex;
  align-items: center;
  justify-content: space-around;
  gap: 2rem;
  padding: 1.5rem 0 1rem;
  margin: -1.5rem auto 0.5rem;
  max-width: 1300px; /* 稍微再拓宽一点 */
}

.hero-left {
  flex: 0 1 auto;
}

/* 核心：横向品牌容器 */
.brand-horizontal-wrapper {
  display: flex;
  align-items: flex-start; /* 顶部对齐，让文字从第一行对齐 */
  gap: 2.5rem;             /* Logo 与文字间的间距 */
  text-align: left;
}

.hero-logo-large {
  width: 120px;            /* 进一步放大 Logo */
  height: 120px;
  margin-top: 0.5rem;      /* 微调，对齐标题第一行 */
  filter: drop-shadow(0 0 35px rgba(0, 163, 255, 0.4));
  transition: transform 0.3s ease;
  flex-shrink: 0;
}

.hero-logo-large:hover {
  transform: rotate(-10deg) scale(1.05);
}

.brand-text-content {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}

.hero-title {
  font-size: 3.8rem;
  line-height: 1;
  font-weight: 800;
  margin: 0;
}

.clip {
  background: linear-gradient(120deg, #41d1ff 30%, #bd34fe);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-tagline {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--vp-c-text-1);
  margin-top: 0.6rem;
}

.hero-sub {
  font-size: 1.1rem;
  color: var(--vp-c-text-2);
  margin-top: 1rem;
  max-width: 800px;
  line-height: 1.6;
}

.hero-actions {
  display: flex;
  gap: 1.2rem;
  margin-top: 2.2rem;
}

.hero-actions a {
  padding: 0.8rem 1.6rem;
  border-radius: 12px;
  font-weight: 700;
  text-decoration: none !important;
  font-size: 0.95rem;
  transition: all 0.2s;
  display: inline-block;
}

.btn-brand {
  background: var(--vp-c-brand);
  color: white !important;
}
.btn-brand:hover {
  filter: brightness(1.1);
  transform: translateY(-2px);
}

.btn-alt {
  background: var(--vp-c-bg-alt);
  border: 1px solid var(--vp-c-divider);
  color: var(--vp-c-text-1) !important;
}
.btn-alt:hover {
  background: var(--vp-c-bg-soft);
  transform: translateY(-2px);
}

.hero-right {
  flex-shrink: 0;
  max-width: 500px;
}

/* 适配：当屏幕变窄时，Logo 居中置顶 */
@media (max-width: 1024px) {
  .merged-hero-container {
    flex-direction: column;
    padding: 2rem 0;
  }
  .brand-horizontal-wrapper {
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 1.5rem;
  }
  .hero-logo-large {
    margin-top: 0;
  }
  .hero-sub {
    margin: 1rem auto;
  }
  .hero-actions {
    justify-content: center;
  }
}
</style>
