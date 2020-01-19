import cards_point from '../../api/cards-point'
import * as mutation_types from '../mutation-types'
import * as action_types from '../action-types'

const state = {
  bases: []
}

const getters = {
  bases: state => state.bases
}

const actions = {
  async [action_types.GET_BASES]({commit}) {
    const answer = await cards_point.getBases()
    let bases = answer.bases
    commit(mutation_types.UPDATE_BASES, {bases})
  },
}

const mutations = {
  [mutation_types.UPDATE_BASES](state, {bases}) {
    state.bases = bases
  },
}

export default {
  state,
  getters,
  mutations,
  actions,
}
