import api from '@/api';
import researchesPoint from '@/api/researches-point';

import * as mutationTypes from '../mutation-types';
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
  researchesPkRequiredStattalonFields: [],
  researchesPkRequiredStattalonFieldsLoaded: false,
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
  researchesPkRequiredStattalonFields: (state) => state.researchesPkRequiredStattalonFields,
};

const actions = {
  async [actionsTypes.GET_TEMPLATES]({ commit, state }) {
    if (state.templates_loaded) {
      return;
    }
    const answer = await researchesPoint.getTemplates();
    const { templates } = answer;
    commit(mutationTypes.UPDATE_TEMPLATES, { templates });
    commit(mutationTypes.SET_TEMPLATES_LOADED, { templates_loaded: true });
  },
  async [actionsTypes.GET_RESEARCHES]({ commit, state }) {
    if (state.researches_loaded) {
      return;
    }
    const answer = await researchesPoint.getResearches();
    const { researches } = answer;
    const { tubes } = answer;
    commit(mutationTypes.UPDATE_RESEARCHES, { researches });
    commit(mutationTypes.UPDATE_TUBES, { tubes });
  },
  async [actionsTypes.GET_LAST_USED_RESEARCHES]({ commit }) {
    const answer = await researchesPoint.getLastUsedResearches();
    const { researches } = answer;
    commit(mutationTypes.ADD_RESEARCHES, { researches });
  },
  async [actionsTypes.LOAD_PERMANENT_DIRECTORY]({ commit, state }, { oid }) {
    if (state.permanentDirectories[oid]) {
      return;
    }
    const data = await api('permanent-directory', { oid });
    commit(mutationTypes.SET_PERMANENT_DIRECTORY, { oid, data });
  },
  async [actionsTypes.LOAD_REQUIRED_STATTALON_FIELDS]({ commit, state }) {
    if (state.requiredStattalonFieldsLoaded) {
      return;
    }
    const answer = await researchesPoint.getRequiredStattalonFields();
    commit(mutationTypes.SET_REQUIRED_STATTALON_FIELDS, { answer });
  },
  async [actionsTypes.LOAD_RESEARCHES_PK_REQUIRED_STATTALON_FIELDS]({ commit, state }) {
    if (state.researchesPkRequiredStattalonFieldsLoaded) {
      return;
    }
    const answer = await researchesPoint.getResearchesPkRequiredStattalonFields();
    commit(mutationTypes.SET_RESEARCHES_PK_REQUIRED_STATTALON_FIELDS, { answer });
  },
};

const mutations = {
  [mutationTypes.UPDATE_TEMPLATES](state, { templates }) {
    state.templates = templates;
  },
  [mutationTypes.SET_TEMPLATES_LOADED](state, { templates_loaded: tl }) {
    state.templates_loaded = tl;
  },
  [mutationTypes.UPDATE_RESEARCHES](state, { researches }) {
    state.researches = researches;
    state.researches_loaded = true;
  },
  [mutationTypes.ADD_RESEARCHES](state, { researches }) {
    state.researches = {
      ...state.researches,
      ...researches,
    };
    state.researches_loaded = true;
  },
  [mutationTypes.UPDATE_TUBES](state, { tubes }) {
    state.tubes = tubes;
  },
  [mutationTypes.SET_PERMANENT_DIRECTORY](state, { oid, data }) {
    state.permanentDirectories = {
      ...state.permanentDirectories,
      [oid]: data,
    };
  },
  [mutationTypes.SET_REQUIRED_STATTALON_FIELDS](state, { answer }) {
    state.requiredStattalonFields = answer;
    state.requiredStattalonFieldsLoaded = true;
  },
  [mutationTypes.SET_RESEARCHES_PK_REQUIRED_STATTALON_FIELDS](state, { answer }) {
    state.researchesPkRequiredStattalonFields = answer;
    state.researchesPkRequiredStattalonFieldsLoaded = true;
  },
};

export default {
  state: stateInitial,
  getters,
  mutations,
  actions,
};
