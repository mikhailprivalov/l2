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
            <small>{{ fioShort }}</small>
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
        <ul
          v-if="l2CashEnabled && meta.showShiftModal"
          class="nav navbar-nav"
        >
          <ShiftButton />
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
            <span class="navbar-brand org-title"> Организация: {{ userHospitalTitle || orgTitle }} </span>
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
          <small>{{ fioShort }}</small>
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

<script setup lang="ts">
import { computed, getCurrentInstance } from 'vue';

import { useStore } from '@/store';
import NavbarDropdownContent from '@/components/NavbarDropdownContent.vue';
import ShiftButton from '@/ui-cards/CashRegisters/ShiftButton.vue';

const CardReader = () => import('@/ui-cards/CardReader.vue');
const ExtendedPatientSearch = () => import('@/ui-cards/ExtendedPatientSearch/index.vue');
const CreateDescriptiveDirection = () => import('@/ui-cards/CreateDescriptiveDirection.vue');
const ExpertiseStatus = () => import('@/ui-cards/ExpertiseStatus.vue');
const RmisLink = () => import('@/ui-cards/RmisLink.vue');
const Favorites = () => import('@/ui-cards/Favorites.vue');
const PrintQueue = () => import('@/ui-cards/PrintQueue.vue');
const HelpLinkField = () => import('@/ui-cards/HelpLinkField.vue');
const OperationPlans = () => import('@/ui-cards/OperationPlans.vue');
const LaboratoryHeader = () => import('@/ui-cards/LaboratoryHeader.vue');
const LaboratorySelector = () => import('@/ui-cards/LaboratorySelector.vue');
const ChatsButton = () => import('@/ui-cards/ChatsButton.vue');
const EcpSchedule = () => import('@/ui-cards/EcpSchedule.vue');

// eslint-disable-next-line @typescript-eslint/no-non-null-assertion
const instance = getCurrentInstance()!.proxy;
const store = useStore();
const route = instance.$route;

const authenticated = computed(() => store.getters.authenticated);
const inLoading = computed(() => store.getters.inLoading);
const loadingLabel = computed(() => store.getters.loadingLabel);
const loaderInHeader = computed(() => store.getters.loaderInHeader);
const fioShort = computed(() => store.getters.fio_short);
const userHospitalTitle = computed(() => store.getters.user_hospital_title);
const hasNewVersion = computed(() => store.getters.hasNewVersion);
const chatsEnabled = computed(() => store.getters.chatsEnabled);
const l2CashEnabled = computed(() => store.getters.modules.l2_cash);

const orgTitle = instance.$orgTitle();
const system = instance.$systemTitle();
const asVI = instance.$asVI();
const l2LogoClass = instance.$l2LogoClass();

const meta = computed(() => route.meta || {});
const metaTitle = computed(() => String(route.meta?.title || ''));
const loading = computed(() => inLoading.value && loaderInHeader.value);
const loadingText = computed(() => (loadingLabel.value || 'Загрузка').toUpperCase());

function reload() {
  window.location.reload();
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
