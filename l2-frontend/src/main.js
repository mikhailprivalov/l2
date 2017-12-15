import Vue from 'vue'
import JournalGetMaterialModal from './JournalGetMaterialModal.vue'
import DepartmentsForm from './DepartmentsForm.vue'
import store from './store'
import * as action_types from './store/action-types'

new Vue({
  el: '#app',
  store,
  components: {JournalGetMaterialModal, DepartmentsForm},
  created() {
    let vm = this
    this.$store.watch((state) => (state.departments.all), () => {
      let diff = vm.$store.getters.diff_departments
      /*vm.$store.dispatch(action_types.UPDATE_DEPARTMENTS, 'update', diff).then((ok) => {
        if (Array.isArray(ok) && ok.length > 0) {

        }
      })*/
      if (diff.length > 0 && diff[0].title !== 'test') {
        diff[0].title = 'test'
      }
    }, {deep: true})
    this.$store.dispatch(action_types.GET_ALL_DEPARTMENTS).then()
  }
})
