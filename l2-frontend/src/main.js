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
    this.$store.watch((state) => (state.departments.all), (departments) => {
      let diff = []
      for (let row of departments) {
        for (let in_row of this.$store.departments.old_all) {
          console.log(in_row.pk, row.pk, in_row.pk === row.pk, in_row.title, row.title, in_row.title !== row.title)
          if (in_row.pk === row.pk) {
            if (in_row.title !== row.title) {
              diff.push(row)
            }
            break
          }
        }
      }
      console.log(diff)
      this.$store.commit(types.UPDATE_OLD_DEPARTMENTS, {departments})
    }, {deep: true})
    this.$store.dispatch('getAllDepartments').then()
  }
})
