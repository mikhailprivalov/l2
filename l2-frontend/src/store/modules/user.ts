import { Menu } from '@/types/menu';
import user_point from '../../api/user-point';
import * as mutation_types from '../mutation-types';
import * as actionsTypes from '../action-types';

const stateInitial = {
  data: {
    auth: false,
    loading: true,
    modules: {},
    groups: [],
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
  fio_short: (state, g) => {
    if (!g.user_data || !g.user_data.fio) {
      return 'Unauthenticated';
    }

    return String(g.user_data.fio)
      .split(' ')
      .map((p, i) => {
        if (!p) {
          return p;
        }

        if (i === 0 || p.length === 1) {
          return `${p} `;
        }

        return `${p[0]}.`;
      })
      .filter(Boolean)
      .join('')
      .trim();
  },
  user_hospital_title: state => state.data?.hospital_title,
  authenticated: state => Boolean(state.data?.auth),
  user_groups: state => state.data?.groups || [],
  authenticateLoading: state => Boolean(state.data?.loading),
  ex_dep: state => state.data.extended_departments || [],
  directive_from: state => state.directive_from,
  modules: state => state.data.modules || {},
  menu: (state): Menu => state.menu as Menu,
  version: (state, g) => (g.menu || {}).version || null,
  hasNewVersion: state => state.hasNewVersion,
};

const actions = {
  async [actionsTypes.GET_USER_DATA]({ commit }, { loadMenu = false } = {}) {
    commit(mutation_types.SET_USER_DATA, { loading: true });

    const [userData, menuData] = await Promise.all([
      user_point.getCurrentUserInfo(),
      loadMenu ? user_point.getMenu() : Promise.resolve(null),
    ]);

    commit(mutation_types.SET_USER_DATA, { data: userData });
    if (loadMenu) {
      commit(mutation_types.SET_MENU, { data: menuData });
    }
  },
  async [actionsTypes.GET_DIRECTIVE_FROM]({ commit }) {
    const { data: directive_from } = await user_point.getDirectiveFrom();
    commit(mutation_types.SET_DIRECTIVE_FROM, { directive_from });
  },
  async [actionsTypes.HAS_NEW_VERSION]({ commit }) {
    commit(mutation_types.SET_HAS_NEW_VERSION);
  },
};

const mutations = {
  [mutation_types.SET_USER_DATA](state, { data }) {
    state.data = {
      ...state.data,
      ...data,
    };
  },
  [mutation_types.SET_HAS_NEW_VERSION](state) {
    state.hasNewVersion = true;
  },
  [mutation_types.SET_MENU](state, { data }) {
    state.menu = {
      version: data.version,
      region: data.region,
      buttons: data.buttons.map(b => (['/mainmenu', '/mainmenu/'].includes(b.url) ? { ...b, url: '/ui/menu' } : b)),
    };
  },
  [mutation_types.SET_DIRECTIVE_FROM](state, { directive_from }) {
    state.directive_from = directive_from;
  },
};

export default {
  state: stateInitial,
  getters,
  mutations,
  actions,
};
