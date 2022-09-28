import api from '@/api';
import departmentsDirectory from '@/api/departments-directory';

import * as mutationTypes from '../mutation-types';
import * as actionsTypes from '../action-types';

const stateInitial = {
  all: [],
  can_edit: false,
  department_types: [],
  hospitals: [],
};

const getters = {
  hospitals: (state) => state.hospitals || [],
  all_hospitals_with_none: (state, g) => [
    ...(g.hospitals.find(x => x.id === -1) ? [] : [{ id: -1, label: 'Общие' }]),
    ...g.hospitals,
  ],
  hospitalsById: (state, g) => g.hospitals.reduce((a, b) => ({ ...a, [b.id]: b }), {}),
  allDepartments: (state) => state.all || [],
  canEditDepartments: (state) => state.can_edit,
  allTypes: (state) => state.department_types,
  okDep: (state) => state.department_types.length > 0,
};

const actions = {
  async [actionsTypes.GET_ALL_DEPARTMENTS]({ commit, state }, { lazy = false } = {}) {
    if (lazy && state.all && state.all.length > 0) {
      return;
    }
    const answer = await departmentsDirectory.getDepartments({ method: 'GET' });
    const { departments } = answer;
    commit(mutationTypes.UPDATE_DEPARTMENTS, { departments });
    commit(mutationTypes.UPDATE_OLD_DEPARTMENTS, { departments });
    commit(mutationTypes.SET_CAN_EDIT, { can_edit: answer.can_edit });
    commit(mutationTypes.SET_TYPES, { department_types: answer.types });
  },
  async [actionsTypes.LOAD_HOSPITALS]({ commit, state }, { lazy = false } = {}) {
    if (lazy && state.hospitals && state.hospitals.length > 0) {
      return;
    }
    const data = await api('hospitals');
    commit(mutationTypes.SET_HOSPITALS, data);
  },
};

const mutations = {
  [mutationTypes.SET_HOSPITALS](state, { hospitals }) {
    state.hospitals = hospitals;
  },
  [mutationTypes.UPDATE_DEPARTMENTS](state, { departments }) {
    state.all = departments;
  },
  [mutationTypes.UPDATE_OLD_DEPARTMENTS](state, { departments }) {
    state.old_all = JSON.parse(JSON.stringify(departments));
  },
  [mutationTypes.SET_CAN_EDIT](state, { can_edit: canEdit }) {
    state.can_edit = canEdit;
  },
  [mutationTypes.SET_TYPES](state, { department_types: types }) {
    state.department_types = types;
  },
  [mutationTypes.SET_UPDATED_DEPARTMENT](state, data) {
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
