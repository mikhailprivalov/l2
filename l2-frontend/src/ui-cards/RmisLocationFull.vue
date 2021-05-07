<template>
  <table v-show="!!user_data.rmis_location" class="table table">
    <thead>
      <tr>
        <th></th>
      </tr>
    </thead>
  </table>
</template>

<script>
import { mapGetters } from 'vuex';
import usersPoint from '../api/user-point';

export default {
  name: 'RmisLocation',
  data() {
    return {
      loading: false,
      init: false,
      data: {},
    };
  },
  watch: {
    async user_data({ rmis_location }) {
      if (!this.init && rmis_location) {
        this.init = true;
        this.loading = true;
        console.log('rmis_location', rmis_location);
        this.data = await usersPoint.loadLocation({});
        this.loading = false;
      }
    },
  },
  computed: {
    ...mapGetters({
      user_data: 'user_data',
    }),
  },
};
</script>

<style scoped lang="scss">

</style>
