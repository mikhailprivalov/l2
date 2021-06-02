<template>
  <nav class="navbar navbar-inverse" :class="loaderInHeader && 'show-loader'">
    <div class="nav-cont" v-if="!loading">
      <div class="navbar-header">
        <router-link :to="authenticated ? '/ui/menu' : '/ui/login'" class="navbar-left logo">
          L<sup>2</sup>
        </router-link>
        <button type="button" class="navbar-toggle collapsed" data-toggle="collapse"
                data-target="#navbar">
          <span class="icon-bar"></span>
          <span class="icon-bar"></span>
          <span class="icon-bar"></span>
        </button>
        <router-link to="/ui/menu" v-if="authenticated">
          <span class="navbar-brand"><small>{{ fio_short }}</small></span>
        </router-link>
        <span class="navbar-brand" v-else><small class="page-title">{{ $route.meta.title }}</small></span>
      </div>
      <div id="navbar" class="navbar-collapse collapse">
        <ul class="nav navbar-nav" v-if="authenticated">
          <li class="dropdown dropdown-large">
            <a href="#" class="dropdown-toggle" data-toggle="dropdown">
              Меню <b class="caret"></b>
            </a>
            <div class="dropdown-menu dropdown-menu-large">
              <div class="dash-buttons text-center">
                <template v-for="(b, i) in menu.buttons">
                  <div v-if="b.hr" :key="i" class="menu-hr"></div>
                  <div v-else class="col-xs-12 col-sm-6 col-md-4 col-lg-3 mb10 dash-btn" :key="b.url">
                    <router-link :to="b.url" class="panel-body"
                                 active-class="dash-active"
                                 :target="b.nt && '_blank'">
                      <span>{{ b.title }}</span>
                    </router-link>
                  </div>
                </template>
              </div>
              <div class="info">
                L2 {{ menu.version }}
              </div>
            </div>
          </li>
        </ul>
        <card-reader v-if="$route.meta.showCardReader"/>
        <ul class="nav navbar-right navbar-nav">
          <li>
            <span class="navbar-brand org-title">
                Организация: {{ user_hospital_title || $orgTitle() }}
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
        <span class="navbar-brand" v-if="authenticated"><small>{{ fio_short }}</small></span>
        <span class="navbar-brand" v-else><small class="page-title">{{ $route.meta.title }}</small></span>
      </div>
      <div class="din-spinner">
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

@Component({
  computed: mapGetters([
    'inLoading',
    'loadingLabel',
    'loaderInHeader',
    'authenticated',
    'menu',
    'fio_short',
    'user_hospital_title',
  ]),
  components: {
    CardReader: () => import('@/ui-cards/CardReader.vue'),
  },
})
export default class Navbar extends Vue {
  authenticated: boolean;

  inLoading: boolean;

  loadingLabel: string;

  loaderInHeader: boolean;

  fio_short: string;

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

.din-spinner {
  text-align: center;
}

.org-title {
  font-size: 14px;
}

.page-title {
  text-transform: uppercase;
}

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
