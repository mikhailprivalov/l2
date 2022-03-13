import api from '../../api';
import researchesPoint from '../../api/researches-point';
import * as mutation_types from '../mutation-types';
import * as actionsTypes from '../action-types';

const stateInitial = {
  templates: [],
  templates_loaded: false,
  researches: {},
  tubes: {},
  researches_loaded: false,
  permanentDirectories: {},
  requiredStattalonFields: {},
  requiredStattalonFieldsLoaded: false,
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
  permanentDirectories: (state) => state.permanentDirectories,
  requiredStattalonFields: (state) => state.requiredStattalonFields,
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
  async [actionsTypes.LOAD_PERMANENT_DIRECTORY]({ commit, state }, { oid }) {
    if (state.permanentDirectories[oid]) {
      return;
    }
    const data = await api('permanent-directory', { oid });
    commit(mutation_types.SET_PERMANENT_DIRECTORY, { oid, data });
  },
  async [actionsTypes.LOAD_REQUIRED_STATTALON_FIELDS]({ commit, state }) {
    if (state.requiredStattalonFieldsLoaded) {
      return;
    }
    const answer = await researchesPoint.getRequiredStattalonFields();
    commit(mutation_types.SET_REQUIRED_STATTALON_FIELDS, { answer });
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
  [mutation_types.SET_PERMANENT_DIRECTORY](state, { oid, data }) {
    state.permanentDirectories = {
      ...state.permanentDirectories,
      [oid]: data,
    };
  },
  [mutation_types.SET_REQUIRED_STATTALON_FIELDS](state, { answer }) {
    state.requiredStattalonFields = answer;
    state.requiredStattalonFieldsLoaded = true;
  },
};

export default {
  state: stateInitial,
  getters,
  mutations,
  actions,
};
