import Vue from 'vue';
import Router from 'vue-router';
import VueMeta from 'vue-meta';
import { POSITION } from 'vue-toastification/src/ts/constants';

import App from '@/App.vue';

import registerHooks from './registerHooks';
import registerVue from './registerVue';
import store from './store';
import * as actions from './store/action-types';

import './styles/index.scss';

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
    {
      path: '/ui/directions',
      name: 'directions',
      component: () => import('@/pages/Directions.vue'),
      meta: {
        title: 'Направления и картотека',
        groups: ['Лечащий врач', 'Врач-лаборант', 'Оператор лечащего врача', 'Оператор Контакт-центра'],
        showCardReader: true,
        showExtendedPatientSearch: true,
      },
    },
    {
      path: '/ui/results-by-department-or-doctor',
      name: 'results_department',
      component: () => import('@/pages/ResultsDepartment.vue'),
      meta: {
        title: 'Печать по отделению или врачу',
        groups: ['Лечащий врач', 'Оператор лечащего врача'],
      },
    },
    {
      path: '/ui/construct/screening',
      name: 'construct_screening',
      component: () => import('@/construct/ConstructScreening.vue'),
      meta: {
        title: 'Настройка скрининга',
        groups: ['Конструктор: Настройка скрининга'],
      },
    },
    {
      path: '/ui/extra-notification',
      name: 'extra_notification',
      component: () => import('@/pages/ExtraNotification.vue'),
      meta: {
        title: 'Экстренные извещения',
        groups: ['Лечащий врач', 'Оператор лечащего врача', 'Вызов врача', 'Заполнение экстренных извещений'],
        module: 'l2_extra_notifications',
      },
    },
    {
      path: '/ui/monitorings/enter',
      name: 'monitorings_enter',
      component: () => import('@/pages/MonitoringsEnter.vue'),
      meta: {
        title: 'Заполнение мониторингов',
        groups: ['Заполнение мониторингов'],
        module: 'l2_monitorings',
      },
    },
  ],
});

router.beforeEach(async (to, from, next) => {
  await router.app.$store.dispatch(actions.RESET_G_LOADING);
  if (to.fullPath.startsWith('/ui') || to.fullPath.startsWith('ui')) {
    if (
      to.fullPath.startsWith('/ui/https://')
      || to.fullPath.startsWith('/ui/http://')
      || to.fullPath.startsWith('ui/https://')
      || to.fullPath.startsWith('ui/http://')
    ) {
      window.location.replace(to.fullPath.split('ui/')[1]);
      return;
    }

    await router.app.$store.dispatch(actions.INC_G_LOADING);

    await router.app.$store.dispatch(actions.INC_G_LOADING);
    await router.app.$store.dispatch(actions.GET_USER_DATA, { loadMenu: true });
    const { getters } = router.app.$store;

    if (getters.authenticated) {
      await Promise.all([
        router.app.$store.dispatch(actions.GET_ALL_DEPARTMENTS, { lazy: true }),
        router.app.$store.dispatch(actions.GET_BASES, { lazy: true }),
        router.app.$store.dispatch(actions.LOAD_HOSPITALS, { lazy: true }),
      ]);
    }

    await router.app.$store.dispatch(actions.DEC_G_LOADING);

    if (
      to.name === 'login'
      && !getters.authenticated
    ) {
      // Если пользователь неавторизован и открывается страница входа
      // то не проверяем другие варианты
      next();
    } else if (
      to.name !== 'login'
      && !to.matched.some(record => record.meta.allowWithoutLogin)
      && !getters.authenticated
    ) {
      // Если пользователь неавторизован и страница требует авторизации,
      // то идём на страницу входа
      next({ name: 'login' });
    } else if (
      to.name === 'login'
      && getters.authenticated
    ) {
      // Если пользователь авторизован и открывается страница входа,
      // то открываем страницу из ?next=<адрес> или меню
      const urlParams = new URLSearchParams(window.location.search);
      const nextPath = urlParams.get('next');
      next(nextPath || { name: 'menu' });
    } else if (
      to.matched.some(r => r.meta.groups)
      && to.matched.every(r => !r.meta.groups || !r.meta.groups.find(g => getters.user_groups.includes(g)))
      && !getters.user_groups.includes('Admin')
    ) {
      router.app.$toast.warning('Нет доступа.', {
        position: POSITION.BOTTOM_RIGHT,
        timeout: 8000,
        icon: true,
      });
      // Если страница требует наличия групп и у пользователя в группах таких нет, и нет группы Admin,
      // то открываем меню
      next({ name: 'menu' });
    } else if (
      to.matched.some(r => r.meta.module)
      && to.matched.every(r => !getters.modules[r.meta.module])
    ) {
      router.app.$toast.warning('Не настроено.', {
        position: POSITION.BOTTOM_RIGHT,
        timeout: 8000,
        icon: true,
      });
      // Если страница требует наличия модуля, но модуль не настроен
      // то открываем меню
      next({ name: 'menu' });
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
