import Vue from 'vue'
import VueTippy from 'vue-tippy'
import store from './store'
import * as action_types from './store/action-types'
import * as mutation_types from './store/mutation-types'
import directions_point from './api/directions-point'
import { Steps, Step } from 'element-ui'
import 'element-ui/lib/theme-chalk/steps.css'
import 'element-ui/lib/theme-chalk/step.css'
import 'element-ui/lib/theme-chalk/icon.css'
import VueAutosize from 'vue-autosize';
const VueInputMask = require('vue-inputmask').default;
import VuejsDialog from 'vuejs-dialog';
import 'vuejs-dialog/dist/vuejs-dialog.min.css';
import ReplaceAppendModal from './ReplaceAppendModal';

Vue.use(VuejsDialog, {
    okText: 'Подтвердить',
    cancelText: 'Отмена',
    animation: 'fade'
});
Vue.use(VueAutosize)
Vue.use(VueTippy)
Vue.use(Steps)
Vue.use(Step)
Vue.use(VueInputMask)

const promiseFinally = require('promise.prototype.finally');
Vue.dialog.registerComponent('replace-append-modal', ReplaceAppendModal);
promiseFinally.shim()

new Vue({
  el: '#app',
  store,
  components: {
    'JournalGetMaterialModal': () => import('./JournalGetMaterialModal'),
    'StatisticsTicketsPrintModal': () => import('./StatisticsTicketsPrintModal'),
    'DepartmentsForm': () => import('./DepartmentsForm'),
    'Directions': () => import('./Directions'),
    'Cases': () => import('./pages/Cases'),
    'ConstructParaclinic': () => import('./construct/ConstructParaclinic'),
    'ConstructTemplates': () => import('./construct/ConstructTemplates'),
    'ResultsParaclinic': () => import('./ResultsParaclinic'),
    'StatisticsTickets': () => import('./StatisticsTickets'),
    'DirectionVisit': () => import('./DirectionVisit'),
    'ResultsReport': () => import('./ResultsReport'),
    'RmqManagement': () => import('./RmqManagement'),
    'DirectionSteps': () => import('./DirectionSteps'),
    'RmisConfirm': () => import('./RmisConfirm'),
    // loading,
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
    let vm = this
    this.$store.watch((state) => (state.departments.all), () => {
      let diff = vm.$store.getters.diff_departments
      vm.$store.dispatch(action_types.UPDATE_DEPARTMENTS, {type_update: 'update', to_update: diff}).then((ok) => {
        if (Array.isArray(ok) && ok.length > 0) {
          for (let r of ok) {
            vm.$store.commit(mutation_types.SET_UPDATED_DEPARTMENT, {pk: r.pk, value: true})
            if (vm.timeouts.hasOwnProperty(r.pk) && vm.timeouts[r.pk] !== null) {
              clearTimeout(vm.timeouts[r.pk])
              vm.timeouts[r.pk] = null
            }
            vm.timeouts[r.pk] = (function (vm, r) {
              return setTimeout(() => {
                vm.$store.commit(mutation_types.SET_UPDATED_DEPARTMENT, {pk: r.pk, value: false})
                vm.timeouts[r.pk] = null
              }, 2000)
            })(vm, r)
          }
        }
      })
    }, {deep: true})

    vm.$store.dispatch(action_types.INC_LOADING).then()
    this.$store.dispatch(action_types.GET_ALL_DEPARTMENTS).then(() => {
      vm.$store.dispatch(action_types.DEC_LOADING).then()
    })

    vm.$store.dispatch(action_types.INC_LOADING).then()
    this.$store.dispatch(action_types.GET_BASES).then(() => {
      vm.$store.dispatch(action_types.DEC_LOADING).then()
    })

    vm.$store.dispatch(action_types.INC_LOADING).then()
    this.$store.dispatch(action_types.GET_USER_DATA).then(() => {
      vm.$store.dispatch(action_types.DEC_LOADING).then()
    })

    function printForm(tpl, pks) {
      if (!pks || pks.length === 0) {
        return;
      }
      window.open(tpl.replace('{pks}', JSON.stringify(pks)), '_blank')
    }

    this.$root.$on('print:directions', (pks) => printForm('/directions/pdf?napr_id={pks}', pks))
    this.$root.$on('print:directions:contract', (pks) => printForm('/directions/pdf?napr_id={pks}&contract=1', pks))

    this.$root.$on('print:barcodes', (pks) => printForm('/barcodes/tubes?napr_id={pks}', pks))

    this.$root.$on('print:results', (pks) => printForm('/results/preview?pk={pks}', pks))

    this.$root.$on('print:directions_list', (pks) => printForm('/statistic/xls?pk={pks}&type=directions_list', pks))

    this.$root.$on('generate-directions', ({type, card_pk, fin_source_pk, diagnos, base, researches, operator, ofname, history_num, comments, for_rmis, rmis_data, callback, vich_code, count, discount, need_contract}) => {
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
      if (operator && ofname === -1) {
        errmessage('Не выбрано, от чьего имени выписываются направления')
        return
      }
      if (!operator && history_num !== '')
        history_num = ''
      vm.$store.dispatch(action_types.INC_LOADING).then()
      directions_point.sendDirections(card_pk, diagnos, fin_source_pk, history_num, ofname, researches, comments, for_rmis, rmis_data, vich_code, count, discount).then(data => {
        vm.$store.dispatch(action_types.DEC_LOADING).then()

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
          this.$root.$emit('researches-picker:clear_all')
          this.$root.$emit('researches-picker:directions_created')
        } else {
          errmessage('Направления не созданы', data.message)
        }
        if (callback)
          callback()
      })
    })
  }
})
