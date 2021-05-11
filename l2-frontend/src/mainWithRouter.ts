import Vue from 'vue';
import Router from 'vue-router';
import LogPage from '@/pages/LogPage.vue';
import App from '@/App.vue';

import registerHooks from './registerHooks';
import registerVue from './registerVue';
import store from './store';

import './styles/index.scss';

registerVue();

Vue.use(Router);

const router = new Router({
  mode: 'history',
  routes: [
    {
      path: '/ui/log',
      name: 'log',
      component: LogPage,
    },
  ],
});

new Vue({
  router,
  store,
  render: h => h(App),
  created() {
    registerHooks(this);
  },
}).$mount('#app');
