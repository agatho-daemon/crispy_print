/// <reference types="vite/client" />

declare module "*.vue" {
  import type { DefineComponent } from "vue"
  const component: DefineComponent<{}, {}, any>
  export default component
}

// Frappe globals
declare global {
  interface Window {
    frappe: any
    $: any
    mountCrispyPrint: (selector?: string) => any
  }
  const frappe: any
  const $: any
}

export {}