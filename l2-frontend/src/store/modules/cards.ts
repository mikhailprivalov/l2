import { Base } from '@/types/cards';
import cardsPoint from '@/api/cards-point';

import * as mutationTypes from '../mutation-types';
import * as actionsTypes from '../action-types';

interface CardsState {
  bases: Base[],
}

const stateInitial: CardsState = {
  bases: [],
};

const getters = {
  bases: (state: CardsState) => state.bases,
};

const actions = {
  async [actionsTypes.GET_BASES]({ commit, state }, { lazy = false } = {}) {
    if (lazy && state.bases && state.bases.length > 0) {
      return;
    }
    const answer = await cardsPoint.getBases();
    const { bases } = answer;
    commit(mutationTypes.UPDATE_BASES, { bases });
  },
};

const mutations = {
  [mutationTypes.UPDATE_BASES](state, { bases }) {
    state.bases = bases;
  },
};

export default {
  state: stateInitial,
  getters,
  mutations,
  actions,
};
