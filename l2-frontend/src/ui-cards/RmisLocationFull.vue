<template>
  <table
    v-show="!!user_data.rmis_location"
    class="table table"
  >
    <thead>
      <tr>
        <th />
      </tr>
    </thead>
  </table>
</template>

<script lang="ts">
import { mapGetters } from 'vuex';

import usersPoint from '@/api/user-point';

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
        this.init = true;
        this.loading = true;
        // eslint-disable-next-line no-console
        console.log('rmis_location', rl);
        this.data = await usersPoint.loadLocation({});
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped lang="scss"></style>
