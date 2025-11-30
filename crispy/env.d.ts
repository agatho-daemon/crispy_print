/// <reference types="vite/client" />

declare module "*.vue" {
  const component: import("vue").DefineComponent
  export default component
}

// Frappe globals
declare global {
  interface Window {
    frappe: any
    $: any
    mountCrispyPrint: (selector?: string) => any
    Awesomplete: any
  }
  const frappe: any
  const $: any
  const Awesomplete: any
}

export {}
