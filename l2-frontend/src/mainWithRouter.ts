import Vue from 'vue';
import Router from 'vue-router';
import VueMeta from 'vue-meta';
import Toast from 'vue-toastification';
import 'vue-toastification/dist/index.css';

import App from '@/App.vue';

import registerHooks from './registerHooks';
import registerVue from './registerVue';
import store from './store';
import * as actions from './store/action-types';

import './styles/index.scss';

Vue.use(Toast, {
  transition: 'Vue-Toastification__bounce',
  maxToasts: 20,
  newestOnTop: false,
});

registerVue();

Vue.use(Router);
Vue.use(VueMeta);

const router = new Router({
  mode: 'history',
  routes: [
    {
      path: '/ui/login',
      name: 'login',
      component: () => import('@/pages/LoginPage.vue'),
      meta: {
        allowWithoutLogin: true,
        title: 'Вход в систему',
      },
    },
    {
      path: '/ui/menu',
      name: 'menu',
      component: () => import('@/pages/MenuPage.vue'),
      meta: {
        narrowLayout: true,
        title: 'Меню L2',
      },
    },
  ],
});

router.beforeEach(async (to, from, next) => {
  await router.app.$store.dispatch(actions.RESET_G_LOADING);
  if (to.fullPath.startsWith('/ui') || to.fullPath.startsWith('ui')) {
    await router.app.$store.dispatch(actions.INC_G_LOADING);

    await router.app.$store.dispatch(actions.INC_G_LOADING);
    await router.app.$store.dispatch(actions.GET_USER_DATA, { loadMenu: true });
    await router.app.$store.dispatch(actions.DEC_G_LOADING);
    if (
      to.name !== 'login'
      && !to.matched.some(record => record.meta.allowWithoutLogin)
      && !router.app.$store.getters.authenticated
    ) {
      next({ name: 'login' });
    } else if (
      to.name === 'login'
      && router.app.$store.getters.authenticated
    ) {
      const urlParams = new URLSearchParams(window.location.search);
      const nextPath = urlParams.get('next');
      next(nextPath || '/ui/menu');
    } else {
      next();
    }
  } else {
    window.location.href = to.fullPath;
  }
});

router.afterEach(async () => {
  await router.app.$store.dispatch(actions.DEC_G_LOADING);
});

new Vue({
  router,
  store,
  render: h => h(App),
  async created() {
    registerHooks(this);
  },
}).$mount('#app');
