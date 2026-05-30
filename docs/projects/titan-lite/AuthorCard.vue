<template>
  <div class="author-card-wrapper">
    <!-- Explicitly styled card to ensure visibility -->
    <div class="author-card">
      <!-- High-contrast Rotating Border -->
      <div class="premium-avatar-box">
        <div class="rotating-border"></div>
        <div class="avatar-inner">
          <img src="/avatar.png" class="author-avatar" alt="D" />
          <div class="status-indicator">
            <div class="pulse-ring"></div>
          </div>
        </div>
      </div>
      
      <div class="author-content">
        <div class="header-row">
          <h2 class="author-name">Darranlio</h2>
          <span class="role-badge">算法工程师</span>
        </div>
        
        <p class="author-bio">
          美团 UAV 感知算法工程师 <span class="dot">·</span> 量化投资探索者
        </p>
        
        <div class="social-actions">
          <button @click="copyEmail" class="action-btn email-btn" :class="{ 'copied': emailCopied }">
            <span class="btn-text">{{ emailCopied ? '1059390428@qq.com' : '📧 Email' }}</span>
          </button>
          
          <a href="https://github.com/Darranlio" target="_blank" class="action-btn github-btn">
            🐙 GitHub
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emailCopied = ref(false)
const copyEmail = () => {
  const email = '1059390428@qq.com'
  navigator.clipboard.writeText(email).then(() => {
    emailCopied.value = true
    setTimeout(() => { emailCopied.value = false }, 2000)
  })
}
</script>

<style scoped>
/* 使用绝对明确的颜色值，不依赖主题变量 */
.author-card-wrapper {
  margin: 1.5rem 0;
  display: flex;
  justify-content: center;
  width: 100%;
}

.author-card {
  width: 100%;
  max-width: 500px;
  background: #1a1a1a; /* 强制深灰背景 */
  border: 2px solid #00a3ff; /* 明确的蓝色边框 */
  border-radius: 20px;
  padding: 1.2rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 1.5rem;
  position: relative;
  box-shadow: 0 0 20px rgba(0, 163, 255, 0.3);
  animation: glow-breathe 3s ease-in-out infinite;
}

@keyframes glow-breathe {
  0%, 100% { box-shadow: 0 0 15px rgba(0, 163, 255, 0.2); border-color: #00a3ff; }
  50% { box-shadow: 0 0 30px rgba(189, 52, 254, 0.4); border-color: #bd34fe; }
}

.premium-avatar-box {
  position: relative;
  width: 80px;
  height: 80px;
  flex-shrink: 0;
}

.rotating-border {
  position: absolute;
  top: -3px; left: -3px; right: -3px; bottom: -3px;
  background: conic-gradient(from 0deg, #00a3ff, #bd34fe, #00a3ff);
  border-radius: 18px;
  animation: rotate 2s linear infinite;
  z-index: 0;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.avatar-inner {
  position: relative;
  width: 100%;
  height: 100%;
  background: #000;
  border-radius: 15px;
  padding: 2px;
  z-index: 1;
}

.author-avatar {
  width: 100%;
  height: 100%;
  border-radius: 13px;
  object-fit: cover;
}

.status-indicator {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 12px;
  height: 12px;
  background: #238636;
  border: 2px solid #000;
  border-radius: 50%;
  z-index: 2;
}

.pulse-ring {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  border: 2px solid #238636;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  100% { transform: scale(3); opacity: 0; }
}

.author-content { color: #fff; }
.author-name { font-size: 1.3rem; margin: 0; font-weight: 800; color: #fff; }
.role-badge { font-size: 0.7rem; background: #00a3ff22; color: #00a3ff; padding: 2px 8px; border-radius: 5px; margin-left: 10px; }
.author-bio { font-size: 0.85rem; color: #ccc; margin: 8px 0 15px 0; }
.dot { color: #00a3ff; margin: 0 5px; }

.social-actions { display: flex; gap: 10px; }
.action-btn { 
  padding: 6px 12px; 
  border-radius: 8px; 
  font-size: 0.8rem; 
  font-weight: 700; 
  cursor: pointer; 
  border: 1px solid #333;
  background: #222;
  color: #fff;
  text-decoration: none;
}
.email-btn { background: #00a3ff; border: none; min-width: 100px; }
.email-btn.copied { background: #238636; }

@media (max-width: 500px) {
  .author-card { flex-direction: column; text-align: center; }
  .social-actions { justify-content: center; }
}
</style>
