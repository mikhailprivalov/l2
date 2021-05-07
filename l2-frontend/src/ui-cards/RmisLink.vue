<template>
  <a v-if="isSchedule" href="#" @click.prevent="open_page">Записать</a>
  <a v-else href="#" @click.prevent="open_page">ЭЛН</a>
</template>

<script>
import api from '@/api';
import * as actions from '@/store/action-types';

export default {
  name: 'RmisLink',
  props: {
    isSchedule: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      urlAuth: '',
      urlAddress: '',
    };
  },
  methods: {
    async open_page() {
      await this.$store.dispatch(actions.INC_LOADING);

      if (!this.urlAuth) {
        await this.get_auth();
      }

      await new Promise((resolve) => {
        const openWindow = window.open(this.urlAuth, '_blank');
        setTimeout(() => {
          openWindow.close();
          setTimeout(() => {
            window.open(this.urlAddress, '_blank');
            resolve();
          }, 400);
        }, 400);
      });

      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async get_auth() {
      const params = await api('rmis-link');
      this.urlAuth = params.auth_param;
      if (this.isSchedule) {
        this.urlAddress = params.url_schedule;
      } else {
        this.urlAddress = params.url_eln;
      }
    },
  },
};
</script>
