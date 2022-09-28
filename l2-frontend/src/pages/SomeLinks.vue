<template>
  <div>
    <h5>{{ title }}</h5>
    <ul style="list-style-type: none">
      <li
        v-for="r in link_rows"
        :key="r.title"
        style="padding-top: 9px; font-size: 16px;"
      >
        <a
          v-tippy
          :href="`${r.link}`"
          target="_blank"
          :title="r.comment"
        >
          {{ r.title }} - {{ r.link }}
        </a>
      </li>
    </ul>
  </div>
</template>

<script lang="ts">
import Component from 'vue-class-component';
import Vue from 'vue';

import * as actions from '@/store/action-types';

@Component({
  data() {
    return {
      title: 'Ресурсы',
      link_rows: [],
    };
  },
  mounted() {
    this.init();
  },
})
export default class SomeLinks extends Vue {
  link_rows: any;

  async init() {
    await this.$store.dispatch(actions.INC_LOADING);
    const resultData = await this.$api('get-links');
    this.link_rows = resultData.rows;
    await this.$store.dispatch(actions.DEC_LOADING);
  }
}
</script>

<style scoped lang="scss">
.buttons {
  margin-bottom: 5px;
  color: #cacfd2;
}
</style>
