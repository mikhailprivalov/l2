<template>
  <div class="dropdown-menu dropdown-menu-large">
    <div class="dash-buttons text-center">
      <template v-for="(b, i) in menu.buttons">
        <div
          v-if="b.hr"
          :key="i"
          class="menu-hr"
        />
        <div
          v-else
          :key="b.url"
          class="col-xs-12 col-sm-6 col-md-4 col-lg-3 mb10 dash-btn"
        >
          <router-link
            :to="b.url"
            class="panel-body"
            active-class="dash-active"
            :target="b.nt && '_blank'"
          >
            <span>{{ b.title }}</span>
          </router-link>
        </div>
      </template>
    </div>
    <div class="info">
      {{ system }} {{ version }}
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import { mapGetters } from 'vuex';

@Component({
  computed: mapGetters(['menu', 'version']),
})
export default class NavbarDropdownContent extends Vue {
  version: string | null;

  menu: any;

  get system() {
    return this.$systemTitle();
  }
}
</script>

<style lang="scss" scoped>
.menu-hr {
  width: 100%;
}

.dash-buttons .panel-body span {
  font-size: 18px;
  font-weight: 300;
}

a.dash-active {
  background: #048493 !important;
  border: 1px solid #048493 !important;
}
</style>
