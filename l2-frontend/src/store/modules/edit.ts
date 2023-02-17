import * as mutationTypes from '@/store/mutation-types';
import * as actionsTypes from '@/store/action-types';

export type Id = number | string;
type IdOptional = Id | null;

interface EditState {
  openEdit: boolean,
  editId: IdOptional,
  formType: string | null,
}

interface EditOpenAction {
  editId: IdOptional,
  formType: string,
}

export interface SavedObjectPayload {
  formType: string,
  id: Id,
  result: any,
}

const stateInitial: EditState = {
  openEdit: false,
  editId: null,
  formType: null,
};

const getters = {
  editOpened: (state: EditState) => state.openEdit,
  editId: (state: EditState) => state.editId,
  editFormType: (state: EditState) => state.formType,
};

const actions = {
  [actionsTypes.EDIT_OPEN]({ commit }, { editId, formType }: EditOpenAction) {
    commit(mutationTypes.EDIT_SET_STATE, {
      openEdit: true,
      editId,
      formType,
    });
  },
  [actionsTypes.EDIT_HIDE]({ commit }) {
    commit(mutationTypes.EDIT_CLEAR_STATE);
  },
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  [actionsTypes.EDIT_SAVED_OBJECT](_: any, info: SavedObjectPayload) {
    // empty
  },
};

const mutations = {
  [mutationTypes.EDIT_SET_STATE](state, {
    openEdit, editId, formType,
  }: EditState) {
    state.openEdit = openEdit;
    state.editId = editId;
    state.formType = formType;
  },
  [mutationTypes.EDIT_CLEAR_STATE](state) {
    state.openEdit = false;
    state.editId = null;
    state.formType = null;
  },
};

export default {
  state: stateInitial,
  getters,
  mutations,
  actions,
};
