import Vue from 'vue'
import JournalGetMaterialModal from './JournalGetMaterialModal.vue'
import DepartmentsForm from './DepartmentsForm.vue'
import store from './store'

new Vue({
  el: '#app',
  store,
  components: {JournalGetMaterialModal, DepartmentsForm},
  created() {
    this.$store.$watch((state) => (state.departments.all), (val, oldVal) => {
      console.log(val, oldVal)
    }, {deep: true})
    this.$store.dispatch('getAllDepartments').then()
  }
})
