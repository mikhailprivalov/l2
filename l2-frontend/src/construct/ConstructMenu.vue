<template>
  <div v-frag>
    <h4 class="f-h text-center">
      Конструктор
    </h4>
    <div class="row menu dash-buttons text-center">
      <div
        v-for="b in buttons"
        :key="b.title"
        class="col-xs-12 col-sm-6 col-md-4 col-lg-3 mb10 dash-btn"
      >
        <router-link
          :to="b.url"
          class="panel-body"
          :target="b.nt && '_blank'"
        >
          <span>{{ b.title }}</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';

import * as actions from '@/store/action-types';
import { Button } from '@/types/menu';

@Component({
  data() {
    return {
      buttons: [],
    };
  },
  created() {
    this.loadData();
  },
})
export default class ConstructMenu extends Vue {
  buttons: Button[];

  async loadData() {
    await this.$store.dispatch(actions.INC_G_LOADING);
    const { menu } = await this.$api('/construct-menu-data');
    this.buttons = menu;
    await this.$store.dispatch(actions.DEC_G_LOADING);
  }
}
</script>

<style lang="scss" scoped>
.mb10 {
  margin-bottom: 5px;
}

.menu.dash-buttons > div.mb10 {
  margin-right: 0;
}

.menu.row.dash-buttons {
  margin-right: -2px;
  margin-left: -2px;
}
</style>
