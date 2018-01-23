import Vue from 'vue'
import store from './store'
import * as action_types from './store/action-types'
import * as mutation_types from './store/mutation-types'
import directions_point from './api/directions-point'

new Vue({
  el: '#app',
  store,
  components: {
    'JournalGetMaterialModal': () => import('./JournalGetMaterialModal'),
    'DepartmentsForm': () => import('./DepartmentsForm'),
    'Directions': () => import('./Directions'),
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

    this.$root.$on('generate-directions', ({type, card_pk, fin_source_pk, diagnos, base, researches, operator, ofname, history_num}) => {
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
      directions_point.sendDirections(card_pk, diagnos, fin_source_pk, history_num, ofname, researches, {}).then(data => {
        vm.$store.dispatch(action_types.DEC_LOADING).then()

        if (data.ok) {
          if (type === 'direction') {
            window.open('/directions/pdf?napr_id=' + JSON.stringify(data.directions), '_blank')
          }
          if (type === 'barcode') {
            window.open('/barcodes/tubes?napr_id=' + JSON.stringify(data.directions), '_blank')
          }
          if (type === 'just-save' || type === 'barcode') {
            okmessage('Направления созданы', 'Номера: ' + data.directions.join(', '))
          }
          this.$root.$emit('researches-picker:clear_all')
        } else {
          errmessage('Направления не созданы', data.message)
        }
      })
    })
  }
})
