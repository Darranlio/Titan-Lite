import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'
import mathjax3 from 'markdown-it-mathjax3'

export default withMermaid(defineConfig({
  base: '/Titan-Lite/',
  ignoreDeadLinks: true,
// === 1. 强制深色模式 ===
  appearance: 'dark',
  title: "Digital Asset Lab",
  description: "Advanced Quant & AI Trading Solutions",

  // 开启数学公式支持
  markdown: {
    config: (md) => {
      md.use(mathjax3)
    }
  },

  mermaid: {
    // 使用 'base' 主题，它允许我们自定义所有颜色
    theme: 'base',
    themeVariables: {
      // 告诉 Mermaid 我们在深色模式下
      darkMode: true,

      // 1. 背景：透明，完美融入网站背景
      background: 'transparent',
      mainBkg: 'transparent',

      // 2. 核心节点 (矩形框)：深灰底 + 金色边框 + 白字
      primaryColor: '#1E1E1E',       // 节点背景色 (深炭灰)
      primaryBorderColor: '#D4AF37', // 节点边框色 (香槟金)
      primaryTextColor: '#FFFFFF',   // 节点文字 (纯白)

      // 3. 连线与箭头：高亮灰白，确保清晰
      lineColor: '#E0E0E0',          // 连线颜色 (亮灰)
      arrowheadColor: '#E0E0E0',     // 箭头颜色

      // 4. 子图/容器 (Subgraph)：稍浅的灰色背景，做层次区分
      tertiaryColor: '#252526',      // 容器背景
      tertiaryBorderColor: '#555555',// 容器边框 (暗灰)
      tertiaryTextColor: '#CCCCCC',  // 容器标题文字 (银灰)

      // 5. 特殊形状 (圆圈/数据库)：使用强调色
      secondaryColor: '#2D2D2D',
      secondaryBorderColor: '#FFD700', // 更亮的金色强调
      secondaryTextColor: '#FFF',

      // 6. 字体优化：使用等宽字体增加科技感
      fontFamily: '"JetBrains Mono", "Fira Code", monospace',
      fontSize: '14px'
    },
  },

  themeConfig: {
    // === 1. 顶部导航栏 (NavBar) ===
    nav: [
      { text: '实验室中心', link: '/' },
      { text: '我的基金', link: '/projects/titan-lite/portfolio' },
      { text: '研报档案', link: '/projects/titan-lite/reports/index' },
      { text: '技术手册', link: '/projects/titan-lite/design/design_doc' },
      { text: '学习笔记', link: '/notes/python/tricks' }
    ],

    // === 2. 侧边栏 (Sidebar) ===
    sidebar: {
      '/': [
        {
          text: '📊 实验室控制台',
          items: [
            { text: '控制中心 (首页)', link: '/' },
            { text: '🏦 我的基金中心', link: '/projects/titan-lite/portfolio' },
          ]
        },
        {
          text: '📂 数字化档案馆',
          collapsed: false,
          items: [
            { text: '全市场研报索引', link: '/projects/titan-lite/reports/index' },
            { text: '🌏 宏观全景展望', link: '/projects/titan-lite/reports/market_overview' },
          ]
        },
        {
          text: '🏗️ 核心技术文档',
          collapsed: false,
          items: [
            { text: '系统原理与哲学', link: '/projects/titan-lite/design/architecture_theory' },
            { text: '施工细节与UI规范', link: '/projects/titan-lite/design/ui_logic_spec' },
            { text: 'API 接口手册', link: '/projects/titan-lite/design/api' },
          ]
        },
        {
          text: '🚀 部署与使用',
          collapsed: true,
          items: [
            { text: '使用手册', link: '/projects/titan-lite/design/usage_guide' },
            { text: '部署运维指南', link: '/projects/titan-lite/design/deploy' },
          ]
        }
      ],

      // -----------------------------------------
      // B. 当用户在 笔记 栏目里时
      // -----------------------------------------
      '/notes/': [
        {
          text: 'Python 进阶',
          collapsed: false, // 默认展开
          items: [
            { text: 'Pandas 性能优化', link: '/notes/python/pandas-opt' },
            { text: '异步编程实战', link: '/notes/python/async' }
          ]
        },
        {
          text: 'DevOps 运维',
          collapsed: true, // 默认折叠
          items: [
            { text: 'Docker 常用指令', link: '/notes/devops/docker' }
          ]
        }
      ],

      // -----------------------------------------
      // C. 当用户在 随想录 栏目里时
      // -----------------------------------------
      '/thoughts/': [
        {
          text: '年度规划',
          items: [
            { text: '2026 目标', link: '/thoughts/2026-plan' },
            { text: '2027 展望', link: '/thoughts/2027-vision' }
          ]
        }
      ]
    },

    // 社交链接
    socialLinks: [
      { icon: 'github', link: 'https://github.com/Darranlio' }
    ],
    
    // 页脚
    footer: {
        message: 'Built with ❤️ using VitePress',
        copyright: '© 2026 Darranlio | All Rights Reserved'
    }
  }
}))