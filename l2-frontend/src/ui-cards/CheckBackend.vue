<template>
  <div id="check-backend" />
</template>

<script lang="ts">
import Vue from 'vue';
import { mapGetters } from 'vuex';
import Component from 'vue-class-component';
import { POSITION } from 'vue-toastification/src/ts/constants';

import * as actions from '@/store/action-types';

@Component({
  computed: mapGetters(['authenticated', 'user_data', 'version']),
  data() {
    return {
      userIsIdle: false,
      hasError: false,
      aliveTimer: null,
    };
  },
})
export default class CheckBackend extends Vue {
  authenticated: boolean;

  userIsIdle: boolean;

  hasError: boolean;

  aliveTimer: any | void;

  user_data: any;

  version: string | null;

  mounted() {
    setTimeout(() => this.check(), 8000);
  }

  check() {
    if (this.aliveTimer) {
      clearTimeout(this.aliveTimer);
    }

    if (this.$route?.name === 'login' && this.authenticated) {
      const urlParams = new URLSearchParams(window.location.search);
      const nextPath = urlParams.get('next');
      this.$router.push(nextPath || { name: 'menu' });
      return;
    }

    window.$.ajax({
      method: 'GET',
      url: '/mainmenu/',
      cache: false,
      statusCode: {
        500: () => {
          this.$toast.clear();
          this.$toast.error('Сервер недоступен. Ошибка 500. Ожидайте доступность сервера.', {
            position: POSITION.BOTTOM_RIGHT,
            timeout: this.userIsIdle ? 300000 : 20000,
            icon: true,
          });

          if (!this.hasError) {
            this.hasError = true;
            this.$store.dispatch(actions.INC_LOADING);
          }
          window.$('input').blur();
        },
        502: () => {
          this.$toast.clear();
          this.$toast.error('Сервер недоступен. Ошибка 502. Ожидайте доступность сервера.', {
            position: POSITION.BOTTOM_RIGHT,
            timeout: this.userIsIdle ? 300000 : 20000,
            icon: true,
          });

          if (!this.hasError) {
            this.hasError = true;
            this.$store.dispatch(actions.INC_LOADING);
          }
          window.$('input').blur();
        },
      },
    })
      .fail((jqXHR) => {
        if (jqXHR.status === 502 || jqXHR.status === 500) return;
        this.$toast.clear();
        this.$toast.error('Сервер недоступен. Ошибка связи с сервером. Сообщите администратору о проблеме', {
          position: POSITION.BOTTOM_RIGHT,
          timeout: this.userIsIdle ? 300000 : 20000,
          icon: true,
        });

        if (!this.hasError) {
          this.hasError = true;
          this.$store.dispatch(actions.INC_LOADING);
        }
        window.$('input').blur();
      })
      .done((data) => {
        const [status, login, version] = String(data).split(':');
        const isOk = status === 'OK';

        if (!this.authenticated && isOk) {
          const urlParams = new URLSearchParams(window.location.search);
          const nextPath = urlParams.get('next');
          this.$router.push(nextPath || { name: 'menu' });
        }

        if (this.authenticated && !isOk) {
          this.$router.push(`/ui/login?next=${encodeURIComponent(window.location.href.replace(window.location.origin, ''))}`);
          return;
        }

        if (this.authenticated && this.user_data && !this.user_data.loading && this.user_data.username !== login) {
          window.location.reload();
        }

        if (this.authenticated && this.version && this.version !== version) {
          // eslint-disable-next-line no-console
          console.log({ uiVersion: this.version, newVersion: version });
          this.$store.dispatch(actions.HAS_NEW_VERSION);
        }

        if (this.hasError) {
          this.$toast.clear();
          this.hasError = false;
          this.$toast.success('Сервер доступен', {
            position: POSITION.BOTTOM_RIGHT,
            timeout: 10000,
            icon: true,
          });
          this.$store.dispatch(actions.DEC_LOADING);
        }
      })
      .always(() => {
        this.aliveTimer = setTimeout(() => this.check(), this.userIsIdle ? 60000 : 20000);
      });
  }
}
</script>

<style scoped>
#check-backend {
  display: none;
}
</style>
