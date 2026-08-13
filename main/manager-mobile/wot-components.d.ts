declare module 'vue' {
  interface GlobalComponents {
    WdButton: typeof import('wot-design-uni/components/wd-button/wd-button.vue')['default']
    WdNavbar: typeof import('wot-design-uni/components/wd-navbar/wd-navbar.vue')['default']
  }
}

export {}
