<template>
  <a v-if="is_schedule" href="#" @click.prevent="open_page">Записать</a>
  <a v-else href="#" @click.prevent="open_page">ЭЛН</a>
</template>

<script>
import api from "@/api";
import * as action_types from "@/store/action-types";

export default {
  name: 'RmisLink',
  props: {
    is_schedule: {
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
      await this.$store.dispatch(action_types.INC_LOADING);

      if (!this.urlAuth) {
        await this.get_auth()
      }

      await new Promise(resolve => {
        const openWindow = window.open(this.urlAuth, '_blank');
        setTimeout(() => {
          openWindow.close();
          setTimeout(() => {
            window.open(this.urlAddress, '_blank');
            resolve();
          }, 5);
        }, 5);
      });

      await this.$store.dispatch(action_types.DEC_LOADING);
    },
    async get_auth() {
      const params = await api('rmis-link');
      this.urlAuth = params.auth_param;
      if (this.is_schedule) {
        this.urlAddress = params.url_schedule;
      } else {
        this.urlAddress = params.url_eln;
      }
    },
  },
}
</script>
