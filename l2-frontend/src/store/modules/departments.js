import api from '@/api';
import departments_directory from '@/api/departments-directory';
import * as mutation_types from '../mutation-types';
import * as actionsTypes from '../action-types';

const stateInitial = {
  all: [],
  can_edit: false,
  department_types: [],
  hospitals: [],
};

const getters = {
  hospitals: (state) => state.hospitals || [],
  all_hospitals_with_none: (state, g) => [{ id: -1, label: 'Общие' }, ...g.hospitals],
  hospitalsById: (state, g) => g.hospitals.reduce((a, b) => ({ ...a, [b.id]: b }), {}),
  allDepartments: (state) => state.all || [],
  canEditDepartments: (state) => state.can_edit,
  allTypes: (state) => state.department_types,
  okDep: (state) => state.department_types.length > 0,
};

const actions = {
  async [actionsTypes.GET_ALL_DEPARTMENTS]({ commit }) {
    const answer = await departments_directory.getDepartments({ method: 'GET' });
    const { departments } = answer;
    commit(mutation_types.UPDATE_DEPARTMENTS, { departments });
    commit(mutation_types.UPDATE_OLD_DEPARTMENTS, { departments });
    commit(mutation_types.SET_CAN_EDIT, { can_edit: answer.can_edit });
    commit(mutation_types.SET_TYPES, { department_types: answer.types });
  },
  async [actionsTypes.LOAD_HOSPITALS]({ commit }) {
    const data = await api('hospitals');
    commit(mutation_types.SET_HOSPITALS, data);
  },
};

const mutations = {
  [mutation_types.SET_HOSPITALS](state, { hospitals }) {
    state.hospitals = hospitals;
  },
  [mutation_types.UPDATE_DEPARTMENTS](state, { departments }) {
    state.all = departments;
  },
  [mutation_types.UPDATE_OLD_DEPARTMENTS](state, { departments }) {
    state.old_all = JSON.parse(JSON.stringify(departments));
  },
  [mutation_types.SET_CAN_EDIT](state, { can_edit }) {
    state.can_edit = can_edit;
  },
  [mutation_types.SET_TYPES](state, { department_types }) {
    state.department_types = department_types;
  },
  [mutation_types.SET_UPDATED_DEPARTMENT](state, data) {
    for (let i = 0; i < state.all.length; i++) {
      if (state.all[i].pk === data.pk) {
        state.all[i].updated = data.value;
        break;
      }
    }
  },
};

export default {
  state: stateInitial,
  getters,
  actions,
  mutations,
};
