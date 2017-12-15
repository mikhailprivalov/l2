import Vue from 'vue'
import JournalGetMaterialModal from './JournalGetMaterialModal.vue'
import DepartmentsForm from './DepartmentsForm.vue'
import store from './store'
import * as types from './store/mutation-types'

new Vue({
  el: '#app',
  store,
  components: {JournalGetMaterialModal, DepartmentsForm},
  created() {
    let vm = this
    this.$store.watch((state) => (state.departments.all), (departments) => {
      let diff = []
      for (let row of departments) {
        for (let in_row of vm.$store.getters.oldDepartments) {
          if (in_row.pk === row.pk) {
            if (in_row.title !== row.title) {
              diff.push(row)
            }
            break
          }
        }
      }
      console.log(departments)
      console.log(vm.$store.getters.oldDepartments)
      console.log(diff)
      vm.$store.commit(types.UPDATE_OLD_DEPARTMENTS, {departments})
    }, {deep: true})
    this.$store.dispatch('getAllDepartments').then()
  }
})
