<template>
  <li>
    <a href="#" @click.prevent="open_schedule">
      В регистратуру
    </a>
  </li>
</template>

<script>
import api from "@/api";

export default {
  name: 'DoctorSchedule',
  data() {
    return {
      linkAuth: '',
      linkSchedule: '',
    };
  },
  methods: {
    async open_schedule()  {
      await this.get_auth()
        let myWindowURL = this.linkAuth;
        let myWidowSchedule = this.linkSchedule
        let openWindow = null;
        openWindow = window.open(myWindowURL, '_blank');

        setTimeout(function() {
            openWindow.close()
        }, 200);

       setTimeout(function() {
            window.open(myWidowSchedule);
        }, 500);
    },
    async get_auth(){
        const params = await api('eln-link');
        this.linkAuth = params.eln_auth;
        this.linkSchedule = params.doctor_schedule;
      },
  },
}
</script>
