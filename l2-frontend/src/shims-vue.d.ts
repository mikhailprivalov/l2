declare module '*.vue' {
  import Vue from 'vue';

  declare module 'vue/types/vue' {
    interface Vue {
      $dialog: any;
      $api: any;
    }
  }

  export default Vue;
}
