import * as mutationTypes from '@/store/mutation-types';
import * as actionsTypes from '@/store/action-types';

export type Id = number | string;
type IdOptional = Id | null;

type EditStateCommon = {
  openEdit: boolean,
  editId: IdOptional,
  formType: string | null,
  filters: Record<string, any> | null,
};

type EditState = EditStateCommon & {
  editStack: EditStateCommon[],
  prevEditId: IdOptional,
  initiator?: string,
};

interface EditOpenAction {
  editId: IdOptional,
  formType: string,
  filters: Record<string, any>,
  initiator?: string,
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
  filters: {},
  editStack: [],
  prevEditId: null,
  initiator: null,
};

const getters = {
  editOpened: (state: EditState) => state.openEdit,
  editId: (state: EditState) => state.editId,
  editFormType: (state: EditState) => state.formType,
  editFilters: (state: EditState) => state.filters,
  editStack: (state: EditState) => state.editStack,
  editStackHasFormType: (state: EditState) => (formType: string) => state.editStack.some((s) => s.formType === formType),
  editInitiator: (state: EditState) => state.initiator,
  editPrevEditId: (state: EditState) => state.prevEditId,
};

const actions = {
  [actionsTypes.EDIT_OPEN]({ commit }, {
    editId, formType, filters, initiator,
  }: EditOpenAction) {
    commit(mutationTypes.EDIT_SET_STATE, {
      openEdit: true,
      editId,
      formType,
      filters,
      initiator,
    });
  },
  [actionsTypes.EDIT_HIDE]({ commit }) {
    commit(mutationTypes.EDIT_CLEAR_STATE);
  },
  [actionsTypes.EDIT_SAVED_OBJECT]({ getters: g, commit }, info: SavedObjectPayload) {
    if (g.editStack.length) {
      if (info.result?.id) {
        commit(mutationTypes.SET_PREV_EDIT_ID, info.result.id);
      }
    }
  },
};

const mutations = {
  [mutationTypes.EDIT_SET_STATE](state, {
    openEdit, editId, formType, filters, initiator,
  }: EditState) {
    if (state.openEdit) {
      state.editStack.push({
        openEdit: state.openEdit,
        editId: state.editId,
        formType: state.formType,
        filters: state.filters,
        initiator: initiator || null,
      });
    }
    state.openEdit = openEdit;
    state.editId = editId;
    state.formType = formType;
    state.filters = filters || {};
  },
  [mutationTypes.EDIT_CLEAR_STATE](state) {
    if (state.editStack.length) {
      const lastState = state.editStack.pop();
      if (lastState) {
        state.openEdit = lastState.openEdit;
        state.editId = lastState.editId;
        state.formType = lastState.formType;
        state.filters = lastState.filters;
        state.initiator = lastState.initiator || null;
        return;
      }
    }
    state.openEdit = false;
    state.editId = null;
    state.formType = null;
    state.prevEditId = null;
    state.filters = {};
    state.initiator = null;
  },
  [mutationTypes.SET_PREV_EDIT_ID](state, id: IdOptional) {
    state.prevEditId = id;
  },
};

export default {
  state: stateInitial,
  getters,
  mutations,
  actions,
};
