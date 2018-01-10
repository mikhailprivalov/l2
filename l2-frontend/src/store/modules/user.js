import user_point from '../../api/user-point'
import * as mutation_types from '../mutation-types'
import * as action_types from '../action-types'

const state = {
  data: {},
}

const getters = {
  user_data: state => state.data,
}

const actions = {
  async [action_types.GET_USER_DATA]({commit}) {
    const data = await user_point.getCurrentUserInfo()
    commit(mutation_types.SET_USER_DATA, {data})
  },
}

const mutations = {
  [mutation_types.SET_USER_DATA](state, {data}) {
    state.data = data
  },
}

export default {
  state,
  getters,
  mutations,
  actions,
}
