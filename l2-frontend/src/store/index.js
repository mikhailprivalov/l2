import Vue from 'vue'
import departments from './modules/departments'
import Vuex from 'vuex/types/index'

Vue.use(Vuex)

export default new Vuex.Store({
  modules: {
    departments
  }
})
