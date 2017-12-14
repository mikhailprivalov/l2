import departments_directory from '../../api/departments-directory'
import * as types from '../mutation-types'

const state = {
  all: []
}

const getters = {
  allDepartments: state => state.all
}

const actions = {
  async getAllDepartments({commit}) {
    const departments = await departments_directory.getDepartments()
    console.log(departments)
    // commit(types.RECEIVE_ALL_DEPARTMENTS, {departments})
  }
}

const mutations = {
  [types.RECEIVE_ALL_DEPARTMENTS](state, {departments}) {
    state.all = departments
  },
}

export default {
  state,
  getters,
  actions,
  mutations
}
