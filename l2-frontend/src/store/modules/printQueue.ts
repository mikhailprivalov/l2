import { setLocalStorageDataJson } from '@/utils';

import * as mutationTypes from '../mutation-types';
import * as actionsTypes from '../action-types';

const stateInitial = {
  currentPrintQueue: [],
};

const getters = {
  printQueueCount: (state) => state.currentPrintQueue.length,
  idInQueue: state => id => state.currentPrintQueue.includes(id),
};

const actions = {
  async [actionsTypes.PRINT_QUEUE_INIT]({ commit }) {
    commit(mutationTypes.PRINT_QUEUE_INIT);
  },
  async [actionsTypes.PRINT_QUEUE_ADD_ELEMENT]({ commit }, { id }) {
    commit(mutationTypes.PRINT_QUEUE_ADD_ELEMENT, { id });
  },
  async [actionsTypes.PRINT_QUEUE_DEL_ELEMENT]({ commit }, { id }) {
    commit(mutationTypes.PRINT_QUEUE_DEL_ELEMENT, { id });
  },
};

const mutations = {
  [mutationTypes.PRINT_QUEUE_INIT](state) {
    try {
      const queue = JSON.parse(localStorage.getItem('queue'));
      if (Array.isArray(queue)) {
        state.currentPrintQueue = queue;
      } else {
        setLocalStorageDataJson('queue', state.currentPrintQueue);
      }
    } catch (e) {
      state.currentPrintQueue = [];
      setLocalStorageDataJson('queue', state.currentPrintQueue);
    }
  },
  [mutationTypes.PRINT_QUEUE_ADD_ELEMENT](state, { id }) {
    if (!getters.idInQueue(id)) {
      state.currentPrintQueue = [...state.currentPrintQueue, id];
      setLocalStorageDataJson('queue', state.currentPrintQueue);
    }
  },
  [mutationTypes.PRINT_QUEUE_DEL_ELEMENT](state, { id }) {
    const i = state.currentPrintQueue.indexOf(id);
    if (i >= 0) {
      state.currentPrintQueue.splice(i, 1);
      setLocalStorageDataJson('queue', state.currentPrintQueue);
    }
  },
};

export default {
  state: stateInitial,
  getters,
  mutations,
  actions,
};
