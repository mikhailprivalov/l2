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
      path: '/ui/transfer-card',
      name: 'transfer_card',
      component: () => import('@/pages/TransferDocument/TransferCard.vue'),
      meta: {
        title: 'Движение карт',
        groups: ['Лечащий врач', 'Оператор лечащего врача'],
        narrowLayout: true,
        module: 'l2_transfer_card',
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
      path: '/ui/construct/laboratory',
      name: 'construct_laboratory',
      component: () => import('@/construct/ConstructLaboratory.vue'),
      meta: {
        title: 'Лабораторные исследования',
        fullPageLayout: true,
        groups: ['Конструктор: Лабораторные исследования'],
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
      path: '/ui/construct/employees',
      name: 'construct_employees',
      component: () => import('@/construct/ConstructEmployees.vue'),
      meta: {
        title: 'Управление сотрудниками',
        groups: ['Конструктор: Настройка организации'],
        fullPageLayout: true,
      },
    },
    {
      path: '/ui/construct/price',
      name: 'construct_price',
      component: () => import('@/construct/ConstructPrice.vue'),
      meta: {
        title: 'Настройка прайсов',
        groups: ['Конструктор: Настройка организации'],
        narrowLayout: true,
      },
    },
    {
      path: '/ui/construct/company',
      name: 'construct_company',
      component: () => import('@/construct/ConstructCompany.vue'),
      meta: {
        title: 'Настройка компаний',
        groups: ['Конструктор: Настройка организации'],
      },
    },
    {
      path: '/ui/construct/harmful-factor',
      name: 'harmful_factor',
      component: () => import('@/construct/ConstructHarmfulFactor.vue'),
      meta: {
        title: 'Факторы вредности',
        groups: ['Конструктор: Факторы вредности'],
        narrowLayout: true,
      },
    },
    {
      path: '/ui/construct/research-sets',
      name: 'research_sets',
      component: () => import('@/construct/ConstuctResearchSets.vue'),
      meta: {
        title: 'Наборы исследований',
        groups: ['Конструктор: Настройка организации'],
        narrowLayout: true,
      },
    },
    {
      path: '/ui/construct/patient-control-param',
      name: 'construct_patient_control_param',
      component: () => import('@/construct/ConstructControlParam.vue'),
      meta: {
        title: 'Контролируемые параметры пациентов',
        groups: ['Конструктор: Контролируемые параметры пациентов'],
        narrowLayout: true,
      },
    },
    {
      path: '/ui/construct/route-perform-service',
      name: 'construct_route_perform_service',
      component: () => import('@/construct/ConstructRoutePerformService.vue'),
      meta: {
        title: 'Маршрут исследований',
        groups: ['Конструктор: Маршрут исследований'],
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
        showEcpSchedule: true,
        showExpertiseStatus: true,
      },
    },
    {
      path: '/ui/case-control',
      name: 'cases',
      component: () => import('@/pages/CaseControl/index.vue'),
      meta: {
        title: 'Случаи обслуживания',
        fullPageLayout: true,
        showPrintQueue: true,
        groups: ['Врач параклиники', 'Врач консультаций'],
        module: 'l2_case',
      },
    },
    {
      path: '/ui/search',
      name: 'search',
      component: () => import('@/pages/Search.vue'),
      meta: {
        title: 'Поиск описательных результатов',
        groups: ['Лечащий врач', 'Оператор лечащего врача', 'Врач консультаций', 'Врач стационара'],
        module: 'paraclinic_module',
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
      path: '/ui/upload-directions',
      name: 'upload_directions',
      component: () => import('@/pages/UploadDirections.vue'),
      meta: {
        title: 'Выгрузка',
        groups: [
          'Врач параклиники',
          'Врач консультаций',
          'Врач-лаборант',
        ],
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
      path: '/ui/direction-visit',
      name: 'direction_visit',
      component: () => import('@/pages/DirectionVisit.vue'),
      meta: {
        title: 'Регистрация направлений',
        narrowLayout: true,
        groups: [
          'Посещения по направлениям',
          'Врач параклиники',
          'Врач консультаций',
          'Заборщик биоматериала микробиологии',
          'Получатель биоматериала микробиологии',
        ],
        module: 'paraclinic_module',
      },
    },
    {
      path: '/ui/departments',
      name: 'departments',
      component: () => import('@/pages/DepartmentsForm.vue'),
      meta: {
        title: 'Управление подразделениями',
        narrowLayout: true,
        groups: [
          'Создание и редактирование пользователей',
        ],
      },
    },
    // DEPRECATED
    {
      path: '/ui/cases',
      name: 'cases',
      component: () => import('@/pages/Cases.vue'),
      meta: {
        title: 'Случаи обслуживания',
        fullPageLayout: true,
        groups: [
          'Случаи обслуживания',
        ],
      },
    },
    {
      path: '/ui/construct/descriptive',
      name: 'construct-descriptive',
      component: () => import('@/construct/ConstructParaclinic.vue'),
      meta: {
        title: 'Описательные протоколы и консультации',
        fullPageLayout: true,
        groups: [
          'Конструктор: Параклинические (описательные) исследования',
        ],
        module: 'paraclinic_module',
        showHelpLinkField: true,
      },
    },
    {
      path: '/ui/construct/templates',
      name: 'construct-templates',
      component: () => import('@/construct/ConstructTemplates.vue'),
      meta: {
        title: 'Настройка шаблонов назначений',
        fullPageLayout: true,
        groups: [
          'Конструктор: Настройка шаблонов',
        ],
      },
    },
    {
      path: '/ui/construct/bacteria',
      name: 'construct-bacteria',
      component: () => import('@/construct/ConstructBacteria.vue'),
      meta: {
        title: 'Настройка бактерий и антибиотиков',
        groups: [
          'Конструктор: Бактерии и антибиотики',
        ],
      },
    },
    {
      path: '/ui/construct/dispensary-plan',
      name: 'construct-dispensary-plan',
      component: () => import('@/construct/ConstructDispensaryPlan.vue'),
      meta: {
        title: 'Д-учет настройка обследований',
        groups: [
          'Конструктор: Д-учет',
        ],
      },
    },
    {
      path: '/ui/statistics-tickets',
      name: 'statistics-tickets',
      component: () => import('@/pages/StatisticsTickets.vue'),
      meta: {
        title: 'Статталоны',
        groups: [
          'Оформление статталонов',
          'Лечащий врач',
          'Оператор лечащего врача',
        ],
      },
    },
    {
      path: '/ui/plan-operations',
      name: 'plan-operations',
      component: () => import('@/pages/PlanOperations/index.vue'),
      meta: {
        title: 'План операций',
        narrowLayout: true,
        groups: [
          'Врач стационара',
          'Лечащий врач',
          'Оператор лечащего врача',
          'Врач консультаций',
          'План операций',
        ],
        module: 'l2_hosp',
      },
    },
    {
      path: '/ui/results-report',
      name: 'results-report',
      component: () => import('@/pages/ResultsReport.vue'),
      meta: {
        title: 'Отчёт по результатам',
        groups: [
          'Лечащий врач',
          'Оператор лечащего врача',
          'Врач-лаборант',
          'Лаборант',
          'Врач параклиники',
          'Врач консультаций',
        ],
      },
    },
    {
      path: '/ui/profiles',
      name: 'profiles',
      component: () => import('@/pages/Profiles.vue'),
      meta: {
        title: 'Профили пользователей',
        groups: [
          'Создание и редактирование пользователей',
        ],
      },
    },
    {
      path: '/ui/stationar',
      name: 'stationar',
      component: () => import('@/pages/Stationar/index.vue'),
      meta: {
        title: 'Стационар',
        groups: [
          'Врач стационара',
          't, ad, p',
        ],
        module: 'l2_hosp',
        showHospFavorites: true,
        showOperationPlans: true,
        showExpertiseStatus: true,
        showPrintQueue: true,
      },
    },
    {
      path: '/ui/doc-call',
      name: 'doc-call',
      component: () => import('@/pages/DocCall.vue'),
      meta: {
        title: 'Вызовы врача и заявки',
        groups: [
          'Лечащий врач',
          'Оператор лечащего врача',
          'Вызов врача',
        ],
        module: 'l2_doc_call',
      },
    },
    {
      path: '/ui/employee-jobs',
      name: 'employee-jobs',
      component: () => import('@/pages/EmployeeJobs.vue'),
      meta: {
        title: 'Учёт косвенных услуг по лаборатории',
        groups: [
          'Врач-лаборант',
          'Лаборант',
          'Зав. лабораторией',
        ],
        module: 'l2_employee_job',
      },
    },
    {
      path: '/ui/list-wait',
      name: 'list-wait',
      component: () => import('@/pages/ListWait.vue'),
      meta: {
        title: 'Листы ожидания',
        groups: [
          'Лечащий врач',
          'Оператор лечащего врача',
        ],
        module: 'l2_list_wait',
      },
    },
    {
      path: '/ui/plan-pharmacotherapy',
      name: 'plan-pharmacotherapy',
      component: () => import('@/pages/PlanPharmacotherapy/index.vue'),
      meta: {
        title: 'Процедурный лист',
        groups: [
          'Лечащий врач',
          'Оператор лечащего врача',
        ],
      },
    },
    {
      path: '/ui/laboratory/results',
      name: 'laboratory-results',
      component: () => import('@/pages/LaboratoryResults/index.vue'),
      meta: {
        title: 'Лабораторные результаты',
        groups: [
          'Врач-лаборант',
          'Лаборант',
          'Сброс подтверждений результатов',
        ],
        showLaboratoryHeader: true,
      },
    },
    {
      path: '/ui/direction/history',
      name: 'direction-history',
      component: () => import('@/pages/DirectionHistory.vue'),
      meta: {
        title: 'История направления',
        narrowLayout: true,
        groups: [
          'Лечащий врач',
          'Врач-лаборант',
          'Оператор лечащего врача',
          'Лаборант',
          'Врач-лаборант',
          'Просмотр журнала',
          'Свидетельство о смерти-доступ',
        ],
      },
    },
    {
      path: '/ui/directions/print',
      name: 'directions-print',
      component: () => import('@/pages/DirectionsPrint.vue'),
      meta: {
        title: 'Печать направлений',
        narrowLayout: true,
        groups: [
          'Лечащий врач',
          'Врач-лаборант',
          'Оператор лечащего врача',
        ],
      },
    },
    {
      path: '/ui/receive/one-by-one',
      name: 'receive-one-by-one',
      component: () => import('@/pages/ReceiveOneByOne.vue'),
      meta: {
        title: 'Приём биоматериала по одному',
        narrowLayout: true,
        groups: [
          'Получатель биоматериала',
        ],
        showLaboratorySelector: true,
      },
    },
    {
      path: '/ui/receive/by-direction',
      name: 'receive-by-direction',
      component: () => import('@/pages/ReceiveByDirection.vue'),
      meta: {
        title: 'Поступление',
        narrowLayout: true,
        groups: [
          'Поступление материала',
        ],
        showLaboratorySelector: true,
      },
    },
    {
      path: '/ui/directories',
      name: 'directories',
      component: () => import('@/pages/Directories/index.vue'),
      meta: {
        title: 'Справочники',
        module: 'l2_dynamic_directories',
      },
    },
    {
      path: '/ui/email-org',
      name: 'email-org',
      component: () => import('@/pages/EmailOrg.vue'),
      meta: {
        narrowLayout: true,
        title: 'Отправка результатов в организации',
        module: 'l2_send_orgs_email_results',
        groups: [
          'Отправка результатов в организации',
        ],
      },
    },
    {
      path: '/ui/receive/journal',
      name: 'receive-journal',
      component: () => import('@/pages/ReceiveJournal.vue'),
      meta: {
        narrowLayout: true,
        title: 'Журнал приёма',
        groups: [
          'Получатель биоматериала',
        ],
        showLaboratorySelectorWithoutAll: true,
      },
    },
    {
      path: '/ui/utils',
      name: 'utils',
      component: () => import('@/pages/Utils.vue'),
      meta: {
        narrowLayout: true,
        title: 'Инструменты',
        groups: ['Инструменты'],
      },
    },
    {
      path: '/ui/results/preview',
      name: 'results-preview',
      component: () => import('@/pages/ResultsPreview.vue'),
      meta: {
        emptyLayout: true,
        title: 'Предварительный просмотр бланков результатов',
      },
    },
    {
      path: '/ui/directions/preview',
      name: 'directions-preview',
      component: () => import('@/pages/DirectionsPreview.vue'),
      meta: {
        emptyLayout: true,
        title: 'Предварительный просмотр бланков направлений',
      },
    },
    {
      path: '/ui/analyzers',
      name: 'ManageAnalyzer',
      component: () => import('@/pages/ManageAnalyzers/index.vue'),
      meta: {
        narrowLayout: true,
        title: 'Управление анализаторами',
        groups: ['Управление анализаторами'],
      },
    },
    {
      path: '/ui/turnovers',
      name: 'Turnovers',
      component: () => import('@/pages/Turnovers/Turnovers.vue'),
      meta: {
        title: 'Обороты',
        groups: ['Обороты'],
      },
    },
    {
      path: '/ui/construct/related-tube/:id',
      name: 'construct-related-tube',
      component: () => import('@/construct/ConstructRelatedTube.vue'),
      meta: {
        emptyLayout: true,
        title: 'Управление ёмкостями фракций',
        groups: ['Оператор', 'Конструктор: Лабораторные исследования'],
      },
    },
    {
      path: '/404',
      name: '404',
      meta: {},
    },
    {
      path: '/ui/404',
      name: 'ui404',
      component: () => import('@/pages/Ui404.vue'),
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
    await router.app.$store.dispatch(actions.GET_USER_DATA, { loadMenu: true, semiLazy: true });
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
      && toMatched.every((r) => !r.meta.groups?.find((g) => getters.user_groups.includes(g)))
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
    window.location.href = String(to.fullPath);
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
