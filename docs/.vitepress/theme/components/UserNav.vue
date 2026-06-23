<template>
  <div class="user-nav-container">
    <div v-if="token" class="avatar-wrapper shadow-pop" @click.stop="showDropdown = !showDropdown">
      <div class="avatar-circle">
        <span class="initial">{{ user?.username?.charAt(0).toUpperCase() || 'U' }}</span>
        <div class="online-indicator"></div>
      </div>
      <transition name="fade">
        <div v-if="showDropdown" class="nav-dropdown" @click.stop>
          <div class="user-meta">
            <span class="u-role">Researcher</span>
            <span class="u-name">{{ user?.username || 'Guest' }}</span>
          </div>
          <div class="u-divider"></div>
          <a href="/projects/titan-lite/portfolio" class="u-link">Portfolio Center</a>
          <button class="u-link u-disabled">Upload Avatar (Pro)</button>
          <div class="u-divider"></div>
          <button @click="logout" class="u-link u-logout">Logout System</button>
        </div>
      </transition>
    </div>
    <button v-else @click="showModal = true" class="anon-btn" title="Login to Terminal">
      <div class="anon-icon">
        <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2.5" fill="none"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
      </div>
    </button>
    
    <!-- Auth Modal -->
    <Teleport to="body">
      <transition name="fade">
        <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
          <div class="modal-content-wrap">
            <button class="close-btn" @click="showModal = false">&times;</button>
            <AuthPortal />
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import AuthPortal from '../../../projects/titan-lite/AuthPortal.vue'

const token = ref(null)
const user = ref(null)
const showDropdown = ref(false)
const showModal = ref(false)

const loadUser = () => {
  if (typeof window !== 'undefined') {
    token.value = localStorage.getItem('titan_token')
    user.value = JSON.parse(localStorage.getItem('titan_user') || 'null')
    if (token.value) showModal.value = false
  }
}

const hideDropdown = () => { showDropdown.value = false }

onMounted(() => {
  loadUser()
  window.addEventListener('storage', loadUser)
  window.addEventListener('click', hideDropdown)
})

onUnmounted(() => {
  window.removeEventListener('storage', loadUser)
  window.removeEventListener('click', hideDropdown)
})

const logout = () => {
  localStorage.removeItem('titan_token')
  localStorage.removeItem('titan_user')
  window.location.reload()
}
</script>

<style scoped>
.user-nav-container { position: relative; display: flex; align-items: center; margin-left: 12px; }
.avatar-wrapper { position: relative; cursor: pointer; }
.avatar-circle { width: 34px; height: 34px; background: var(--vp-c-brand); border-radius: 50%; display: flex; align-items: center; justify-content: center; position: relative; color: white; font-weight: bold; }
.online-indicator { position: absolute; bottom: 0; right: 0; width: 10px; height: 10px; background: #00e676; border-radius: 50%; border: 2px solid var(--vp-c-bg); }
.nav-dropdown { position: absolute; top: 45px; right: 0; background: var(--vp-c-bg-soft); border: 1px solid var(--vp-c-divider); border-radius: 12px; padding: 0.5rem; min-width: 200px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); z-index: 100; }
.user-meta { padding: 0.5rem; display: flex; flex-direction: column; }
.u-role { font-size: 0.7rem; color: var(--vp-c-text-3); font-weight: bold; text-transform: uppercase; }
.u-name { font-size: 1rem; color: var(--vp-c-text-1); font-weight: bold; }
.u-divider { height: 1px; background: var(--vp-c-divider); margin: 0.5rem 0; }
.u-link { display: block; width: 100%; text-align: left; padding: 0.5rem; border-radius: 6px; color: var(--vp-c-text-2); text-decoration: none; font-size: 0.9rem; border: none; background: transparent; cursor: pointer; }
.u-link:hover { background: var(--vp-c-bg-alt); color: var(--vp-c-text-1); }
.u-logout { color: #ff5252; }
.u-logout:hover { background: rgba(255,82,82,0.1); color: #ff5252; }
.u-disabled { opacity: 0.5; cursor: not-allowed; }
.anon-btn { background: transparent; border: none; color: var(--vp-c-text-2); cursor: pointer; padding: 0.5rem; transition: color 0.2s; display: flex; align-items: center; justify-content: center; }
.anon-btn:hover { color: var(--vp-c-brand); }
.modal-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.7); backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; z-index: 99999; }
.modal-content-wrap { position: relative; max-height: 100vh; overflow-y: auto; background: transparent; width: 100%; display: flex; justify-content: center; }
.close-btn { position: absolute; top: 2rem; right: 2rem; font-size: 2.5rem; color: var(--vp-c-text-2); background: transparent; border: none; cursor: pointer; z-index: 100000; transition: color 0.2s; line-height: 1; }
.close-btn:hover { color: white; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
