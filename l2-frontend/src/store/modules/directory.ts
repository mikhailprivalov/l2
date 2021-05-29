import researchesPoint from '../../api/researches-point';
import * as mutation_types from '../mutation-types';
import * as actionsTypes from '../action-types';

const stateInitial = {
  templates: [],
  templates_loaded: false,
  researches: {},
  tubes: {},
  researches_loaded: false,
};

const getters = {
  templates: (state) => state.templates,
  researches: (state) => state.researches,
  tubes: (state) => state.tubes,
  researches_obj(state) {
    const o = {};
    for (const k of Object.keys(state.researches)) {
      for (const r of state.researches[k]) {
        o[r.pk] = r;
      }
    }
    return o;
  },
};

const actions = {
  async [actionsTypes.GET_TEMPLATES]({ commit, state }) {
    if (state.templates_loaded) {
      return;
    }
    const answer = await researchesPoint.getTemplates();
    const { templates } = answer;
    commit(mutation_types.UPDATE_TEMPLATES, { templates });
    const templates_loaded = true;
    commit(mutation_types.SET_TEMPLATES_LOADED, { templates_loaded });
  },
  async [actionsTypes.GET_RESEARCHES]({ commit, state }) {
    if (state.researches_loaded) {
      return;
    }
    const answer = await researchesPoint.getResearches();
    const { researches } = answer;
    const { tubes } = answer;
    commit(mutation_types.UPDATE_RESEARCHES, { researches });
    commit(mutation_types.UPDATE_TUBES, { tubes });
  },
};

const mutations = {
  [mutation_types.UPDATE_TEMPLATES](state, { templates }) {
    state.templates = templates;
  },
  [mutation_types.SET_TEMPLATES_LOADED](state, { templates_loaded }) {
    state.templates_loaded = templates_loaded;
  },
  [mutation_types.UPDATE_RESEARCHES](state, { researches }) {
    state.researches = researches;
    state.researches_loaded = true;
  },
  [mutation_types.UPDATE_TUBES](state, { tubes }) {
    state.tubes = tubes;
  },
};

export default {
  state: stateInitial,
  getters,
  mutations,
  actions,
};
