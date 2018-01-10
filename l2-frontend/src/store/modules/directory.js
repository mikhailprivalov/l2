import researches_point from '../../api/researches-point'
import * as mutation_types from '../mutation-types'
import * as action_types from '../action-types'

const state = {
  templates: [],
  templates_loaded: false,
  researches: {},
  researches_loaded: false,
}

const getters = {
  templates: state => state.templates,
  researches: state => state.researches,
}

const actions = {
  async [action_types.GET_TEMPLATES]({commit}) {
    const answer = await researches_point.getTemplates()
    let templates = answer.templates
    commit(mutation_types.UPDATE_TEMPLATES, {templates})
    let templates_loaded = true
    commit(mutation_types.SET_TEMPLATES_LOADED, {templates_loaded})
  },
  async [action_types.GET_RESEARCHES]({commit}) {
    const answer = await researches_point.getResearches()
    let researches = answer.researches
    commit(mutation_types.UPDATE_RESEARCHES, {researches})
  },
}

const mutations = {
  [mutation_types.UPDATE_TEMPLATES](state, {templates}) {
    state.templates = templates
  },
  [mutation_types.SET_TEMPLATES_LOADED](state, {templates_loaded}) {
    state.templates_loaded = templates_loaded
  },
  [mutation_types.UPDATE_RESEARCHES](state, {researches}) {
    state.researches = researches
  },
}

export default {
  state,
  getters,
  mutations,
  actions,
}
