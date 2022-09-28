<template>
  <div
    v-show="!!user_data.rmis_location"
    class="root"
  >
    <!--    <div v-if="loading">-->
    <!--      загрузка расписания...-->
    <!--    </div>-->
    <!--    <div v-else>-->
    <!--      {{user_data.rmis_location}}-->
    <!--    </div>-->
  </div>
</template>

<script lang="ts">
import { mapGetters } from 'vuex';

export default {
  name: 'RmisLocation',
  data() {
    return {
      loading: false,
      init: false,
      data: {},
    };
  },
  computed: {
    ...mapGetters({
      user_data: 'user_data',
    }),
  },
  watch: {
    async user_data({ rmis_location: rl }) {
      if (!this.init && rl) {
        // this.init = true;
        // this.loading = true;
        // this.data = await usersPoint.loadLocation();
        // this.loading = false;
      }
    },
  },
};
</script>

<style scoped lang="scss">
.root {
  color: #fff;
}
</style>
