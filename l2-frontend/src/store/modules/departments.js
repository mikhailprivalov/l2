import departments_directory from '../../api/departments-directory'
import * as types from '../mutation-types'

const state = {
  all: [],
  can_edit: false,
  types: []
}

const getters = {
  allDepartments: state => state.all
}

const actions = {
  async getAllDepartments({commit}) {
    const departments = await departments_directory.getDepartments()
    commit(types.RECEIVE_ALL_DEPARTMENTS, {departments})
  }
}

const mutations = {
  [types.RECEIVE_ALL_DEPARTMENTS](state, {departments}) {
    state.all = departments
  },
}

const watch = {
  all: {
    deep: true,
    handler: function (val, oldVal) {
      console.log(val, oldVal)
    }
  }
}

export default {
  state,
  getters,
  actions,
  mutations,
  watch
}
