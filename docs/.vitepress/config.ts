import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

// 使用 withMermaid 包裹配置，启用图表支持
export default withMermaid(defineConfig({
  title: "Titan-Lite",
  description: "Personal Quant Knowledge Base",
  
  // 强制深色模式 (Hacker Style)
  appearance: 'dark', 
  
  themeConfig: {
    // 顶部导航
    nav: [
      { text: '仪表盘', link: '/' },
      { text: '策略逻辑', link: '/strategy' },
      { text: '部署日志', link: '/deploy' }
    ],

    // 左侧侧边栏
    sidebar: [
      {
        text: '核心架构',
        items: [
          { text: '系统总览', link: '/' },
          { text: '卡尔曼滤波', link: '/strategy' }
        ]
      },
      {
        text: '运维记录',
        items: [
          { text: '部署指南', link: '/deploy' }
        ]
      }
    ],

    // 页脚装X
    footer: {
      message: 'SYSTEM ONLINE. ENCRYPTED CONNECTION.',
      copyright: '© 2026 Titan-Lite Protocol'
    }
  }
}))