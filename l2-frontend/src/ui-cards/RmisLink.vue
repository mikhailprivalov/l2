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
    is_eln: {
      type: Boolean,
      default: false,
    },
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
      // const urlAuth = this.urlAuth;
      // const urlAddress = this.urlAddress
      let openWindow = null;
      this.$store.dispatch(action_types.INC_LOADING)

      if (this.urlAuth === '') {
        await this.get_auth()
      }

      const p = new Promise((resolve, reject) => {
        openWindow = window.open(this.urlAuth, '_blank');
        resolve({status: true})
      })

      p
        .then((data) => {
          if (data.status) {
            return new Promise((resolve, reject) => {
                setTimeout(() => {
                  openWindow.close()
                  resolve({status: true})
                }, 5);
              }
            )
          }
        }
      )
        .then((data) => {
          if (data.status) {
            return new Promise(() => {
              setTimeout(() => {
                window.open(this.urlAddress, '_blank');
              }, 5);
            })
          }
        })

      this.$store.dispatch(action_types.DEC_LOADING)
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
