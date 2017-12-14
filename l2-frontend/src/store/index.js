import Vue from 'vue'
import Vuex from 'vuex'
import departments from './modules/departments'

Vue.use(Vuex)

export default new Vuex.Store({
  modules: {
    departments
  }
})
