export {};

declare global {
  interface Window {
    $: any
    okmessage: (title: string, body: string | void) => void
    errmessage: (title: string, body: string | void) => void
    wrnmessage: (title: string, body: string | void) => void
  }
}
