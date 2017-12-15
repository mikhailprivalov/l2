import Vue from 'vue'
import JournalGetMaterialModal from './JournalGetMaterialModal.vue'
import DepartmentsForm from './DepartmentsForm.vue'
import store from './store'

new Vue({
  el: '#app',
  store,
  components: {JournalGetMaterialModal, DepartmentsForm},
  created() {
    this.$store.watch((state) => (state.departments.all), (val, oldVal) => {
      let diff = []
      for (let row of val) {
        for (let in_row of oldVal) {
          if (in_row.pk === row.pk) {
            if (in_row.title !== row.title) {
              diff.push(row)
            }
            break
          }
        }
      }
      console.log(diff)
    }, {deep: true})
    this.$store.dispatch('getAllDepartments').then()
  }
})
