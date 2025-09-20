import { defineConfig } from 'vitepress'

export default defineConfig({
  title: "SOFA",
  description: "Simple Organized Feed for Apple - Security Updates Tracker",
  
  themeConfig: {
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Dashboard', link: '/dashboard' },
      { text: 'API', link: '/api' },
      { text: 'About', link: '/about' }
    ],

    sidebar: [
      {
        text: 'Getting Started',
        items: [
          { text: 'Introduction', link: '/intro' },
          { text: 'Quick Start', link: '/quickstart' },
          { text: 'API Reference', link: '/api' }
        ]
      },
      {
        text: 'Data Feeds',
        items: [
          { text: 'macOS', link: '/feeds/macos' },
          { text: 'iOS', link: '/feeds/ios' },
          { text: 'XProtect', link: '/feeds/xprotect' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/sofa' }
    ],

    footer: {
      message: 'Automatically updated every 6 hours',
      copyright: 'Data sourced from Apple Inc.'
    }
  },

  base: '/sofa-2.0/',
  
  head: [
    ['link', { rel: 'icon', href: '/favicon.ico' }],
    ['meta', { name: 'theme-color', content: '#3eaf7c' }]
  ]
})