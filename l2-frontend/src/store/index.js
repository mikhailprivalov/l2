import Vue from 'vue'
import Vuex from 'vuex'
import departments from './modules/departments'
import cards from './modules/cards'
import directory from './modules/directory'
import user from './modules/user'
import * as action_types from './action-types'
import * as mutation_types from './mutation-types'

Vue.use(Vuex)

export default new Vuex.Store({
  modules: {
    departments,
    cards,
    directory,
    user
  },
  state: {
    inLoading: false,
    loadingCounter: 0,
    loadingLabel: ''
  },
  actions: {
    async [action_types.ENABLE_LOADING]({commit}, {loadingLabel}) {
      commit(mutation_types.SET_LOADING, {inLoading: true, loadingLabel: loadingLabel || 'Загрузка...'})
    },
    async [action_types.INC_LOADING]({commit, state}) {
      commit(mutation_types.SET_LOADING_COUNTER, {loadingCounter: state.loadingCounter + 1})
    },
    async [action_types.DISABLE_LOADING]({commit}) {
      commit(mutation_types.SET_LOADING, {inLoading: false, loadingLabel: 'Загрузка...'})
    },
    async [action_types.DEC_LOADING]({commit, state}) {
      commit(mutation_types.SET_LOADING_COUNTER, {loadingCounter: state.loadingCounter - 1})
    },
  },
  mutations: {
    [mutation_types.SET_LOADING](state, {inLoading, loadingLabel}) {
      state.inLoading = inLoading
      state.loadingLabel = loadingLabel
    },
    [mutation_types.SET_LOADING_COUNTER](state, {loadingCounter}) {
      state.loadingCounter = Math.max(0, loadingCounter)
      if (state.loadingCounter > 0) {
        state.inLoading = true
        state.loadingLabel = 'Загрузка...'
      }
      else {
        state.inLoading = false
        state.loadingLabel = 'Загрузка...'
      }
    },
  },
  getters: {
    inLoading: state => state.inLoading,
    loadingLabel: state => state.loadingLabel,
    loadingCounter: state => state.loadingCounter,
  }
})
