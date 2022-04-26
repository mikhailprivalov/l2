declare module '*.vue' {
  import V from 'vue';

  declare module 'vue/types/vue' {
    interface Vue {
      $dialog: any;
      $api: (...any) => Promise<any>;
      $fullscreen: any;
      $systemTitle: () => string;
      $asVI: () => boolean;
      $l2LogoClass: () => string;
    }
  }

  export default V;
}
