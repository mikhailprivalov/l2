export {};

declare global {
  interface Window {
    ORG_TITLE: string;
    SYSTEM_AS_VI: boolean;
    PROTOCOL_PLAIN_TEXT: boolean;
    SPLIT_PRINT_RESULT: boolean;
    L2_LOGO_CLASS: string;
    $: any
    Modernizr: any
    prefetch: any
    eds: any
    selectTextEl: (arg: any) => void
    okblink: (arg: any) => void
    clearselection: () => void
    set_instance: (arg: any) => void
    okmessage: (title: string, body: string | void) => void
    errmessage: (title: string, body: string | void) => void
    wrnmessage: (title: string, body: string | void) => void
    printResults: (pks: string[]) => void
    today: Date
    getFormattedDate: (d: Date) => string
  }
}
