import user_point from '../../api/user-point';
import * as mutation_types from '../mutation-types';
import * as actionsTypes from '../action-types';

const stateInitial = {
  data: {
    modules: {},
  },
  directive_from: [],
};

const getters = {
  user_data: (state) => state.data,
  ex_dep: (state) => state.data.extended_departments || [],
  directive_from: (state) => state.directive_from,
  modules: (state) => state.data.modules || {},
};

const actions = {
  async [actionsTypes.GET_USER_DATA]({ commit }) {
    const data = await user_point.getCurrentUserInfo();
    commit(mutation_types.SET_USER_DATA, { data });
  },
  async [actionsTypes.GET_DIRECTIVE_FROM]({ commit }) {
    const { data: directive_from } = await user_point.getDirectiveFrom();
    commit(mutation_types.SET_DIRECTIVE_FROM, { directive_from });
  },
};

const mutations = {
  [mutation_types.SET_USER_DATA](state, { data }) {
    state.data = data;
  },
  [mutation_types.SET_DIRECTIVE_FROM](state, { directive_from }) {
    state.directive_from = directive_from;
  },
};

export default {
  state: stateInitial,
  getters,
  mutations,
  actions,
};
