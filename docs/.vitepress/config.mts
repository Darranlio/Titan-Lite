import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'
import mathjax3 from 'markdown-it-mathjax3'

export default withMermaid(defineConfig({
// === 1. 强制深色模式 ===
  appearance: 'dark',
  title: "可塑性记忆Max",
  description: "Projects, Notes & Thoughts",

  // 开启数学公式支持
  markdown: {
    config: (md) => {
      md.use(mathjax3)
    }
  },

  themeConfig: {
    // === 1. 顶部导航栏 (NavBar) ===
    // 按照你的要求：首页 | 项目 | 笔记 | 随想录
    nav: [
      { text: '首页', link: '/' },
      
      // [项目]：设计为下拉菜单，方便快速切换不同项目
      { 
        text: '项目', 
        items: [
          { 
            text: '当前进行中', 
            items: [
              { text: '📊 Titan-Lite 量化系统', link: '/projects/titan-lite/' }
            ]
          },
          { 
            text: '归档 / 其他', 
            items: [
              { text: '🏗️ 待启动项目...', link: '/projects/future-project/' }
            ]
          }
        ]
      },

      // [笔记]：直接链接到笔记主页，或者也可以做成下拉
      { text: '笔记', link: '/notes/python/tricks' },
      
      // [随想录]
      { text: '随想录', link: '/thoughts/2024-plan' }
    ],

    // === 2. 侧边栏 (Sidebar) ===
    // 核心逻辑：根据当前路径，显示对应的侧边栏
    sidebar: {
      // -----------------------------------------
      // A. 当用户在 Titan-Lite 项目文档里时
      // -----------------------------------------
      '/projects/titan-lite/': [
        {
          text: 'Titan-Lite 量化系统',
          items: [
            { text: '项目简介', link: '/projects/titan-lite/' }, // 对应 index.md
            { text: '系统架构设计', link: '/projects/titan-lite/architecture' },
            { text: '核心策略算法', link: '/projects/titan-lite/strategy' },
            { text: 'API 接口文档', link: '/projects/titan-lite/api' },
            { text: '部署运维', link: '/projects/titan-lite/deploy' }
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