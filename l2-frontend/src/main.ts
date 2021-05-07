import Vue from 'vue';

import promiseFinally from 'promise.prototype.finally';
// @ts-ignore
import VueAutosize from 'vue-autosize';
// @ts-ignore
import VueCollapse from 'vue2-collapse';
// @ts-ignore
import frag from 'vue-frag';
// @ts-ignore
import VuejsDialog from 'vuejs-dialog';
import PortalVue from 'portal-vue';
// @ts-ignore
import Inputmask from 'inputmask';
// @ts-ignore
import VueTippy from './vue-tippy-2.1.3/dist/vue-tippy.min';

import store from './store';
// @ts-ignore
import * as actions from './store/action-types';
// @ts-ignore
import directionsPoint from './api/directions-point';

import './styles/index.scss';

import ReplaceAppendModal from './ui-cards/ReplaceAppendModal.vue';

const VueInputMask = {
  install(Vue$) {
    Vue$.directive('mask', {
      bind(el, binding) {
        Inputmask(binding.value).mask(el);
      },
    });
  },
};

Vue.directive('frag', frag);
Vue.use(VuejsDialog, {
  okText: 'Подтвердить',
  cancelText: 'Отмена',
  animation: 'fade',
});
Vue.use(VueAutosize);
Vue.use(VueTippy);
Vue.use(VueInputMask);
Vue.use(VueCollapse);
Vue.use(PortalVue);

Vue.directive('click-outside', {
  bind(el, binding, vnode) {
    // @ts-ignore
    // eslint-disable-next-line no-param-reassign
    el.clickOutsideEvent = function (event) {
      if (!(el === event.target || el.contains(event.target))) {
        // @ts-ignore
        vnode.context[binding.expression](event);
      }
    };
    // @ts-ignore
    document.body.addEventListener('click', el.clickOutsideEvent);
  },
  unbind(el) {
    // @ts-ignore
    document.body.removeEventListener('click', el.clickOutsideEvent);
  },
});

promiseFinally.shim();

// @ts-ignore
Vue.dialog.registerComponent('replace-append-modal', ReplaceAppendModal);

Vue.config.errorHandler = function (msg) {
  window.errmessage('Vue Error', String(msg));
};

Vue.config.warnHandler = function (msg) {
  window.wrnmessage('Vue Warning', msg);
};

function printForm(tpl: string, pks: number[]) {
  if (!pks || !Array.isArray(pks) || pks.length === 0) {
    return;
  }
  window.open(tpl.replace('{pks}', JSON.stringify(pks)), '_blank');
}

const hosp = window.location.href.includes('/stationar') ? 1 : 0;

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
    Directions: () => import('@/pages/Directions.vue'),
    Cases: () => import('@/pages/Cases.vue'),
    ConstructParaclinic: () => import('@/construct/ConstructParaclinic.vue'),
    ConstructTemplates: () => import('@/construct/ConstructTemplates.vue'),
    ConstructBacteria: () => import('@/construct/ConstructBacteria.vue'),
    ConstructDispensaryPlan: () => import('@/construct/ConstructDispensaryPlan.vue'),
    ResultsParaclinic: () => import('@/pages/ResultsParaclinic.vue'),
    StatisticsTickets: () => import('@/pages/StatisticsTickets.vue'),
    DirectionVisit: () => import('@/pages/DirectionVisit.vue'),
    PlanOperations: () => import('@/pages/PlanOperations/index.vue'),
    ResultsDepartment: () => import('@/pages/ResultsDepartment.vue'),
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
    LaboratoryPrintResults: () => import('@/ui-cards/LaboratoryPrintResults.vue'),
    CreateDescriptiveDirection: () => import('@/ui-cards/CreateDescriptiveDirection.vue'),
    RmisLink: () => import('@/ui-cards/RmisLink.vue'),
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

    // @ts-ignore
    this.$root.$on('no-loader-in-header', (status) => this.$store.dispatch(actions.SET_LOADER_IN_HEADER, !status));

    // @ts-ignore
    this.$root.$on('print:directions', (pks) => printForm('/directions/pdf?napr_id={pks}', pks));
    // @ts-ignore
    this.$root.$on('print:hosp', (pks) => printForm('/barcodes/hosp?napr_id={pks}', pks));
    // @ts-ignore
    this.$root.$on('print:directions:contract', (pks) => printForm('/directions/pdf?napr_id={pks}&contract=1', pks));

    // @ts-ignore
    this.$root.$on('print:barcodes', (pks) => printForm('/barcodes/tubes?napr_id={pks}', pks));
    // @ts-ignore
    this.$root.$on('print:barcodes:iss', (pks) => printForm('/barcodes/tubes?iss_ids={pks}', pks));

    // @ts-ignore
    this.$root.$on('print:results', (pks) => printForm(`/results/preview?pk={pks}&hosp=${hosp}`, pks));
    // @ts-ignore
    this.$root.$on('print:directions_list', (pks) => printForm('/statistic/xls?pk={pks}&type=directions_list', pks));

    // @ts-ignore
    this.$root.$on('generate-directions', ({
      type, card_pk: cardPk, fin_source_pk: finSourcePk, diagnos,
      researches, operator, ofname, history_num: historyNum, comments,
      counts, for_rmis: forRmis, rmis_data: rmisData, callback, vich_code: vichCode, count,
      discount, need_contract: needContract,
      parent_iss: parentIss = null, kk = '', localizations = {},
      service_locations: serviceLocations = {},
      direction_purpose: directionPurpose = 'NONE', directions_count: directionsCount = 1,
      external_organization: externalOrganization = 'NONE',
      parent_slave_hosp: parentSlaveHosp = null, direction_form_params: directionFormParams = {},
      current_global_direction_params: currentGlobalDirectionParams = {},
      hospital_department_override: hospitalDepartmentOverride = -1,
    }) => {
      if (cardPk === -1) {
        // @ts-ignore
        window.errmessage('Не выбрана карта');
        return;
      }
      if (finSourcePk === -1) {
        // @ts-ignore
        window.errmessage('Не выбран источник финансирования');
        return;
      }
      if (Object.keys(researches).length === 0) {
        // @ts-ignore
        window.errmessage('Не выбраны исследования');
        return;
      }
      if (operator && ofname < 0) {
        // @ts-ignore
        window.errmessage('Не выбрано, от чьего имени выписываются направления');
        return;
      }
      this.$store.dispatch(actions.INC_LOADING);
      directionsPoint.sendDirections({
        card_pk: cardPk,
        diagnos,
        fin_source: finSourcePk,
        history_num: historyNum,
        ofname_pk: ofname,
        researches,
        comments,
        for_rmis: forRmis,
        rmis_data: rmisData,
        vich_code: vichCode,
        count,
        discount,
        parent_iss: parentIss,
        counts,
        localizations,
        service_locations: serviceLocations,
        direction_purpose: directionPurpose,
        directions_count: directionsCount,
        external_organization: externalOrganization,
        parent_slave_hosp: parentSlaveHosp,
        direction_form_params: directionFormParams,
        current_global_direction_params: currentGlobalDirectionParams,
        hospital_department_override: hospitalDepartmentOverride,
      }).then((data) => {
        this.$store.dispatch(actions.DEC_LOADING);

        if (data.ok) {
          if (type === 'create_and_open') {
            this.$root.$emit('open-direction-form', data.directions[0]);
            // @ts-ignore
            window.okmessage('Направления создано', `Номер: ${data.directions[0]}`);
          } else if (type === 'direction') {
            if (needContract) {
              this.$root.$emit('print:directions:contract', data.directions);
            } else {
              this.$root.$emit('print:directions', data.directions);
            }
          } else if (type === 'barcode') {
            this.$root.$emit('print:barcodes', data.directions, data.directionsStationar);
          } else if (type === 'just-save' || type === 'barcode') {
            // @ts-ignore
            window.okmessage('Направления созданы', `Номера: ${data.directions.join(', ')}`);
          }
          this.$root.$emit(`researches-picker:clear_all${kk}`);
          this.$root.$emit(`researches-picker:directions_created${kk}`);
        } else {
          // @ts-ignore
          window.errmessage('Направления не созданы', data.message);
        }
        if (callback) callback();
      });
    });
  },
});
