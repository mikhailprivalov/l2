import Vue from 'vue';
import Vuex from 'vuex';
import departments from './modules/departments';
import cards from './modules/cards';
import directory from './modules/directory';
import user from './modules/user';
import * as action_types from './action-types';
import * as mutation_types from './mutation-types';

Vue.use(Vuex);

export default new Vuex.Store({
  modules: {
    departments,
    cards,
    directory,
    user,
  },
  state: {
    inLoading: false,
    loaderInHeader: true,
    loadingCounter: 0,
    loadingLabel: '',
    showMenuAnesthesiaStatus: false,
  },
  actions: {
    async [action_types.ENABLE_LOADING]({ commit }, { loadingLabel }) {
      commit(mutation_types.SET_LOADING, { inLoading: true, loadingLabel: loadingLabel || 'Загрузка...' });
    },
    async [action_types.INC_LOADING]({ commit, state }) {
      commit(mutation_types.SET_LOADING_COUNTER, { loadingCounter: state.loadingCounter + 1 });
    },
    async [action_types.DISABLE_LOADING]({ commit }) {
      commit(mutation_types.SET_LOADING, { inLoading: false, loadingLabel: 'Загрузка...' });
    },
    async [action_types.DEC_LOADING]({ commit, state }) {
      commit(mutation_types.SET_LOADING_COUNTER, { loadingCounter: state.loadingCounter - 1 });
    },
    async [action_types.SET_LOADER_IN_HEADER]({ commit }, status) {
      commit(mutation_types.SET_LOADER_IN_HEADER, { loaderInHeader: Boolean(status) });
    },
    async [action_types.CHANGE_STATUS_MENU_ANESTHESIA]({ commit }) {
      commit(mutation_types.TOGGLE_ANESTHESIA_MENU_SHOW);
    },
  },
  mutations: {
    [mutation_types.SET_LOADING](state, { inLoading, loadingLabel }) {
      state.inLoading = inLoading;
      state.loadingLabel = loadingLabel;
    },
    [mutation_types.SET_LOADING_COUNTER](state, { loadingCounter }) {
      state.loadingCounter = Math.max(0, loadingCounter);
      state.inLoading = state.loadingCounter > 0;
      state.loadingLabel = 'Загрузка';
    },
    [mutation_types.SET_LOADER_IN_HEADER](state, { loaderInHeader }) {
      state.loaderInHeader = loaderInHeader;
    },
    [mutation_types.TOGGLE_ANESTHESIA_MENU_SHOW](state) {
      state.showMenuAnesthesiaStatus = !state.showMenuAnesthesiaStatus;
    },
  },
  getters: {
    inLoading: (state) => state.inLoading,
    loaderInHeader: (state) => state.loaderInHeader,
    loadingLabel: (state) => state.loadingLabel,
    loadingCounter: (state) => state.loadingCounter,
  },
});
