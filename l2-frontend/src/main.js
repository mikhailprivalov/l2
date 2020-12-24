import Vue from 'vue'

import VueAutosize from 'vue-autosize';
import VueCollapse from 'vue2-collapse'
import Fragment from 'vue-fragment'
import VuejsDialog from 'vuejs-dialog';
import VueTippy from './vue-tippy-2.1.3/dist/vue-tippy.min'

import store from './store'
import * as action_types from './store/action-types'
import directions_point from './api/directions-point'

import '@openfonts/open-sans_all';
import './styles/index.scss';

import ReplaceAppendModal from './ui-cards/ReplaceAppendModal';


const VueInputMask = require('vue-inputmask').default;

Vue.use(VuejsDialog, {
  okText: 'Подтвердить',
  cancelText: 'Отмена',
  animation: 'fade'
});
Vue.use(VueAutosize)
Vue.use(VueTippy)
Vue.use(VueInputMask)
Vue.use(VueCollapse)
Vue.use(Tippy)
Vue.use(Fragment.Plugin)

const promiseFinally = require('promise.prototype.finally');
Vue.dialog.registerComponent('replace-append-modal', ReplaceAppendModal);
promiseFinally.shim();


function printForm(tpl, pks) {
  if (!pks || pks.length === 0) {
    return;
  }
  window.open(tpl.replace('{pks}', JSON.stringify(pks)), '_blank')
}

const hosp = window.location.href.includes('/stationar') ? 1 : 0;

new Vue({
  el: '#app',
  store,
  components: {
    'JournalGetMaterialModal': () => import('@/modals/JournalGetMaterialModal'),
    'StatisticsTicketsPrintModal': () => import('@/modals/StatisticsTicketsPrintModal'),
    'StatisticsResearchesPrintModal': () => import('@/modals/StatisticsResearchesPrintModal'),
    'DepartmentsForm': () => import('@/forms/DepartmentsForm'),
    'LaboratoryTune': () => import('@/forms/LaboratoryTune'),
    'Directions': () => import('@/pages/Directions'),
    'Cases': () => import('@/pages/Cases'),
    'ConstructParaclinic': () => import('@/construct/ConstructParaclinic'),
    'ConstructTemplates': () => import('@/construct/ConstructTemplates'),
    'ConstructBacteria': () => import('@/construct/ConstructBacteria'),
    'ConstructDispensaryPlan': () => import('@/construct/ConstructDispensaryPlan'),
    'ResultsParaclinic': () => import('@/pages/ResultsParaclinic'),
    'StatisticsTickets': () => import('@/pages/StatisticsTickets'),
    'DirectionVisit': () => import('@/pages/DirectionVisit'),
    'PlanOperations': () => import('@/pages/PlanOperations'),
    'ResultsDepartment': () => import('@/pages/ResultsDepartment'),
    'ResultsReport': () => import('@/pages/ResultsReport'),
    'Favorites': () => import('@/ui-cards/Favorites'),
    'OperationPlans': () => import('@/ui-cards/OperationPlans'),
    'CardReader': () => import('@/ui-cards/CardReader'),
    'RmisConfirm': () => import('@/pages/RmisConfirm'),
    'Profiles': () => import('@/pages/Profiles'),
    'EmployeeJobs': () => import('@/pages/EmployeeJobs'),
    'Stationar': () => import('@/pages/Stationar'),
    'DocCall': () => import('@/pages/DocCall'),
    'ListWait': () => import('@/pages/ListWait'),
    'LoadFile': () => import('@/ui-cards/LoadFile'),
  },
  data: {
    timeouts: {},
  },
  computed: {
    inLoading() {
      return this.$store.getters.inLoading
    },
    loadingLabel() {
      return this.$store.getters.loadingLabel
    }
  },
  watch: {
    inLoading(n, o) {
      if (n && !o) {
        sl()
      }
      if (!n && o) {
        hl()
      }
    }
  },
  created() {
    Promise.all([
      this.$store.dispatch(action_types.INC_LOADING),
      this.$store.dispatch(action_types.GET_ALL_DEPARTMENTS),
      this.$store.dispatch(action_types.GET_BASES),
      this.$store.dispatch(action_types.GET_USER_DATA),
      this.$store.dispatch(action_types.LOAD_HOSPITALS),
    ]).then(() => {
      this.$store.dispatch(action_types.DEC_LOADING)
    })

    this.$root.$on('print:directions', (pks) => printForm('/directions/pdf?napr_id={pks}', pks))
    this.$root.$on('print:hosp', (pks) => printForm('/barcodes/hosp?napr_id={pks}', pks))
    this.$root.$on('print:directions:contract', (pks) => printForm('/directions/pdf?napr_id={pks}&contract=1', pks))

    this.$root.$on('print:barcodes', (pks) => printForm('/barcodes/tubes?napr_id={pks}', pks))
    this.$root.$on('print:barcodes:iss', (pks) => printForm('/barcodes/tubes?iss_ids={pks}', pks))

    this.$root.$on('print:results', (pks) => printForm(`/results/preview?pk={pks}&hosp=${hosp}`, pks))
    this.$root.$on('print:directions_list', (pks) => printForm('/statistic/xls?pk={pks}&type=directions_list', pks))

    this.$root.$on('generate-directions', ({
                                             type, card_pk, fin_source_pk, diagnos, base,
                                             researches, operator, ofname, history_num, comments,
                                             counts, for_rmis, rmis_data, callback, vich_code, count,
                                             discount, need_contract,
                                             parent_iss = null, kk = '', localizations = {}, service_locations = {},
                                             direction_purpose = 'NONE', directions_count = 1,
                                             external_organization = 'NONE', parent_slave_hosp = null,
                                           }) => {
      if (card_pk === -1) {
        errmessage('Не выбрана карта')
        return
      }
      if (fin_source_pk === -1) {
        errmessage('Не выбран источник финансирования')
        return
      }
      if (Object.keys(researches).length === 0) {
        errmessage('Не выбраны исследования')
        return
      }
      if (operator && ofname < 0) {
        errmessage('Не выбрано, от чьего имени выписываются направления')
        return
      }
      this.$store.dispatch(action_types.INC_LOADING)
      directions_point.sendDirections({
        card_pk, diagnos, fin_source: fin_source_pk, history_num,
        ofname_pk: ofname, researches, comments, for_rmis,
        rmis_data, vich_code, count, discount, parent_iss, counts, localizations, service_locations,
        direction_purpose, directions_count, external_organization, parent_slave_hosp,
      }).then(data => {
        this.$store.dispatch(action_types.DEC_LOADING)

        if (data.ok) {
          if (type === 'direction') {
            if (need_contract) {
              this.$root.$emit('print:directions:contract', data.directions)
            } else {
              this.$root.$emit('print:directions', data.directions)
            }
          }
          if (type === 'barcode') {
            this.$root.$emit('print:barcodes', data.directions)
          }
          if (type === 'just-save' || type === 'barcode') {
            okmessage('Направления созданы', 'Номера: ' + data.directions.join(', '))
          }
          this.$root.$emit('researches-picker:clear_all' + kk)
          this.$root.$emit('researches-picker:directions_created' + kk)
        } else {
          errmessage('Направления не созданы', data.message)
        }
        if (callback)
          callback()
      })
    })
  }
});
