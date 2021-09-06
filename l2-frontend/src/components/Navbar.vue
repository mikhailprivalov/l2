<template>
  <nav class="navbar navbar-inverse" :class="loaderInHeader && 'show-loader'">
    <div class="nav-cont" v-show="!loading">
      <div class="navbar-header">
        <router-link :to="authenticated ? '/ui/menu' : '/ui/login'" class="navbar-left logo"> L<sup>2</sup> </router-link>
        <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar">
          <span class="icon-bar"></span>
          <span class="icon-bar"></span>
          <span class="icon-bar"></span>
        </button>
        <router-link to="/ui/menu" v-if="authenticated">
          <span class="navbar-brand">
            <small>{{ fio_short }}</small>
          </span>
        </router-link>
        <span class="navbar-brand" v-else>
          <small class="page-title">{{ metaTitle }}</small>
        </span>
      </div>
      <div id="navbar" class="navbar-collapse collapse">
        <ul class="nav navbar-nav" v-if="authenticated">
          <li class="dropdown dropdown-large">
            <a href="#" class="dropdown-toggle" data-toggle="dropdown"> Меню <b class="caret"></b> </a>
            <NavbarDropdownContent />
          </li>
        </ul>
        <extended-patient-search v-if="meta.showExtendedPatientSearch" />
        <card-reader v-if="meta.showCardReader" />
        <ul class="nav navbar-nav" v-if="meta.showCreateDirection">
          <create-descriptive-direction />
        </ul>
        <ul class="nav navbar-nav" v-if="meta.showRmisLinkSchedule">
          <li>
            <rmis-link isSchedule />
          </li>
        </ul>
        <ul class="nav navbar-right navbar-nav">
          <li v-if="hasNewVersion">
            <button type="button" class="btn btn-blue btn-blue-nb btn-reload" @click="reload">
              L2 обновилась! Перезагрузить страницу
            </button>
          </li>
          <li v-else>
            <span class="navbar-brand org-title"> Организация: {{ user_hospital_title || $orgTitle() }} </span>
          </li>
        </ul>
      </div>
    </div>
    <div class="nav-loader center" v-show="loading">
      <div class="navbar-header">
        <div class="navbar-left logo">L<sup>2</sup></div>
        <span class="navbar-brand" v-if="authenticated">
          <small>{{ fio_short }}</small>
        </span>
        <span class="navbar-brand" v-else>
          <small class="page-title">{{ metaTitle }}</small>
        </span>
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
import NavbarDropdownContent from '@/components/NavbarDropdownContent.vue';

@Component({
  computed: mapGetters([
    'inLoading',
    'loadingLabel',
    'loaderInHeader',
    'authenticated',
    'fio_short',
    'user_hospital_title',
    'hasNewVersion',
  ]),
  components: {
    NavbarDropdownContent,
    CardReader: () => import('@/ui-cards/CardReader.vue'),
    ExtendedPatientSearch: () => import('@/ui-cards/ExtendedPatientSearch/index.vue'),
    CreateDescriptiveDirection: () => import('@/ui-cards/CreateDescriptiveDirection.vue'),
    RmisLink: () => import('@/ui-cards/RmisLink.vue'),
  },
})
export default class Navbar extends Vue {
  authenticated: boolean;

  inLoading: boolean;

  loadingLabel: string;

  hasNewVersion: boolean;

  loaderInHeader: boolean;

  fio_short: string;

  user_hospital_title: string | null;

  $orgTitle: () => string;

  get loading() {
    return this.inLoading && this.loaderInHeader;
  }

  get loadingText() {
    return (this.loadingLabel || 'Загрузка').toUpperCase();
  }

  get meta() {
    return this.$route?.meta || {};
  }

  get metaTitle() {
    return String(this.$route?.meta?.title || '');
  }

  // eslint-disable-next-line class-methods-use-this
  reload() {
    window.location.reload();
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

.btn-reload {
  margin-top: 1px;
}
</style>
