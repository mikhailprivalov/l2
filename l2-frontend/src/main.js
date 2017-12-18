import Vue from 'vue'
import JournalGetMaterialModal from './JournalGetMaterialModal'
import DepartmentsForm from './DepartmentsForm'
import ResearchesPicker from './ResearchesPicker'
import store from './store'
import * as action_types from './store/action-types'
import * as mutation_types from './store/mutation-types'

new Vue({
  el: '#app',
  store,
  components: {JournalGetMaterialModal, DepartmentsForm, ResearchesPicker},
  data: {
    timeouts: {},
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
    this.$store.dispatch(action_types.GET_ALL_DEPARTMENTS).then()
  }
})
