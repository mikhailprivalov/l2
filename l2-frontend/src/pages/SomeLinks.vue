<template>
  <div>
    <h5>{{ title }}</h5>
    <ul style="list-style-type: none">
      <li v-for="r in link_rows" :key="r" style="padding-top: 7px; font-size: 14px;">
        <a :href="`${r.link}`" target="_blank" :title=r.comment v-tippy>
          {{ r.title }} - {{ r.link }}
        </a>
      </li>
    </ul>

  </div>
</template>

<script lang="ts">
import Component from 'vue-class-component';
import Vue from 'vue';

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
    const result_data = await this.$api('get-links');
    this.link_rows = result_data.rows;
  }
}
</script>

<style scoped lang="scss">
.buttons {
  margin-bottom: 5px;
  color: #cacfd2;
}
</style>
