import departments_directory from '../../api/departments-directory'
import * as mutation_types from '../mutation-types'
import _ from 'lodash'
import * as action_types from '../action-types'

const state = {
  all: [],
  old_all: [],
  can_edit: false,
  department_types: []
}

const getters = {
  allDepartments: state => state.all,
  oldDepartments: state => state.old_all,
  diff_departments: state => {
    let diff = []
    let departments = state.all
    for (let row of departments) {
      for (let in_row of state.old_all) {
        if (in_row.pk === row.pk) {
          if (in_row.title !== row.title) {
            diff.push(row)
          }
          break
        }
      }
    }
    return diff
  },
  canEditDepartments: state => state.can_edit,
  allTypes: state => state.department_types,
}

const actions = {
  async [action_types.GET_ALL_DEPARTMENTS]({commit}) {
    const answer = await departments_directory.getDepartments()
    let departments = answer.departments
    commit(mutation_types.UPDATE_DEPARTMENTS, {departments})
    commit(mutation_types.UPDATE_OLD_DEPARTMENTS, {departments})
    commit(mutation_types.SET_CAN_EDIT, {can_edit: answer.can_edit})
    commit(mutation_types.SET_TYPES, {department_types: answer.types})
  },

  async [action_types.UPDATE_DEPARTMENTS]({commit, getters}, type_update, to_update) {
    to_update = to_update || getters.diff_departments
    type_update = type_update || 'update'
    if (to_update.length === 0)
      return []
    try {
      const answer = await departments_directory.sendDepartments(type_update, to_update)
      if (answer.ok) {
        return to_update
      }
      commit(mutation_types.UPDATE_OLD_DEPARTMENTS, {departments: getters.allDepartments})
    } catch (e) {
      return []
    }
  }
}

const mutations = {
  [mutation_types.UPDATE_DEPARTMENTS](state, {departments}) {
    state.all = departments
  },
  [mutation_types.UPDATE_OLD_DEPARTMENTS](state, {departments}) {
    state.old_all = JSON.parse(JSON.stringify(departments))
  },
  [mutation_types.SET_CAN_EDIT](state, {can_edit}) {
    state.can_edit = can_edit
  },
  [mutation_types.SET_TYPES](state, {department_types}) {
    state.department_types = department_types
  },
  [mutation_types.SET_UPDATED_DEPARTMENT](state, {pk, value}) {
    for (let i = 0; i < state.all; i++) {
      if (state.all.pk === pk) {
        state.all[i].updated = value
      }
    }
  },
}

export default {
  state,
  getters,
  actions,
  mutations,
}
