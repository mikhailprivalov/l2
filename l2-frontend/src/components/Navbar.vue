<template>
  <nav
    class="navbar navbar-inverse"
    :class="loaderInHeader && 'show-loader'"
  >
    <div
      v-show="!loading"
      class="nav-cont"
    >
      <div class="navbar-header">
        <router-link
          :to="authenticated ? '/ui/menu' : '/ui/login'"
          class="navbar-left logo"
          :class="l2LogoClass"
        >
          <template v-if="asVI">
            {{ system }}
          </template>
          <template v-else>
            L<sup>2</sup>
          </template>
        </router-link>
        <button
          type="button"
          class="navbar-toggle collapsed"
          data-toggle="collapse"
          data-target="#navbar"
        >
          <span class="icon-bar" />
          <span class="icon-bar" />
          <span class="icon-bar" />
        </button>
        <router-link
          v-if="authenticated"
          to="/ui/menu"
        >
          <span class="navbar-brand">
            <small>{{ fio_short }}</small>
          </span>
        </router-link>
        <span
          v-else
          class="navbar-brand"
        >
          <small class="page-title">{{ metaTitle }}</small>
        </span>
      </div>
      <div
        id="navbar"
        class="navbar-collapse collapse"
      >
        <ul
          v-if="authenticated"
          class="nav navbar-nav"
        >
          <li class="dropdown dropdown-large">
            <a
              href="#"
              class="dropdown-toggle"
              data-toggle="dropdown"
            > Меню <b class="caret" /> </a>
            <NavbarDropdownContent />
          </li>
        </ul>
        <ExtendedPatientSearch v-if="meta.showExtendedPatientSearch" />
        <ul class="nav navbar-nav">
          <shiftModal v-if="l2CashEnabled && meta.showShiftModal" />
        </ul>
        <CardReader v-if="meta.showCardReader" />
        <Favorites v-if="meta.showHospFavorites" />
        <OperationPlans v-if="meta.showOperationPlans" />
        <LaboratoryHeader v-if="meta.showLaboratoryHeader" />
        <HelpLinkField v-if="meta.showHelpLinkField" />
        <ul
          v-if="meta.showLaboratorySelector"
          class="nav navbar-nav"
        >
          <li class="dropdown">
            <LaboratorySelector
              with-all-labs
              with-forced-update-query
            />
          </li>
        </ul>
        <ul
          v-if="meta.showLaboratorySelectorWithoutAll"
          class="nav navbar-nav"
        >
          <li class="dropdown">
            <LaboratorySelector
              with-forced-update-query
            />
          </li>
        </ul>
        <ul
          v-if="meta.showCreateDirection"
          class="nav navbar-nav"
        >
          <CreateDescriptiveDirection />
        </ul>
        <ul
          v-if="meta.showRmisLinkSchedule"
          class="nav navbar-nav"
        >
          <li>
            <RmisLink is-schedule />
          </li>
        </ul>
        <ul
          v-if="meta.showEcpSchedule"
          class="nav navbar-nav"
        >
          <EcpSchedule />
        </ul>
        <ExpertiseStatus v-if="meta.showExpertiseStatus" />
        <PrintQueue v-if="meta.showPrintQueue" />
        <ul class="nav navbar-right navbar-nav">
          <li v-if="hasNewVersion">
            <button
              type="button"
              class="btn btn-blue btn-blue-nb btn-reload"
              @click="reload"
            >
              {{ system }} обновилась! Перезагрузить страницу
            </button>
          </li>
          <li v-else>
            <span class="navbar-brand org-title"> Организация: {{ user_hospital_title || $orgTitle() }} </span>
          </li>
          <ChatsButton v-if="chatsEnabled" />
        </ul>
      </div>
    </div>
    <div
      v-show="loading"
      class="nav-loader center"
    >
      <div class="navbar-header">
        <div
          class="navbar-left logo"
          :class="l2LogoClass"
        >
          <template v-if="asVI">
            {{ system }}
          </template>
          <template v-else>
            L<sup>2</sup>
          </template>
        </div>
        <span
          v-if="authenticated"
          class="navbar-brand"
        >
          <small>{{ fio_short }}</small>
        </span>
        <span
          v-else
          class="navbar-brand"
        >
          <small class="page-title">{{ metaTitle }}</small>
        </span>
      </div>
      <div class="din-spinner">
        <div class="sk-fading-circle">
          <div class="sk-circle1 sk-circle" />
          <div class="sk-circle2 sk-circle" />
          <div class="sk-circle3 sk-circle" />
          <div class="sk-circle4 sk-circle" />
          <div class="sk-circle5 sk-circle" />
          <div class="sk-circle6 sk-circle" />
          <div class="sk-circle7 sk-circle" />
          <div class="sk-circle8 sk-circle" />
          <div class="sk-circle9 sk-circle" />
          <div class="sk-circle10 sk-circle" />
          <div class="sk-circle11 sk-circle" />
          <div class="sk-circle12 sk-circle" />
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
import shiftModal from '@/ui-cards/ShiftModal.vue';

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
    shiftModal,
    NavbarDropdownContent,
    CardReader: () => import('@/ui-cards/CardReader.vue'),
    ExtendedPatientSearch: () => import('@/ui-cards/ExtendedPatientSearch/index.vue'),
    CreateDescriptiveDirection: () => import('@/ui-cards/CreateDescriptiveDirection.vue'),
    ExpertiseStatus: () => import('@/ui-cards/ExpertiseStatus.vue'),
    RmisLink: () => import('@/ui-cards/RmisLink.vue'),
    Favorites: () => import('@/ui-cards/Favorites.vue'),
    PrintQueue: () => import('@/ui-cards/PrintQueue.vue'),
    HelpLinkField: () => import('@/ui-cards/HelpLinkField.vue'),
    OperationPlans: () => import('@/ui-cards/OperationPlans.vue'),
    LaboratoryHeader: () => import('@/ui-cards/LaboratoryHeader.vue'),
    LaboratorySelector: () => import('@/ui-cards/LaboratorySelector.vue'),
    ChatsButton: () => import('@/ui-cards/ChatsButton.vue'),
    EcpSchedule: () => import('@/ui-cards/EcpSchedule.vue'),
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

  get system() {
    return this.$systemTitle();
  }

  get asVI() {
    return this.$asVI();
  }

  get l2LogoClass() {
    return this.$l2LogoClass();
  }

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

  get chatsEnabled() {
    return this.$store.getters.chatsEnabled;
  }

  get l2CashEnabled() {
    return this.$store.getters.modules.l2_cash;
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
