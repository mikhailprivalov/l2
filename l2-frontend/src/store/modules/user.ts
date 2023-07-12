import { Menu } from '@/types/menu';
import userPoint from '@/api/user-point';

import * as mutationTypes from '../mutation-types';
import * as actionsTypes from '../action-types';

const SEMI_LAZY_INITIAL = 5;

const stateInitial = {
  semiLazyState: SEMI_LAZY_INITIAL,
  data: {
    auth: false,
    loading: true,
    modules: {},
    groups: [],
    hospital: null,
  },
  menu: {
    buttons: [],
    version: 'loading',
  },
  directive_from: [],
  hasNewVersion: false,
};

const getters = {
  user_data: state => state.data,
  fio_short: (state, g) => g.user_data?.shortFio ?? 'Гость',
  user_hospital_title: state => state.data?.hospital_title,
  authenticated: state => Boolean(state.data?.auth),
  currentDocPk: state => state.data?.doc_pk,
  user_groups: state => state.data?.groups || [],
  authenticateLoading: state => Boolean(state.data?.loading),
  ex_dep: state => state.data.extended_departments || [],
  directive_from: state => state.directive_from,
  modules: state => state.data.modules || {},
  menu: (state): Menu => state.menu as Menu,
  version: (state, g) => g.menu?.version || null,
  hasNewVersion: state => state.hasNewVersion,
  semiLazyState: state => state.semiLazyState,
  hasGroup: (state, g) => (group) => g.user_groups.includes(group),
  hasAnyGroup: (state, g) => (groups) => groups.some(gr => g.hasGroup(gr)),
};

const actions = {
  async [actionsTypes.GET_USER_DATA]({ commit, getters: g }, { loadMenu = false, semiLazy = false } = {}) {
    if (g.semiLazyState > 0 && semiLazy && g.authenticated) {
      commit(mutationTypes.SET_SEMI_LAZY_STATE, { semiLazy: g.semiLazyState - 1 });
      return;
    }
    commit(mutationTypes.SET_USER_DATA, { loading: true });

    const [userData, menuData] = await Promise.all([
      userPoint.getCurrentUserInfo(),
      loadMenu ? userPoint.getMenu() : Promise.resolve(null),
    ]);

    if (semiLazy && g.authenticated) {
      commit(mutationTypes.SET_SEMI_LAZY_STATE, { semiLazy: SEMI_LAZY_INITIAL });
    }

    commit(mutationTypes.SET_USER_DATA, { data: userData });
    if (loadMenu) {
      commit(mutationTypes.SET_MENU, { data: menuData });
    }
  },
  async [actionsTypes.GET_DIRECTIVE_FROM]({ commit }) {
    const { data } = await userPoint.getDirectiveFrom();
    commit(mutationTypes.SET_DIRECTIVE_FROM, { directive_from: data });
  },
  async [actionsTypes.HAS_NEW_VERSION]({ commit }) {
    commit(mutationTypes.SET_HAS_NEW_VERSION);
  },
};

const mutations = {
  [mutationTypes.SET_USER_DATA](state, { data }) {
    state.data = {
      ...state.data,
      ...data,
    };
  },
  [mutationTypes.SET_HAS_NEW_VERSION](state) {
    state.hasNewVersion = true;
  },
  [mutationTypes.SET_MENU](state, { data }) {
    state.menu = {
      version: data.version,
      region: data.region,
      buttons: data.buttons.map(b => (['/mainmenu', '/mainmenu/'].includes(b.url) ? { ...b, url: '/ui/menu' } : b)),
    };
  },
  [mutationTypes.SET_DIRECTIVE_FROM](state, { directive_from: directiveFrom }) {
    state.directive_from = directiveFrom;
  },
  [mutationTypes.SET_SEMI_LAZY_STATE](state, { semiLazy }) {
    state.semiLazyState = semiLazy;
  },
};

export default {
  state: stateInitial,
  getters,
  mutations,
  actions,
};
