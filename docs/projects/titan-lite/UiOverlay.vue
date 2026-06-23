<template>
  <!-- Only render on client side to avoid SSR Teleport errors -->
  <Teleport to="body" v-if="isMounted">
    <!-- Toast Message -->
    <Transition name="toast-slide">
      <div v-if="uiState.toast.show" class="titan-toast shadow-pop" :class="uiState.toast.type">
        <span class="icon">{{ uiState.toast.type === 'error' ? '⚠️' : '✅' }}</span>
        <span class="msg">{{ uiState.toast.message }}</span>
      </div>
    </Transition>

    <!-- Confirm Modal -->
    <Transition name="fade">
      <div v-if="uiState.confirm.show" class="titan-modal-backdrop" @click.self="uiState.confirm.onCancel">
        <div class="titan-modal scale-in">
          <div class="modal-icon">🤔</div>
          <div class="modal-content">{{ uiState.confirm.message }}</div>
          <div class="modal-actions">
            <button class="modal-btn cancel-btn" @click="uiState.confirm.onCancel">取消</button>
            <button class="modal-btn confirm-btn" @click="uiState.confirm.onConfirm">确定执行</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { uiState } from './hooks/useUI.js'

const isMounted = ref(false)
onMounted(() => {
  isMounted.value = true
})
</script>

<style scoped>
/* Toast Styles */
.titan-toast {
  position: fixed;
  top: 100px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100001;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 32px;
  border-radius: 16px;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-brand);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(20px);
  color: var(--vp-c-text-1);
  font-weight: 800;
  font-size: 1rem;
  pointer-events: none;
  min-width: 300px;
  justify-content: center;
}
.titan-toast.success { border-bottom: 4px solid #43a047; }
.titan-toast.error { border-bottom: 4px solid #d32f2f; }
.titan-toast .icon { font-size: 1.2rem; }

/* Modal Styles */
.titan-modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  z-index: 100000;
  display: flex;
  justify-content: center;
  align-items: center;
}
.titan-modal {
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 20px;
  padding: 2.5rem;
  width: 90%;
  max-width: 420px;
  box-shadow: 0 30px 60px rgba(0, 0, 0, 0.5);
  text-align: center;
}
.modal-icon {
  font-size: 3rem;
  margin-bottom: 1.2rem;
}
.modal-content {
  color: var(--vp-c-text-1);
  font-size: 1.1rem;
  font-weight: 800;
  line-height: 1.6;
  margin-bottom: 2.5rem;
}
.modal-actions {
  display: flex;
  gap: 1.2rem;
  justify-content: center;
}
.modal-btn {
  padding: 12px 28px;
  border-radius: 10px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border: none;
  font-size: 1rem;
}
.cancel-btn {
  background: transparent;
  border: 1px solid var(--vp-c-divider);
  color: var(--vp-c-text-2);
}
.cancel-btn:hover { background: var(--vp-c-bg-alt); color: var(--vp-c-text-1); transform: translateY(-1px); }
.confirm-btn {
  background: var(--vp-c-brand);
  color: white;
  box-shadow: 0 4px 12px var(--vp-c-brand-soft);
}
.confirm-btn:hover { filter: brightness(1.1); transform: translateY(-2px); box-shadow: 0 6px 16px var(--vp-c-brand-soft); }

/* Transitions */
.toast-slide-enter-active, .toast-slide-leave-active { transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1); }
.toast-slide-enter-from { opacity: 0; transform: translate(-50%, -40px); }
.toast-slide-leave-to { opacity: 0; transform: translate(-50%, -40px); }

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.scale-in { animation: scaleIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
@keyframes scaleIn { 0% { transform: scale(0.85); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
</style>
