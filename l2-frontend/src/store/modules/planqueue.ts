import * as mutationTypes from '../mutation-types';
import * as actionsTypes from '../action-types';

const stateInitial = {
  currentPrintQueue: JSON.parse(localStorage.getItem('planQueue')),
};

const getters = {
  statusPrintQueue: (state) => state.currentPrintQueue || [],
};

const actions = {
  async [actionsTypes.PRINT_QUEUE_ADD_ELEMENT]({ commit }, { id }) {
    commit(mutationTypes.PRINT_QUEUE_ADD_ELEMENT, { id });
  },
  async [actionsTypes.PRINT_QUEUE_DEL_ELEMENT]({ commit }, { id }) {
    commit(mutationTypes.PRINT_QUEUE_DEL_ELEMENT, { id });
  },
  async [actionsTypes.PRINT_QUEUE_FLUSH]({ commit }) {
    commit(mutationTypes.PRINT_QUEUE_FLUSH);
  },
};

const mutations = {
  [mutationTypes.PRINT_QUEUE_ADD_ELEMENT](state, { id }) {
    if (state.currentPrintQueue === null) {
      state.currentPrintQueue = [id];
    } else if (!state.currentPrintQueue.includes(id)) {
      state.currentPrintQueue = [...state.currentPrintQueue, id];
    }
    window.localStorage.setItem('planQueue', JSON.stringify(state.currentPrintQueue));
  },
  [mutationTypes.PRINT_QUEUE_DEL_ELEMENT](state, { id }) {
    const i = state.currentPrintQueue.indexOf(id);
    if (i >= 0) {
      state.currentPrintQueue.splice(i, 1);
      window.localStorage.setItem('planQueue', JSON.stringify(state.currentPrintQueue));
    }
  },
  [mutationTypes.PRINT_QUEUE_FLUSH](state) {
    state.currentPrintQueue = [];
    window.localStorage.removeItem('planQueue');
  },
};

export default {
  state: stateInitial,
  getters,
  mutations,
  actions,
};
