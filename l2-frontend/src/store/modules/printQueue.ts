import { setLocalStorageDataJson } from '@/utils';

import * as mutationTypes from '../mutation-types';
import * as actionsTypes from '../action-types';

const PRINT_QUEUE_LS_KEY = 'printQueue';

const stateInitial = {
  currentPrintQueue: [],
};

const getters = {
  printQueueCount: (state) => state.currentPrintQueue.length,
  idInQueue: state => id => state.currentPrintQueue.includes(id),
};

const actions = {
  async [actionsTypes.PRINT_QUEUE_INIT]({ commit, dispatch }) {
    commit(mutationTypes.PRINT_QUEUE_REPLACE_STATE);
    dispatch(actionsTypes.PRINT_QUEUE_SAVE_LS);

    window.addEventListener('storage', (event) => {
      if (event.key === PRINT_QUEUE_LS_KEY) {
        commit(mutationTypes.PRINT_QUEUE_REPLACE_STATE);
      }
    });
  },
  async [actionsTypes.PRINT_QUEUE_ADD_ELEMENT]({ commit, dispatch }, { id }) {
    commit(mutationTypes.PRINT_QUEUE_ADD_ELEMENT, { id });
    dispatch(actionsTypes.PRINT_QUEUE_SAVE_LS);
  },
  async [actionsTypes.PRINT_QUEUE_DEL_ELEMENT]({ commit, dispatch }, { id }) {
    commit(mutationTypes.PRINT_QUEUE_DEL_ELEMENT, { id });
    dispatch(actionsTypes.PRINT_QUEUE_SAVE_LS);
  },
  async [actionsTypes.PRINT_QUEUE_SAVE_LS]({ state }) {
    setLocalStorageDataJson(PRINT_QUEUE_LS_KEY, state.currentPrintQueue);
  },
};

const mutations = {
  [mutationTypes.PRINT_QUEUE_REPLACE_STATE](state) {
    try {
      const queue = JSON.parse(localStorage.getItem(PRINT_QUEUE_LS_KEY));
      if (Array.isArray(queue)) {
        state.currentPrintQueue = queue;
      }
    } catch (e) {
      state.currentPrintQueue = [];
    }
  },
  [mutationTypes.PRINT_QUEUE_ADD_ELEMENT](state, { id }) {
    if (!getters.idInQueue(state)(id)) {
      state.currentPrintQueue = [...state.currentPrintQueue, id];
    }
  },
  [mutationTypes.PRINT_QUEUE_DEL_ELEMENT](state, { id }) {
    const i = state.currentPrintQueue.indexOf(id);
    if (i >= 0) {
      state.currentPrintQueue.splice(i, 1);
    }
  },
};

export default {
  state: stateInitial,
  getters,
  mutations,
  actions,
};
