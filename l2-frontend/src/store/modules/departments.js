import departments_directory from '../../api/departments-directory'
import * as types from '../mutation-types'
import _ from 'lodash'

const state = {
  all: [],
  old_all: [],
  can_edit: false,
  department_types: []
}

const getters = {
  allDepartments: state => state.all,
  oldDepartments: state => state.old_all,
  canEditDepartments: state => state.can_edit,
  allTypes: state => state.department_types,
}

const actions = {
  async getAllDepartments({commit}) {
    const answer = await departments_directory.getDepartments()
    let departments = answer.departments
    commit(types.UPDATE_DEPARTMENTS, {departments})
    commit(types.UPDATE_OLD_DEPARTMENTS, {departments})
    commit(types.SET_CAN_EDIT, {can_edit: answer.can_edit})
    commit(types.SET_TYPES, {department_types: answer.types})
  },
  updateDepartments: _.debounce(async ({commit, getters}) => {
    let diff = []
    let departments = getters.allDepartments
    for (let row of departments) {
      for (let in_row of getters.oldDepartments) {
        if (in_row.pk === row.pk) {
          if (in_row.title !== row.title) {
            diff.push(row)
          }
          break
        }
      }
    }
    if (diff.length === 0)
      return
    console.log(diff)
    try {
      const answer = await departments_directory.sendDepartments('update', diff)
      console.log(answer)
      commit(types.UPDATE_OLD_DEPARTMENTS, {departments})
    } catch (e) {

    }
  }, 650)
}

const mutations = {
  [types.UPDATE_DEPARTMENTS](state, {departments}) {
    state.all = departments
  },
  [types.UPDATE_OLD_DEPARTMENTS](state, {departments}) {
    state.old_all = JSON.parse(JSON.stringify(departments))
  },
  [types.SET_CAN_EDIT](state, {can_edit}) {
    state.can_edit = can_edit
  },
  [types.SET_TYPES](state, {department_types}) {
    state.department_types = department_types
  },
}

export default {
  state,
  getters,
  actions,
  mutations,
}
