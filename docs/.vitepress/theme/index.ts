import DefaultTheme from 'vitepress/theme'
import { h } from 'vue'
import UserNav from './components/UserNav.vue'
import UiOverlay from '../../projects/titan-lite/UiOverlay.vue'

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('UiOverlay', UiOverlay)
  },
  Layout: () => {
    return h(DefaultTheme.Layout, null, {
      'nav-bar-content-after': () => h(UserNav),
      'layout-bottom': () => h(UiOverlay)
    })
  }
}
