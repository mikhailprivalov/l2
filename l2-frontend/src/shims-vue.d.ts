declare module '*.vue' {
  import Vue from 'vue';

  declare module 'vue/types/vue' {
    interface Vue {
      $dialog: any;
      $api: any;
      $systemTitle: () => string;
      $asVI: () => boolean;
      $l2LogoClass: () => string;
    }
  }

  export default Vue;
}
