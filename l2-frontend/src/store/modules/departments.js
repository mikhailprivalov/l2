import departments_directory from '../../api/departments-directory'
import * as types from '../mutation-types'

const state = {
  all: [],
  old_all: [],
  can_edit: false,
  types: []
}

const getters = {
  allDepartments: state => state.all,
  oldDepartments: state => state.old_all,
}

const actions = {
  async getAllDepartments({commit}) {
    const departments = await departments_directory.getDepartments()
    commit(types.UPDATE_DEPARTMENTS, {departments})
    commit(types.UPDATE_OLD_DEPARTMENTS, {departments})
  }
}

const mutations = {
  [types.UPDATE_DEPARTMENTS](state, {departments}) {
    state.all = departments
  },
  [types.UPDATE_OLD_DEPARTMENTS](state, {departments}) {
    state.old_all = departments
  },
}

export default {
  state,
  getters,
  actions,
  mutations,
}
