import Vue from 'vue'
import Vuex from 'vuex'
import departments from './modules/departments'
import cards from './modules/cards'
import directory from './modules/directory'
import user from './modules/user'

Vue.use(Vuex)

export default new Vuex.Store({
  modules: {
    departments,
    cards,
    directory,
    user
  }
})
