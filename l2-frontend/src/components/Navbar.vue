<template>
  <nav class="navbar navbar-inverse" :class="loaderInHeader && 'show-loader'">
    <div class="nav-cont" v-if="!loading">
      <div class="navbar-header">
        <a href="/mainmenu" class="navbar-left logo">
          L<sup>2</sup>
        </a>
        <button type="button" class="navbar-toggle collapsed" data-toggle="collapse"
                data-target="#navbar">
          <span class="icon-bar"></span>
          <span class="icon-bar"></span>
          <span class="icon-bar"></span>
        </button>
        <a href="/mainmenu">
          <span class="navbar-brand"><small>Иванов Иван Иванович</small></span>
        </a>
      </div>
      <div id="navbar" class="navbar-collapse collapse">
        <ul class="nav navbar-nav">
          <li class="dropdown dropdown-large">
            <a href="#" class="dropdown-toggle" data-toggle="dropdown">
              Меню <b class="caret"></b>
            </a>
            <div class="dropdown-menu dropdown-menu-large">
              <div class="dash-buttons text-center">
              </div>
              <div class="dash-buttons text-center">
                //
              </div>
              <div class="info">
                L2 4.0
              </div>
            </div>
          </li>
        </ul>
        <ul class="nav navbar-right navbar-nav">
          <li>
            <span class="navbar-brand" style="font-size: 14px">
                Организация: DEFORG
            </span>
          </li>
        </ul>
      </div>
    </div>
    <div class="nav-loader center" v-else>
      <div class="navbar-header">
        <div class="navbar-left logo">
          L<sup>2</sup>
        </div>
        <span class="navbar-brand"><small>Иванов Иван Иванович</small></span>
      </div>
      <div class="din-spinner" style="text-align: center">
        <div class="sk-fading-circle">
          <div class="sk-circle1 sk-circle"></div>
          <div class="sk-circle2 sk-circle"></div>
          <div class="sk-circle3 sk-circle"></div>
          <div class="sk-circle4 sk-circle"></div>
          <div class="sk-circle5 sk-circle"></div>
          <div class="sk-circle6 sk-circle"></div>
          <div class="sk-circle7 sk-circle"></div>
          <div class="sk-circle8 sk-circle"></div>
          <div class="sk-circle9 sk-circle"></div>
          <div class="sk-circle10 sk-circle"></div>
          <div class="sk-circle11 sk-circle"></div>
          <div class="sk-circle12 sk-circle"></div>
        </div>
        <span class="loading-text">{{ loadingText }}</span>
      </div>
    </div>
  </nav>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import { mapGetters } from 'vuex';
import * as actions from '../store/action-types';

@Component({
  computed: mapGetters(['inLoading', 'loadingLabel', 'loaderInHeader']),
})
export default class Navbar extends Vue {
  inLoading: boolean;

  loadingLabel: string;

  loaderInHeader: boolean;

  async mounted() {
    await this.$store.dispatch(actions.INC_LOADING);
    console.log('mounted');
    // await this.$store.dispatch(actions.DEC_LOADING);
  }

  get loading() {
    return this.inLoading && this.loaderInHeader;
  }

  get loadingText() {
    return (this.loadingLabel || 'Загрузка').toUpperCase();
  }
}
</script>

<style lang="scss" scoped>
.nav-loader {
  display: block;
}

.loading-text {
  color: #fff;
  font-size: 14pt;
  font-weight: 200;
  margin-left: 10px;
  vertical-align: middle;
  display: inline-block;
}
</style>
