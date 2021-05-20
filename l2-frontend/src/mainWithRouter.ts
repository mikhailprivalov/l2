import Vue from 'vue';
import Router from 'vue-router';
import VueMeta from 'vue-meta';
import App from '@/App.vue';

import registerHooks from './registerHooks';
import registerVue from './registerVue';
import store from './store';
import * as actions from './store/action-types';

import './styles/index.scss';
import { RESET_G_LOADING } from './store/action-types';

registerVue();

Vue.use(Router);
Vue.use(VueMeta);
Vue.prototype.$orgTitle = () => window.ORG_TITLE;

const router = new Router({
  mode: 'history',
  routes: [
    {
      path: '/ui/login',
      name: 'login',
      component: () => import('@/pages/LoginPage.vue'),
      meta: {
        allowWithoutLogin: true,
      },
    },
  ],
});

router.beforeEach(async (to, from, next) => {
  if (to.fullPath.startsWith('/ui') || to.fullPath.startsWith('ui')) {
    await router.app.$store.dispatch(actions.RESET_G_LOADING);
    await router.app.$store.dispatch(actions.INC_G_LOADING);
    next();
  } else {
    window.location.href = to.fullPath;
  }
});

router.afterEach(() => {
  // eslint-disable-next-line @typescript-eslint/no-empty-function
  router.app.$store.dispatch(actions.DEC_G_LOADING).then(() => {
  });
});

router.beforeEach((to, from, next) => {
  if (
    to.name !== 'login'
    && !to.matched.some(record => record.meta.allowWithoutLogin)
    && router.app.$store.getters.authenticated
  ) {
    next({ name: 'login' });
  } else {
    next();
  }
});

new Vue({
  router,
  store,
  render: h => h(App),
  async created() {
    await this.$store.dispatch(actions.INC_G_LOADING);
    await this.$store.dispatch(actions.GET_USER_DATA);
    registerHooks(this);
    await this.$store.dispatch(actions.DEC_G_LOADING);
  },
}).$mount('#app');
