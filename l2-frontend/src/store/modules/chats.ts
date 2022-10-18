import api from '@/api';
import * as mutationTypes from '@/store/mutation-types';
import * as actionsTypes from '@/store/action-types';
import { ChatsDepartment } from '@/types/chats';

interface ChatsState {
  departments: ChatsDepartment[],
  loading: boolean,
  dialogsOpenedList: number[],
  initied: boolean,
  unreadMessages: number,
  totalMessages: number,
  notifyToken: string | null,
}

const stateInitial: ChatsState = {
  departments: [],
  loading: false,
  dialogsOpenedList: [],
  initied: false,
  unreadMessages: 0,
  totalMessages: 0,
  notifyToken: null,
};

const getters = {
  chatsDepartments: (state: ChatsState) => state.departments || [],
  // eslint-disable-next-line @typescript-eslint/no-unused-vars,max-len
  chatsEnabled: (_, __, ___, rootGetters) => Boolean(rootGetters.modules.l2_chats && rootGetters.authenticated),
  chatsLoading: (state: ChatsState) => state.loading,
  chatsDialogsOpened: (state: ChatsState) => state.dialogsOpenedList || [],
  chatsUnreadMessages: (state: ChatsState) => state.unreadMessages || 0,
  chatsGetUserDepartmentTitle: (state: ChatsState) => (userId: number) => {
    const department = state.departments.find(d => d.users.some(u => u.id === userId));
    return department ? department.title : '';
  },
  chatsGetUser: (state: ChatsState) => (userId: number) => {
    const department = state.departments.find((d) => d.users.find((u) => u.id === userId));
    if (!department) {
      return null;
    }
    const user = department.users.find((u) => u.id === userId);
    if (!user) {
      return null;
    }
    return user;
  },
  chatsGetUserIsOnline: (state: ChatsState, g) => (userId: number) => {
    const user = g.chatsGetUser(userId);
    if (!user) {
      return false;
    }
    return user.isOnline;
  },
  chatsNotifyToken: (state: ChatsState) => state.notifyToken,
};

const actions = {
  async [actionsTypes.CHATS_LOAD_DEPARTMENTS]({
    commit, getters: g, dispatch,
  }) {
    if (!g.chatsEnabled) {
      return;
    }
    try {
      commit(mutationTypes.CHATS_SET_LOADING, true);
      const { departments } = await api('chats/get-users-for-hospital');
      if (departments) {
        commit(mutationTypes.CHATS_SET_DEPARTMENTS, { departments });
      }
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error(e);
    }
    commit(mutationTypes.CHATS_SET_LOADING, false);

    await new Promise((resolve) => {
      setTimeout(resolve, 60000);
    });

    dispatch(actionsTypes.CHATS_LOAD_DEPARTMENTS);
  },
  async [actionsTypes.CHATS_MESSAGES_COUNT]({
    commit, getters: g, dispatch,
  }) {
    if (g.chatsEnabled && !g.chatsNotifyToken) {
      await dispatch(actionsTypes.CHATS_GET_NOTIFY_TOKEN);
    }
    if (!g.chatsEnabled || !g.chatsNotifyToken) {
      return;
    }
    try {
      const {
        unreadMessages, totalMessages, notifications, newToken,
      } = await api('chats/get-messages-count', {
        notifyToken: g.chatsNotifyToken,
      });
      commit(mutationTypes.CHATS_SET_MESSAGES_COUNT, { unreadMessages, totalMessages });
      if (notifications) {
        for (const notification of notifications) {
          dispatch(actionsTypes.CHATS_NOTIFY, notification);
        }
      }
      if (newToken !== g.chatsNotifyToken) {
        commit(mutationTypes.CHATS_SET_NOTIFY_TOKEN, newToken);
      }
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error(e);
    }

    await new Promise((resolve) => {
      setTimeout(resolve, 8000);
    });

    dispatch(actionsTypes.CHATS_MESSAGES_COUNT);
  },
  async [actionsTypes.CHATS_OPEN_DIALOG]({ commit }, userId) {
    const { dialogId } = await api('chats/get-dialog-id', { userId });

    commit(mutationTypes.CHATS_OPEN_DIALOG, { dialogId });
  },
  async [actionsTypes.CHATS_OPEN_DIALOG_BY_ID]({ commit }, { dialogId }) {
    commit(mutationTypes.CHATS_OPEN_DIALOG, { dialogId });
  },
  [actionsTypes.CHATS_CLOSE_DIALOG]({ commit }, dialogId) {
    commit(mutationTypes.CHATS_CLOSE_DIALOG, { dialogId });
  },
  [actionsTypes.CHATS_CLEAR_STATE]({ commit }) {
    commit(mutationTypes.CHATS_CLEAR_STATE);
  },
  async [actionsTypes.CHATS_GET_NOTIFY_TOKEN]({ commit, getters: g }) {
    if (!g.chatsEnabled) {
      return;
    }
    try {
      const { notifyToken } = await api('chats/get-notify-token');
      commit(mutationTypes.CHATS_SET_NOTIFY_TOKEN, { notifyToken });
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error(e);
    }
  },
  [actionsTypes.CHATS_NOTIFY]() {
    // empty
  },
};

const mutations = {
  [mutationTypes.CHATS_SET_DEPARTMENTS](state, { departments }) {
    state.departments = departments;
  },
  [mutationTypes.CHATS_SET_LOADING](state, loading) {
    state.loading = loading;
  },
  [mutationTypes.CHATS_OPEN_DIALOG](state, { dialogId }) {
    if (!state.dialogsOpenedList.includes(dialogId)) {
      state.dialogsOpenedList.push(dialogId);
    }
  },
  [mutationTypes.CHATS_CLOSE_DIALOG](state, { dialogId }) {
    state.dialogsOpenedList = state.dialogsOpenedList.filter((id) => id !== dialogId);
  },
  [mutationTypes.CHATS_CLEAR_STATE](state) {
    state.departments = [];
    state.dialogsOpenedList = [];
    state.unreadMessages = 0;
    state.totalMessages = 0;
    state.notifyToken = null;
  },
  [mutationTypes.CHATS_SET_MESSAGES_COUNT](state, { unreadMessages, totalMessages }) {
    state.unreadMessages = unreadMessages || 0;
    state.totalMessages = totalMessages || 0;
  },
  [mutationTypes.CHATS_SET_NOTIFY_TOKEN](state, { notifyToken }) {
    state.notifyToken = notifyToken;
  },
};

export default {
  state: stateInitial,
  getters,
  mutations,
  actions,
};
