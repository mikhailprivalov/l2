import Vue from 'vue'
import Vuex from 'vuex'
import departments from './modules/departments'
import cards from './modules/cards'

Vue.use(Vuex)

export default new Vuex.Store({
  modules: {
    departments,
    cards
  }
})
