import Vue from 'vue';

import store from './store';
// @ts-ignore
import * as actions from './store/action-types';

import './styles/index.scss';

import registerHooks from './registerHooks';
import registerVue from './registerVue';

registerVue();

// eslint-disable-next-line no-new
new Vue({
  el: '#app',
  store,
  components: {
    JournalGetMaterialModal: () => import('@/modals/JournalGetMaterialModal.vue'),
    StatisticsTicketsPrintModal: () => import('@/modals/StatisticsTicketsPrintModal.vue'),
    StatisticsResearchesPrintModal: () => import('@/modals/StatisticsResearchesPrintModal.vue'),
    StatisticsCompanyPrintModal: () => import('@/modals/StatisticsCompanyPrintModal.vue'),
    DepartmentsForm: () => import('@/forms/DepartmentsForm.vue'),
    LaboratoryTune: () => import('@/forms/LaboratoryTune.vue'),
    Cases: () => import('@/pages/Cases.vue'),
    ConstructParaclinic: () => import('@/construct/ConstructParaclinic.vue'),
    ConstructTemplates: () => import('@/construct/ConstructTemplates.vue'),
    ConstructBacteria: () => import('@/construct/ConstructBacteria.vue'),
    ConstructDispensaryPlan: () => import('@/construct/ConstructDispensaryPlan.vue'),
    ResultsParaclinic: () => import('@/pages/ResultsParaclinic.vue'),
    StatisticsTickets: () => import('@/pages/StatisticsTickets.vue'),
    DirectionVisit: () => import('@/pages/DirectionVisit.vue'),
    PlanOperations: () => import('@/pages/PlanOperations/index.vue'),
    ResultsReport: () => import('@/pages/ResultsReport.vue'),
    Favorites: () => import('@/ui-cards/Favorites.vue'),
    OperationPlans: () => import('@/ui-cards/OperationPlans.vue'),
    CardReader: () => import('@/ui-cards/CardReader.vue'),
    RmisConfirm: () => import('@/pages/RmisConfirm.vue'),
    Profiles: () => import('@/pages/Profiles.vue'),
    EmployeeJobs: () => import('@/pages/EmployeeJobs.vue'),
    Stationar: () => import('@/pages/Stationar/index.vue'),
    DocCall: () => import('@/pages/DocCall.vue'),
    ListWait: () => import('@/pages/ListWait.vue'),
    LoadFile: () => import('@/ui-cards/LoadFile.vue'),
    LaboratorySelector: () => import('@/ui-cards/LaboratorySelector.vue'),
    ExecutionList: () => import('@/ui-cards/ExecutionList.vue'),
    LaboratoryJournal: () => import('@/ui-cards/LaboratoryJournal.vue'),
    ExpertiseStatus: () => import('@/ui-cards/ExpertiseStatus.vue'),
    LaboratoryPrintResults: () => import('@/ui-cards/LaboratoryPrintResults.vue'),
    PlanPharmacotherapy: () => import('@/pages/PlanPharmacotherapy/index.vue'),
    LaboratoryResults: () => import('@/pages/LaboratoryResults/index.vue'),
  },
  data: {
    timeouts: {},
  },
  computed: {
    inLoading() {
      return this.$store.getters.inLoading;
    },
    loadingLabel() {
      return this.$store.getters.loadingLabel;
    },
    loaderInHeader() {
      return this.$store.getters.loaderInHeader;
    },
  },
  watch: {
    inLoading(n, o) {
      if (n && !o) {
        // @ts-ignore
        window.sl();
      }
      if (!n && o) {
        // @ts-ignore
        window.hl();
      }
    },
  },
  created() {
    Promise.all([
      this.$store.dispatch(actions.INC_LOADING),
      this.$store.dispatch(actions.GET_ALL_DEPARTMENTS),
      this.$store.dispatch(actions.GET_BASES),
      this.$store.dispatch(actions.GET_USER_DATA),
      this.$store.dispatch(actions.LOAD_HOSPITALS),
    ]).then(() => {
      this.$store.dispatch(actions.DEC_LOADING);
    });

    registerHooks(this);
  },
});
