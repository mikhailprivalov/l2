import cards_point from '../../api/cards-point';
import * as mutation_types from '../mutation-types';
import * as actionsTypes from '../action-types';

const stateInitial = {
  bases: [],
};

const getters = {
  bases: (state) => state.bases,
};

const actions = {
  async [actionsTypes.GET_BASES]({ commit }) {
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
