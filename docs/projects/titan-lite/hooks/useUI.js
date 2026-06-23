import { reactive } from 'vue'

/**
 * Titan-UI V3.3: 工业级响应式单例
 * 使用 reactive 替代 ref，确保深层属性变更能 100% 触发全站重绘。
 * 强制挂载到 window 对象，彻底解决 VitePress 异步分包导致的状态隔离。
 */

const GLOBAL_KEY = '__TITAN_UI_GLOBAL_STATE_V3__'

const createInitialState = () => ({
  toast: { show: false, message: '', type: 'success' },
  confirm: { show: false, message: '', onConfirm: null, onCancel: null },
  _timer: null
})

let state

if (typeof window !== 'undefined') {
  if (!window[GLOBAL_KEY]) {
    window[GLOBAL_KEY] = reactive(createInitialState())
  }
  state = window[GLOBAL_KEY]
} else {
  // SSR 环境使用普通对象（避免 Teleport 报错）
  state = createInitialState()
}

/**
 * 暴露全局状态
 */
export const uiState = state

/**
 * 显示消息提示 (Toast)
 */
export const showToast = (message, type = 'success') => {
  if (state._timer) {
    clearTimeout(state._timer)
  }
  
  state.toast.message = message
  state.toast.type = type
  state.toast.show = true
  
  state._timer = setTimeout(() => {
    state.toast.show = false
    state._timer = null
  }, 3000)
}

/**
 * 显示二次确认弹窗 (Confirm)
 */
export const showConfirm = (message) => {
  // 清理可能存在的旧弹窗状态
  state.confirm.show = false
  
  return new Promise((resolve) => {
    state.confirm.message = message
    state.confirm.onConfirm = () => {
      state.confirm.show = false
      resolve(true)
    }
    state.confirm.onCancel = () => {
      state.confirm.show = false
      resolve(false)
    }
    state.confirm.show = true
  })
}
