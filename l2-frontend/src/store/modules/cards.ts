import { Base } from '@/types/cards';
import cards_point from '../../api/cards-point';
import * as mutation_types from '../mutation-types';
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
    const answer = await cards_point.getBases();
    const { bases } = answer;
    commit(mutation_types.UPDATE_BASES, { bases });
  },
};

const mutations = {
  [mutation_types.UPDATE_BASES](state, { bases }) {
    state.bases = bases;
  },
};

export default {
  state: stateInitial,
  getters,
  mutations,
  actions,
};
