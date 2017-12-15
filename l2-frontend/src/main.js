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
    this.$store.watch((state) => (state.departments.all), () => {
      vm.$store.dispatch('updateDepartments').then()
    }, {deep: true})
    this.$store.dispatch('getAllDepartments').then()
  }
})
