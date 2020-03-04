import departments_directory from '../../api/departments-directory'
import * as mutation_types from '../mutation-types'
import * as action_types from '../action-types'

const state = {
  all: [],
  old_all: [],
  can_edit: false,
  department_types: []
}

const getters = {
  allDepartments: state => state.all || [],
  oldDepartments: state => state.old_all || [],
  diff_departments: (state, getters) => {
    let diff = []
    for (let row of getters.allDepartments) {
      for (let in_row of getters.oldDepartments) {
        if (in_row.pk === row.pk) {
          if (in_row.title !== row.title || in_row.type !== row.type) {
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
  okDep: state => state.department_types.length > 0,
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

  async [action_types.UPDATE_DEPARTMENTS]({commit, getters}, {type_update, to_update}) {
    const data = to_update || getters.diff_departments
    const type = type_update || 'update'
    if (type === 'update') {
      if (data.length === 0)
        return []
      try {
        const answer = await departments_directory.sendDepartments(null, null, {
          type,
          data,
        })
        commit(mutation_types.UPDATE_OLD_DEPARTMENTS, {departments: getters.allDepartments})
        if (answer.ok) {
          return data
        }
      } catch (e) {
        // console.log(e)
      }
      return []
    } else if (type === 'insert') {
      try {
        const answer = await departments_directory.sendDepartments(null, null, {
          type,
          data,
        })
        return answer.ok
      } catch (e) {
        // console.log(e)
      }
      return false
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
  [mutation_types.SET_UPDATED_DEPARTMENT](state, data) {
    for (let i = 0; i < state.all.length; i++) {
      if (state.all[i].pk === data.pk) {
        state.all[i].updated = data.value
        break
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
