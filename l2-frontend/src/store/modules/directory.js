import researches_point from '../../api/researches-point'
import * as mutation_types from '../mutation-types'
import * as action_types from '../action-types'

const state = {
  templates: [],
  templates_loaded: false,
  researches: {},
  tubes: {},
  researches_loaded: false,
}

const getters = {
  templates: state => state.templates,
  researches: state => state.researches,
  tubes: state => state.tubes,
  researches_obj: function (state) {
    let o = {}
    for (let k in state.researches) {
      if (state.researches.hasOwnProperty(k)) {
        for (let r of state.researches[k]) {
          o[r.pk] = r
        }
      }
    }
    return o
  }
}

const actions = {
  async [action_types.GET_TEMPLATES]({commit, state}) {
    if (state.templates_loaded) {
      return
    }
    const answer = await researches_point.getTemplates()
    let templates = answer.templates
    commit(mutation_types.UPDATE_TEMPLATES, {templates})
    let templates_loaded = true
    commit(mutation_types.SET_TEMPLATES_LOADED, {templates_loaded})
  },
  async [action_types.GET_RESEARCHES]({commit, state}) {
    if (state.researches_loaded) {
      return
    }
    const answer = await researches_point.getResearches()
    let researches = answer.researches
    let tubes = answer.tubes
    commit(mutation_types.UPDATE_RESEARCHES, {researches})
    commit(mutation_types.UPDATE_TUBES, {tubes})
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
    state.researches_loaded = true
  },
  [mutation_types.UPDATE_TUBES](state, {tubes}) {
    state.tubes = tubes
  },
}

export default {
  state,
  getters,
  mutations,
  actions,
}
