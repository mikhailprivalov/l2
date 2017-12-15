import Vue from 'vue'
import JournalGetMaterialModal from './JournalGetMaterialModal.vue'
import DepartmentsForm from './DepartmentsForm.vue'
import store from './store'
import * as action_types from './store/action-types'
import * as mutation_types from './store/mutation-types'

new Vue({
  el: '#app',
  store,
  components: {JournalGetMaterialModal, DepartmentsForm},
  data: {
    timeouts: {}
  },
  created() {
    let vm = this
    this.$store.watch((state) => (state.departments.all), () => {
      let diff = vm.$store.getters.diff_departments
      vm.$store.dispatch(action_types.UPDATE_DEPARTMENTS, 'update', diff).then((ok) => {
        if (Array.isArray(ok) && ok.length > 0) {
          for (let r of ok) {
            vm.$store.commit(mutation_types.SET_UPDATED_DEPARTMENT, {pk: r.pk, value: true})
            if (vm.timeouts.hasOwnProperty(r.pk) && vm.timeouts[r.pk] !== null) {
              clearTimeout(vm.timeouts[r.pk])
              vm.timeouts[r.pk] = null
            }
            vm.timeouts[r.pk] = setTimeout(() => {
              vm.$store.commit(mutation_types.SET_UPDATED_DEPARTMENT, {pk: r.pk, value: false})
              vm.timeouts[r.pk] = null
            }, 2000)
          }
        }
      })
    }, {deep: true})
    this.$store.dispatch(action_types.GET_ALL_DEPARTMENTS).then()
  }
})
