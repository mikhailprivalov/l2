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
        title: 'Разделы',
      },
    },
    {
      path: '/ui/directions',
      name: 'directions',
      component: () => import('@/pages/Directions.vue'),
      meta: {
        title: 'Направления и картотека',
        groups: [
          'Лечащий врач',
          'Врач-лаборант',
          'Оператор лечащего врача',
          'Оператор Контакт-центра',
          'Свидетельство о смерти-доступ',
        ],
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
      path: '/ui/construct/menu',
      name: 'construct_menu',
      component: () => import('@/construct/ConstructMenu.vue'),
      meta: {
        title: 'Конструктор справочника',
        groups: [
          'Конструктор: Лабораторные исследования',
          'Конструктор: Параклинические (описательные) исследования',
          'Конструктор: Консультации',
          'Конструктор: Ёмкости для биоматериала',
          'Конструктор: Настройка УЕТов',
          'Конструктор: Группировка исследований по направлениям',
          'Конструктор: Настройка скрининга',
          'Конструктор: Настройка организации',
        ],
        narrowLayout: true,
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
      path: '/ui/construct/org',
      name: 'construct_org',
      component: () => import('@/construct/ConstructOrg.vue'),
      meta: {
        title: 'Настройка организации',
        groups: ['Конструктор: Настройка организации'],
        narrowLayout: true,
      },
    },
    {
      path: '/ui/construct/district',
      name: 'construct_district',
      component: () => import('@/construct/ConstructDistrict.vue'),
      meta: {
        title: 'Настройка участков',
        groups: ['Конструктор: Настройка организации'],

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
    {
      path: '/ui/monitorings/report',
      name: 'monitorings_report',
      component: () => import('@/pages/MonitoringsReport/index.vue'),
      meta: {
        title: 'Просмотр мониторингов',
        groups: ['Просмотр мониторингов'],
        module: 'l2_monitorings',
      },
    },
    {
      path: '/ui/statistics/report/:id?',
      name: 'statistics_report',
      component: () => import('@/pages/StatisticsReport/index.vue'),
      meta: {
        allowWithoutLogin: true,
        hideHeaderWithoutLogin: true,
        title: 'Просмотр графиков статистики',
        module: 'l2_statistics',
      },
    },
    {
      path: '/ui/results/descriptive',
      name: 'results_descriptive',
      component: () => import('@/pages/ResultsParaclinic.vue'),
      meta: {
        title: 'Ввод описательных результатов',
        groups: ['Врач параклиники', 'Врач консультаций', 'Заполнение мониторингов', 'Свидетельство о смерти-доступ'],
        module: 'paraclinic_module',
        showCreateDirection: true,
        showRmisLinkSchedule: true,
        showExpertiseStatus: true,
      },
    },
    {
      path: '/ui/schedule',
      name: 'schedule',
      component: () => import('@/pages/Schedule/index.vue'),
      meta: {
        title: 'Расписание',
        groups: [
          'Лечащий врач',
          'Оператор лечащего врача',
          'Врач консультаций',
          'Врач стационара',
          'Врач параклиники',
          'Управление расписанием',
          'Создание и редактирование пользователей',
        ],
        module: 'l2_schedule',
      },
    },
    {
      path: '/ui/biomaterial/get',
      name: 'biomaterial_get',
      component: () => import('@/pages/BiomaterialGet.vue'),
      meta: {
        title: 'Забор биоматериала',
        groups: ['Заборщик биоматериала'],
      },
    },
    {
      path: '/ui/statistic',
      name: 'statistic',
      component: () => import('@/pages/Statistics.vue'),
      meta: {
        title: 'Статистика',
        groups: [
          'Просмотр статистики',
          'Врач-лаборант',
          'Статистика скрининга',
          'Свидетельство о смерти-доступ',
          'Врач консультаций',
        ],
      },
    },
    {
      path: '/ui/eds',
      name: 'eds',
      component: () => import('@/pages/EDS.vue'),
      meta: {
        title: 'Подпись документов',
        groups: [
          'Подпись документов',
          'Врач параклиники',
          'Врач консультаций',
          'Врач-лаборант',
          'ЭЦП Медицинской организации',
          'Свидетельство о смерти-доступ',
        ],
        module: 'l2_eds',
      },
    },
    {
      path: '/ui/plan-hospitalization',
      name: 'plan_hospitalization',
      component: () => import('@/pages/PlanHospitalization/index.vue'),
      meta: {
        title: 'План госпитализации',
        groups: ['Лечащий врач', 'Оператор лечащего врача', 'Вызов врача'],
        narrowLayout: true,
      },
    },
    {
      path: '/ui/some-links',
      name: 'some_links',
      component: () => import('@/pages/SomeLinks.vue'),
      meta: {
        title: 'Ссылки',
        narrowLayout: true,
        module: 'l2_some_links',
      },
    },
    {
      path: '/404',
      name: '404',
      meta: {},
    },
    {
      path: '*',
      redirect: (to) => ({ name: '404', hash: to.fullPath }),
      meta: {},
    },
  ],
});

router.beforeEach(async (to, from, next) => {
  if (to.path === from.path && to.hash !== from.hash) {
    next();
    return;
  }

  if (
    to.fullPath.startsWith('/ui/https://')
    || to.fullPath.startsWith('/ui/http://')
    || to.fullPath.startsWith('ui/https://')
    || to.fullPath.startsWith('ui/http://')
  ) {
    window.location.replace(to.fullPath.split('ui/')[1]);
    return;
  }

  if (to.name === '404') {
    if (to.hash && !to.hash.startsWith('/ui')) {
      window.location.href = to.hash;
      return;
    }

    if (
      to.hash.startsWith('/ui/https://')
      || to.hash.startsWith('/ui/http://')
      || to.hash.startsWith('ui/https://')
      || to.hash.startsWith('ui/http://')
    ) {
      window.location.replace(to.hash.split('ui/')[1]);
      return;
    }

    router.app.$toast.warning(`Страница ${to.hash} не найдена.`, {
      position: POSITION.BOTTOM_RIGHT,
      timeout: 8000,
      icon: true,
    });
    await router.app.$store.dispatch(actions.RESET_G_LOADING);
    next({ name: 'menu' });
    return;
  }

  await router.app.$store.dispatch(actions.RESET_G_LOADING);

  if (to.fullPath.startsWith('/https://') || to.fullPath.startsWith('/http://')) {
    window.location.replace(to.fullPath.replace('/', ''));
    return;
  }

  if (to.fullPath.startsWith('/ui') || to.fullPath.startsWith('ui')) {
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
    const toMatched = to.matched.filter(Boolean);

    if (to.name === 'login' && !getters.authenticated) {
      // Если пользователь неавторизован и открывается страница входа
      // то не проверяем другие варианты
      next();
    } else if (to.name !== 'login' && !toMatched.some((record) => record.meta.allowWithoutLogin) && !getters.authenticated) {
      await router.app.$store.dispatch(actions.RESET_G_LOADING);
      // Если пользователь неавторизован и страница требует авторизации,
      // то идём на страницу входа
      next({ name: 'login', query: { next: to.fullPath } });
    } else if (to.name === 'login' && getters.authenticated) {
      await router.app.$store.dispatch(actions.RESET_G_LOADING);
      // Если пользователь авторизован и открывается страница входа,
      // то открываем страницу из ?next=<адрес> или меню
      const urlParams = new URLSearchParams(window.location.search);
      const nextPath = urlParams.get('next');
      next(nextPath || { name: 'menu' });
    } else if (
      toMatched.some((r) => r.meta.groups)
      && toMatched.every((r) => !r.meta.groups || !r.meta.groups.find((g) => getters.user_groups.includes(g)))
      && !getters.user_groups.includes('Admin')
    ) {
      router.app.$toast.warning('Нет доступа.', {
        position: POSITION.BOTTOM_RIGHT,
        timeout: 8000,
        icon: true,
      });
      await router.app.$store.dispatch(actions.RESET_G_LOADING);
      // Если страница требует наличия групп и у пользователя в группах таких нет, и нет группы Admin,
      // то открываем меню
      next({ name: 'menu' });
    } else if (toMatched.some((r) => r.meta.module) && toMatched.every((r) => !getters.modules[r.meta.module])) {
      router.app.$toast.warning('Не настроено.', {
        position: POSITION.BOTTOM_RIGHT,
        timeout: 8000,
        icon: true,
      });
      await router.app.$store.dispatch(actions.RESET_G_LOADING);
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
  async created() {
    registerHooks(this);
  },
  render: (h) => h(App),
}).$mount('#app');
