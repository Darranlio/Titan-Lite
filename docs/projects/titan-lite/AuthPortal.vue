<script setup>
import { ref, onMounted } from 'vue'

const isLogin = ref(true)
const username = ref('')
const password = ref('')
const email = ref('')
const code = ref('')
const message = ref('')
const error = ref('')
const loading = ref(false)
const countdown = ref(0)

const API_BASE = typeof window !== 'undefined' 
  ? `${window.location.protocol}//${window.location.hostname}:8000` 
  : 'http://localhost:8000'

// Use reactive refs that initialize on mount to avoid SSR hydration issues
const token = ref(null)
const user = ref(null)

onMounted(() => {
  token.value = localStorage.getItem('titan_token')
  user.value = JSON.parse(localStorage.getItem('titan_user') || 'null')
})

const sendCode = async () => {
  if (!email.value) {
    error.value = 'Please enter an email'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const res = await fetch(`${API_BASE}/auth/send-code?email=${encodeURIComponent(email.value)}`, { method: 'POST' })
    if (res.ok) {
      message.value = '验证码已发送，请查看后台控制台日志'
      countdown.value = 60
      const timer = setInterval(() => {
        countdown.value--
        if (countdown.value <= 0) clearInterval(timer)
      }, 1000)
    } else {
      const data = await res.json()
      error.value = data.detail || '发送失败'
    }
  } catch (e) {
    error.value = '网络错误: 无法连接至后端'
  } finally {
    loading.value = false
  }
}

const handleAuth = async () => {
  if (!username.value || !password.value) {
    error.value = 'Username and password are required'
    return
  }
  
  loading.value = true
  error.value = ''
  message.value = ''
  
  try {
    if (isLogin.value) {
      // Professional Login Flow
      const formData = new FormData()
      formData.append('username', username.value)
      formData.append('password', password.value)
      
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (res.ok) {
        token.value = data.access_token
        localStorage.setItem('titan_token', data.access_token)
        const userInfo = { username: username.value }
        user.value = userInfo
        localStorage.setItem('titan_user', JSON.stringify(userInfo))
        window.location.reload()
      } else {
        error.value = data.detail || '登录失败: 用户名或密码错误'
      }
    } else {
      // Register Flow
      if (!email.value || !code.value) {
        error.value = 'Email and verification code are required'
        loading.value = false
        return
      }
      
      const res = await fetch(`${API_BASE}/auth/register?username=${encodeURIComponent(username.value)}&password=${encodeURIComponent(password.value)}&email=${encodeURIComponent(email.value)}&code=${encodeURIComponent(code.value)}`, {
        method: 'POST'
      })
      if (res.ok) {
        message.value = '注册成功！正在切换至登录...'
        setTimeout(() => {
            isLogin.value = true
            message.value = ''
        }, 1500)
      } else {
        const data = await res.json()
        error.value = data.detail || '注册失败'
      }
    }
  } catch (e) {
    error.value = '通信异常: 请检查后端服务'
  } finally {
    loading.value = false
  }
}

const logout = () => {
  localStorage.removeItem('titan_token')
  localStorage.removeItem('titan_user')
  token.value = null
  user.value = null
  window.location.reload()
}
</script>

<template>
  <div class="auth-portal">
    <!-- Unauthenticated State -->
    <div v-if="!token" class="auth-card">
      <div class="auth-header">
        <div class="logo-wrapper">
           <img src="/logo.svg" class="mini-logo" />
           <div class="status-dot offline"></div>
        </div>
        <h2>{{ isLogin ? 'Researcher Login' : 'System Registration' }}</h2>
        <p class="subtitle">{{ isLogin ? 'Access your private terminal' : 'Join the quant research team' }}</p>
      </div>

      <div class="auth-body">
        <!-- Common Fields -->
        <div class="input-group">
          <label>Username / ID</label>
          <input v-model="username" placeholder="e.g. quant_master" @keyup.enter="handleAuth" />
        </div>

        <!-- Registration Only Fields -->
        <div v-if="!isLogin" class="input-group slide-in">
          <label>Email Address</label>
          <div class="email-input">
            <input v-model="email" placeholder="researcher@titan.com" />
            <button @click="sendCode" :disabled="loading || countdown > 0" class="code-btn">
              {{ countdown > 0 ? `${countdown}s` : 'Verify' }}
            </button>
          </div>
        </div>

        <div v-if="!isLogin" class="input-group slide-in">
          <label>Code</label>
          <input v-model="code" placeholder="6-digit code" maxlength="6" />
        </div>

        <div class="input-group">
          <label>Secure Password</label>
          <input v-model="password" type="password" placeholder="••••••••" @keyup.enter="handleAuth" />
        </div>

        <!-- Feedback Messages -->
        <div v-if="error" class="error-msg anim-shake">{{ error }}</div>
        <div v-if="message" class="success-msg">{{ message }}</div>

        <!-- THE MAIN ACTION BUTTON -->
        <div class="action-wrapper">
            <button @click="handleAuth" :disabled="loading" class="primary-btn">
              <span v-if="!loading">{{ isLogin ? 'Login to Terminal' : 'Create Account' }}</span>
              <span v-else class="loader"></span>
            </button>
        </div>

        <div class="toggle-auth">
          <span>{{ isLogin ? "New researcher?" : "Already verified?" }}</span>
          <button @click="isLogin = !isLogin" class="link-btn">{{ isLogin ? 'Join Team' : 'Back to Login' }}</button>
        </div>
      </div>
    </div>

    <!-- Authenticated State -->
    <div v-else class="user-badge-container">
      <div class="user-badge shadow-pop">
        <div class="status-indicator">
            <span class="online-indicator pulsate"></span>
            <span class="live-label">LIVE</span>
        </div>
        <div class="user-info">
            <span class="user-role">RESEARCHER</span>
            <span class="user-name">{{ user?.username }}</span>
        </div>
        <div class="divider"></div>
        <button @click="logout" class="logout-btn" title="Exit Terminal">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-portal { margin: 1.5rem 0; width: 100%; }

/* --- Auth Card Styling --- */
.auth-card {
  max-width: 440px;
  margin: 3rem auto;
  padding: 2.5rem;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 24px;
  box-shadow: 0 20px 50px rgba(0,0,0,0.15);
  backdrop-filter: blur(10px);
  position: relative;
  overflow: hidden;
}

.auth-header { text-align: center; margin-bottom: 2.5rem; }
.logo-wrapper { position: relative; display: inline-block; margin-bottom: 1rem; }
.mini-logo { width: 48px; filter: drop-shadow(0 0 10px var(--vp-c-brand)); }
.status-dot { position: absolute; bottom: 0; right: 0; width: 12px; height: 12px; border-radius: 50%; border: 2px solid var(--vp-c-bg-soft); }
.status-dot.offline { background: #666; }

.auth-header h2 { margin: 0; font-size: 1.6rem; font-weight: 800; color: var(--vp-c-text-1); letter-spacing: -0.5px; }
.subtitle { font-size: 0.85rem; color: var(--vp-c-text-2); margin-top: 0.4rem; }

.input-group { margin-bottom: 1.4rem; }
.input-group label { display: block; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; margin-bottom: 0.5rem; color: var(--vp-c-text-3); letter-spacing: 0.5px; }
.input-group input {
  width: 100%;
  padding: 0.9rem 1rem;
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  color: var(--vp-c-text-1);
  font-family: 'JetBrains Mono', monospace;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.input-group input:focus { border-color: var(--vp-c-brand); box-shadow: 0 0 0 4px var(--vp-c-brand-soft); outline: none; }

.email-input { display: flex; gap: 0.75rem; }
.code-btn {
  white-space: nowrap;
  padding: 0 1.2rem;
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand);
  border: 1px solid var(--vp-c-brand);
  border-radius: 10px;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}
.code-btn:hover:not(:disabled) { background: var(--vp-c-brand); color: white; }

/* --- Action Button --- */
.action-wrapper { margin-top: 2rem; }
.primary-btn {
  width: 100%;
  padding: 1.1rem;
  background: linear-gradient(135deg, var(--vp-c-brand) 0%, #7000ff 100%);
  color: white;
  border: none;
  border-radius: 14px;
  font-weight: 800;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 10px 20px rgba(0, 163, 255, 0.2);
  display: flex;
  justify-content: center;
  align-items: center;
}
.primary-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 15px 30px rgba(0, 163, 255, 0.4); filter: brightness(1.1); }
.primary-btn:active { transform: translateY(0); }
.primary-btn:disabled { opacity: 0.6; cursor: not-allowed; filter: grayscale(0.5); }

/* --- Authenticated Badge --- */
.user-badge-container { display: flex; justify-content: flex-end; margin-bottom: 1rem; }
.user-badge {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.6rem 1.2rem;
  background: var(--vp-c-bg-soft);
  border-radius: 50px;
  border: 1px solid var(--vp-c-divider);
  transition: all 0.3s;
}
.status-indicator { display: flex; flex-direction: column; align-items: center; }
.online-indicator { width: 10px; height: 10px; background: #00e676; border-radius: 50%; box-shadow: 0 0 10px #00e676; }
.live-label { font-size: 0.6rem; font-weight: 900; color: #00e676; margin-top: 2px; }

.user-info { display: flex; flex-direction: column; line-height: 1.2; }
.user-role { font-size: 0.65rem; font-weight: 800; color: var(--vp-c-text-3); }
.user-name { font-size: 1rem; font-weight: 800; color: var(--vp-c-brand); }

.divider { width: 1px; height: 24px; background: var(--vp-c-divider); }
.logout-btn { color: var(--vp-c-text-2); cursor: pointer; background: none; border: none; padding: 0.4rem; border-radius: 50%; display: flex; transition: all 0.2s; }
.logout-btn:hover { background: rgba(255, 82, 82, 0.1); color: #ff5252; }

/* --- Utilities --- */
.error-msg { background: rgba(255, 23, 68, 0.1); color: #ff1744; padding: 0.75rem; border-radius: 10px; border: 1px solid rgba(255, 23, 68, 0.2); font-size: 0.85rem; font-weight: 600; margin: 1rem 0; }
.success-msg { background: rgba(0, 200, 83, 0.1); color: #00c853; padding: 0.75rem; border-radius: 10px; border: 1px solid rgba(0, 200, 83, 0.2); font-size: 0.85rem; font-weight: 600; margin: 1rem 0; }
.toggle-auth { text-align: center; margin-top: 1.8rem; font-size: 0.9rem; color: var(--vp-c-text-2); }
.link-btn { background: none; border: none; color: var(--vp-c-brand); cursor: pointer; font-weight: 800; text-decoration: underline; margin-left: 0.5rem; }

/* --- Animations --- */
.anim-shake { animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both; }
@keyframes shake { 10%, 90% { transform: translate3d(-1px, 0, 0); } 20%, 80% { transform: translate3d(2px, 0, 0); } 30%, 50%, 70% { transform: translate3d(-4px, 0, 0); } 40%, 60% { transform: translate3d(4px, 0, 0); } }
.pulsate { animation: pulsate-glow 2s infinite; }
@keyframes pulsate-glow { 0% { box-shadow: 0 0 0 0 rgba(0, 230, 118, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(0, 230, 118, 0); } 100% { box-shadow: 0 0 0 0 rgba(0, 230, 118, 0); } }
.slide-in { animation: slide-in 0.3s ease-out; }
@keyframes slide-in { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }

.loader { width: 20px; height: 20px; border: 3px solid rgba(255,255,255,0.3); border-radius: 50%; border-top-color: #fff; animation: spin 1s ease-in-out infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.shadow-pop { box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
.shadow-pop:hover { box-shadow: 0 15px 35px rgba(0,0,0,0.2); transform: translateY(-1px); }
</style>
