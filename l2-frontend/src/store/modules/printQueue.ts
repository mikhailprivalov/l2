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
  stateCurrentPrintQueue: stata => stata.currentPrintQueue,
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
  async [actionsTypes.PRINT_QUEUE_CHANGE_ORDER]({ commit, dispatch }, { typeOrder, index }) {
    commit(mutationTypes.PRINT_QUEUE_CHANGE_ORDER, { typeOrder, index });
    dispatch(actionsTypes.PRINT_QUEUE_SAVE_LS);
  },
  async [actionsTypes.PRINT_QUEUE_FLUSH]({ commit, dispatch }) {
    commit(mutationTypes.PRINT_QUEUE_FLUSH);
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
    const addsIds = [];
    for (const el of id) {
      if (!getters.idInQueue(state)(el)) {
        addsIds.push(el);
      }
    }
    state.currentPrintQueue = [...state.currentPrintQueue, ...addsIds];
  },
  [mutationTypes.PRINT_QUEUE_CHANGE_ORDER](state, { typeOrder, index }) {
    const tmp = state.currentPrintQueue[index];
    if (typeOrder === 'down') {
      state.currentPrintQueue[index] = state.currentPrintQueue[index + 1];
      state.currentPrintQueue[index + 1] = tmp;
    } else {
      state.currentPrintQueue[index] = state.currentPrintQueue[index - 1];
      state.currentPrintQueue[index - 1] = tmp;
    }
  },
  [mutationTypes.PRINT_QUEUE_DEL_ELEMENT](state, { id }) {
    state.currentPrintQueue = state.currentPrintQueue.filter(el => el !== id);
  },
  [mutationTypes.PRINT_QUEUE_FLUSH](state) {
    state.currentPrintQueue = [];
  },
};

export default {
  state: stateInitial,
  getters,
  mutations,
  actions,
};
