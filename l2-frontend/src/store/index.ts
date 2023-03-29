import Vue from 'vue';
import Vuex from 'vuex';

import departments from './modules/departments';
import cards from './modules/cards';
import directory from './modules/directory';
import user from './modules/user';
import chats from './modules/chats';
import printQueue from './modules/printQueue';
import edit from './modules/edit';
import * as actions from './action-types';
import * as mutations from './mutation-types';

Vue.use(Vuex);

const store = new Vuex.Store({
  modules: {
    departments,
    cards,
    directory,
    user,
    chats,
    printQueue,
    edit,
  },
  state: {
    globalLoadingCounter: 0,
    inLoading: false,
    loaderInHeader: true,
    loadingCounter: 0,
    loadingLabel: '',
    showMenuAnesthesiaStatus: false,
  },
  actions: {
    async [actions.ENABLE_LOADING]({ commit }, { loadingLabel }) {
      commit(mutations.SET_LOADING, { inLoading: true, loadingLabel: loadingLabel || 'Загрузка...' });
    },
    async [actions.DISABLE_LOADING]({ commit }) {
      commit(mutations.SET_LOADING, { inLoading: false, loadingLabel: 'Загрузка...' });
    },
    async [actions.INC_LOADING]({ commit, state }) {
      commit(mutations.SET_LOADING_COUNTER, { loadingCounter: state.loadingCounter + 1 });
    },
    async [actions.DEC_LOADING]({ commit, state }) {
      commit(mutations.SET_LOADING_COUNTER, { loadingCounter: state.loadingCounter - 1 });
    },
    async [actions.RESET_LOADING]({ commit }) {
      commit(mutations.SET_LOADING_COUNTER, { loadingCounter: 0 });
    },
    async [actions.SET_LOADER_IN_HEADER]({ commit }, status) {
      commit(mutations.SET_LOADER_IN_HEADER, { loaderInHeader: Boolean(status) });
    },
    async [actions.INC_G_LOADING]({ commit, state }) {
      commit(mutations.SET_G_LOADING_COUNTER, { loadingCounter: state.globalLoadingCounter + 1 });
    },
    async [actions.DEC_G_LOADING]({ commit, state }) {
      commit(mutations.SET_G_LOADING_COUNTER, { loadingCounter: state.globalLoadingCounter - 1 });
    },
    async [actions.RESET_G_LOADING]({ commit }) {
      commit(mutations.SET_G_LOADING_COUNTER, { loadingCounter: 0 });
    },
    async [actions.CHANGE_STATUS_MENU_ANESTHESIA]({ commit }) {
      commit(mutations.TOGGLE_ANESTHESIA_MENU_SHOW);
    },
  },
  mutations: {
    [mutations.SET_LOADING](state, { inLoading, loadingLabel }) {
      state.inLoading = inLoading;
      state.loadingLabel = loadingLabel;
    },
    [mutations.SET_LOADING_COUNTER](state, { loadingCounter }) {
      state.loadingCounter = Math.max(0, loadingCounter);
      state.inLoading = state.loadingCounter > 0;
      state.loadingLabel = 'Загрузка';
    },
    [mutations.SET_G_LOADING_COUNTER](state, { loadingCounter }) {
      state.globalLoadingCounter = Math.max(0, loadingCounter);
    },
    [mutations.SET_LOADER_IN_HEADER](state, { loaderInHeader }) {
      state.loaderInHeader = loaderInHeader;
    },
    [mutations.TOGGLE_ANESTHESIA_MENU_SHOW](state) {
      state.showMenuAnesthesiaStatus = !state.showMenuAnesthesiaStatus;
    },
  },
  getters: {
    inLoading: (state) => state.inLoading,
    loaderInHeader: (state) => state.loaderInHeader,
    loadingLabel: (state) => state.loadingLabel,
    loadingCounter: (state) => state.loadingCounter,
    fullPageLoader: (state, getters) => getters.authenticateLoading || state.globalLoadingCounter,
  },
});

export default store;
export const useStore = () => store;
