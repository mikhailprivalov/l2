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

// Lazy load components with chunk names for better debugging
const LoginPage = () => import(/* webpackChunkName: "auth" */ '@/pages/LoginPage.vue');
const MenuPage = () => import(/* webpackChunkName: "menu" */ '@/pages/MenuPage.vue');
const Directions = () => import(/* webpackChunkName: "directions" */ '@/pages/Directions.vue');
const ResultsDepartment = () => import(/* webpackChunkName: "results" */ '@/pages/ResultsDepartment.vue');
const TransferCard = () => import(/* webpackChunkName: "transfer" */ '@/pages/TransferDocument/TransferCard.vue');

// Construct module lazy loading
const ConstructMenu = () => import(/* webpackChunkName: "construct-core" */ '@/construct/ConstructMenu.vue');
const ConstructLaboratory = () => import(/* webpackChunkName: "construct-lab" */ '@/construct/ConstructLaboratory.vue');
const ConstructParaclinic = () => import(/* webpackChunkName: "construct-para" */ '@/construct/ConstructParaclinic.vue');
const ConstructTubes = () => import(
  /* webpackChunkName: "construct-tubes" */ '@/construct/ConstructTubes/ConstructTubes.vue'
);
const ConstructEmployees = () => import(
  /* webpackChunkName: "construct-emp" */ '@/construct/ConstructEmployees.vue'
);
const ConstructTemplates = () => import(
  /* webpackChunkName: "construct-tmpl" */ '@/construct/ConstructTemplates.vue'
);
const ConstructBacteria = () => import(
  /* webpackChunkName: "construct-bact" */ '@/construct/ConstructBacteria.vue'
);
const ConstructCompany = () => import(
  /* webpackChunkName: "construct-company" */ '@/construct/ConstructCompany.vue'
);
const ConstructOrg = () => import(
  /* webpackChunkName: "construct-org" */ '@/construct/ConstructOrg.vue'
);
const ConstructScreening = () => import(
  /* webpackChunkName: "construct-screen" */ '@/construct/ConstructScreening.vue'
);
const ConstructPrice = () => import(
  /* webpackChunkName: "construct-price" */ '@/construct/ConstructPrice.vue'
);
const ConstructComplexServices = () => import(
  /* webpackChunkName: "construct-complex" */ '@/construct/ConstructComplexServices.vue'
);
const ConstructDistinct = () => import(
  /* webpackChunkName: "construct-distinct" */ '@/construct/ConstructDistrict.vue'
);
const ConstructHarmfulFactor = () => import(
  /* webpackChunkName: "construct-harmful" */ '@/construct/ConstructHarmfulFactor.vue'
);
const ConstructControlParam = () => import(
  /* webpackChunkName: "construct-control" */ '@/construct/ConstructControlParam.vue'
);
const ConstructResearchSets = () => import(
  /* webpackChunkName: "construct-sets" */ '@/construct/ConstuctResearchSets.vue'
);
const ConstructRelatedTube = () => import(
  /* webpackChunkName: "construct-related" */ '@/construct/ConstructRelatedTube.vue'
);
const ConstructDispensaryPlan = () => import(
  /* webpackChunkName: "construct-dispensary" */ '@/construct/ConstructDispensaryPlan.vue'
);
const ConstructRoutePerformService = () => import(
  /* webpackChunkName: "construct-route" */ '@/construct/ConstructRoutePerformService.vue'
);

// Laboratory and results modules
const LaboratoryResults = () => import(
  /* webpackChunkName: "lab-results" */ '@/pages/LaboratoryResults/index.vue'
);
const ResultsParaclinic = () => import(
  /* webpackChunkName: "results-para" */ '@/pages/ResultsParaclinic.vue'
);
const ResultsReport = () => import(
  /* webpackChunkName: "results-report" */ '@/pages/ResultsReport.vue'
);
const ResultsPreview = () => import(
  /* webpackChunkName: "results-preview" */ '@/pages/ResultsPreview.vue'
);

// Statistics and reports
const Statistics = () => import(/* webpackChunkName: "statistics" */ '@/pages/Statistics.vue');
const StatisticsTickets = () => import(
  /* webpackChunkName: "stats-tickets" */ '@/pages/StatisticsTickets.vue'
);
const StatisticsReport = () => import(
  /* webpackChunkName: "stats-report" */ '@/pages/StatisticsReport/index.vue'
);

// Hospital and patient management
const Stationar = () => import(/* webpackChunkName: "hospital" */ '@/pages/Stationar/index.vue');
const PlanHospitalization = () => import(
  /* webpackChunkName: "plan-hosp" */ '@/pages/PlanHospitalization/index.vue'
);
const PlanOperations = () => import(
  /* webpackChunkName: "plan-ops" */ '@/pages/PlanOperations/index.vue'
);
const PlanPharmacotherapy = () => import(
  /* webpackChunkName: "plan-pharma" */ '@/pages/PlanPharmacotherapy/index.vue'
);

// Schedule and time management
const Schedule = () => import(/* webpackChunkName: "schedule" */ '@/pages/Schedule/index.vue');
const WorkingTime = () => import(
  /* webpackChunkName: "work-time" */ '@/pages/WorkingTime/WorkingTime.vue'
);

// Other core modules - lazy loaded with appropriate chunks
const Directories = () => import(
  /* webpackChunkName: "directories" */ '@/pages/Directories/index.vue'
);
const BiomaterialGet = () => import(
  /* webpackChunkName: "biomaterial" */ '@/pages/BiomaterialGet.vue'
);
const ReceiveOneByOne = () => import(
  /* webpackChunkName: "receive" */ '@/pages/ReceiveOneByOne.vue'
);
const ReceiveByDirection = () => import(
  /* webpackChunkName: "receive-dir" */ '@/pages/ReceiveByDirection.vue'
);
const ReceiveJournal = () => import(
  /* webpackChunkName: "receive-journal" */ '@/pages/ReceiveJournal.vue'
);
const RequestCreation = () => import(
  /* webpackChunkName: "request-create" */ '@/pages/RequestCreation/index.vue'
);
const RequestsFill = () => import(
  /* webpackChunkName: "request-fill" */ '@/pages/RequestsFill/index.vue'
);

const router = new Router({
  mode: 'history',
  routes: [
    {
      path: '/ui/login',
      name: 'login',
      component: LoginPage,
      meta: {
        allowWithoutLogin: true,
        title: 'Вход в систему',
      },
    },
    {
      path: '/ui/menu',
      name: 'menu',
      component: MenuPage,
      meta: {
        narrowLayout: true,
        title: 'Разделы',
      },
    },
    {
      path: '/ui/directions',
      name: 'directions',
      component: Directions,
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
        showShiftModal: true,
      },
    },
    {
      path: '/ui/results-by-department-or-doctor',
      name: 'results_department',
      component: ResultsDepartment,
      meta: {
        title: 'Печать по отделению или врачу',
        groups: ['Лечащий врач', 'Оператор лечащего врача'],
      },
    },
    {
      path: '/ui/transfer-card',
      name: 'transfer_card',
      component: TransferCard,
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
      component: ConstructMenu,
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
      component: ConstructLaboratory,
      meta: {
        title: 'Конструктор: Лабораторные исследования',
        groups: ['Конструктор: Лабораторные исследования'],
        fullPageLayout: true,
      },
    },
    {
      path: '/ui/construct/paraclinic',
      name: 'construct_paraclinic',
      component: ConstructParaclinic,
      meta: {
        title: 'Конструктор: Параклинические исследования',
        groups: ['Конструктор: Параклинические (описательные) исследования'],
        fullPageLayout: true,
      },
    },
    {
      path: '/ui/construct/consultations',
      name: 'construct_consultations',
      component: ConstructParaclinic, // Use ConstructParaclinic for consultations
      meta: {
        title: 'Конструктор: Консультации',
        groups: ['Конструктор: Консультации'],
        fullPageLayout: true,
      },
    },
    {
      path: '/ui/construct/tubes',
      name: 'construct_tubes',
      component: ConstructTubes,
      meta: {
        title: 'Конструктор: Ёмкости для биоматериала',
        groups: ['Конструктор: Ёмкости для биоматериала'],
        narrowLayout: true,
      },
    },
    {
      path: '/ui/construct/employees',
      name: 'construct_employees',
      component: ConstructEmployees,
      meta: {
        title: 'Конструктор: Сотрудники',
        groups: ['Конструктор: Настройка организации'],
        fullPageLayout: true,
      },
    },
    {
      path: '/ui/construct/templates',
      name: 'construct_templates',
      component: ConstructTemplates,
      meta: {
        title: 'Конструктор: Шаблоны',
        groups: [
          'Конструктор: Лабораторные исследования',
          'Конструктор: Параклинические (описательные) исследования',
          'Конструктор: Консультации',
          'Конструктор: Настройка организации',
        ],
        narrowLayout: true,
      },
    },
    {
      path: '/ui/construct/bacteria',
      name: 'construct_bacteria',
      component: ConstructBacteria,
      meta: {
        title: 'Конструктор: Бактерии и антибиотики',
        groups: ['Конструктор: Лабораторные исследования'],
        fullPageLayout: true,
      },
    },
    {
      path: '/ui/construct/company',
      name: 'construct_company',
      component: ConstructCompany,
      meta: {
        title: 'Конструктор: Контрагенты',
        groups: ['Конструктор: Настройка организации'],
        narrowLayout: true,
      },
    },
    {
      path: '/ui/construct/org',
      name: 'construct_org',
      component: ConstructOrg,
      meta: {
        title: 'Конструктор: Настройка организации',
        groups: ['Конструктор: Настройка организации'],
        narrowLayout: true,
      },
    },
    {
      path: '/ui/construct/harmful-factor',
      name: 'harmful_factor',
      component: ConstructHarmfulFactor,
      meta: {
        title: 'Факторы вредности',
        groups: ['Конструктор: Факторы вредности'],
        narrowLayout: true,
      },
    },
    {
      path: '/ui/construct/research-sets',
      name: 'research_sets',
      component: ConstructResearchSets,
      meta: {
        title: 'Наборы исследований',
        groups: ['Конструктор: Настройка организации'],
        narrowLayout: true,
      },
    },
    {
      path: '/ui/construct/patient-control-param',
      name: 'construct_patient_control_param',
      component: ConstructControlParam,
      meta: {
        title: 'Контролируемые параметры пациентов',
        groups: ['Конструктор: Контролируемые параметры пациентов'],
        narrowLayout: true,
      },
    },
    {
      path: '/ui/construct/route-perform-service',
      name: 'construct_route_perform_service',
      component: ConstructRoutePerformService,
      meta: {
        title: 'Маршрут исследований',
        groups: ['Конструктор: Маршрут исследований'],
        narrowLayout: true,
      },
    },
    {
      path: '/ui/construct/complex-services',
      name: 'construct_complex',
      component: ConstructComplexServices,
      meta: {
        title: 'Комплексные услуги',
        groups: ['Конструктор: Комплексные услуги'],
        narrowLayout: true,
      },
    },
    {
      path: '/ui/construct/district',
      name: 'construct_district',
      component: ConstructDistinct,
      meta: {
        title: 'Настройка участков',
        groups: ['Конструктор: Настройка организации'],

      },
    },
    {
      path: '/ui/construct/tubes',
      name: 'construct_tubes',
      component: ConstructTubes,
      meta: {
        title: 'Ёмкости для биоматериала (н)',
        groups: ['Конструктор: Ёмкости для биоматериала'],
        narrowLayout: true,
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
      component: StatisticsReport,
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
      component: ResultsParaclinic,
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
      name: 'cases-control',
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
      component: Schedule,
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
      component: BiomaterialGet,
      meta: {
        title: 'Забор биоматериала',
        groups: ['Заборщик биоматериала'],
      },
    },
    {
      path: '/ui/statistic',
      name: 'statistic',
      component: Statistics,
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
      component: PlanHospitalization,
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
      component: ConstructParaclinic,
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
      component: ConstructTemplates,
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
      component: ConstructBacteria,
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
      component: ConstructDispensaryPlan,
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
      component: StatisticsTickets,
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
      component: PlanOperations,
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
      component: ResultsReport,
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
      path: '/ui/logs',
      name: 'logs',
      component: () => import('@/pages/Logs.vue'),
      meta: {
        title: 'Просмотр журнала',
        groups: ['Просмотр журнала'],
      },
    },
    {
      path: '/ui/stationar',
      name: 'stationar',
      component: Stationar,
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
      component: PlanPharmacotherapy,
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
      component: LaboratoryResults,
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
      component: ReceiveOneByOne,
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
      component: ReceiveByDirection,
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
      component: Directories,
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
      component: ReceiveJournal,
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
      component: ResultsPreview,
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
      path: '/ui/chambers',
      name: 'ManageChamber',
      component: () => import('@/pages/ManageChambers/index.vue'),
      meta: {
        title: 'Палаты',
        groups: [
          'Оператор лечащего врача',
          'Лечащий врач',
        ],
        module: 'l2_hosp',
        fullPageLayout: true,
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
      path: '/ui/billing',
      name: 'Billing',
      component: () => import('@/pages/Billing/index.vue'),
      meta: {
        title: 'Счет на оплату',
        groups: ['Счет: проект'],
      },
    },
    {
      path: '/ui/document-manager',
      name: 'document-manager',
      component: () => import('@/pages/DocumentManagement/DocumentManager.vue'),
      meta: {
        title: 'ДОУ',
        fullPageLayout: true,
        groups: ['ДОУ: просмотр документов'],
      },
    },
    {
      path: '/ui/working-time',
      name: 'WorkingTime',
      component: WorkingTime,
      meta: {
        narrowLayout: false,
        title: 'График рабочего времени',
        groups: ['График рабочего времени'],
      },
    },
    {
      path: '/ui/employees',
      name: 'employees',
      component: () => import('@/pages/Employees/Employees.vue'),
      meta: {
        title: 'Сотрудники',
        groups: ['Конструктор: Настройка организации'],
        fullPageLayout: true,
      },
    },
    {
      path: '/ui/construct/related-tube/:id',
      name: 'construct-related-tube',
      component: ConstructRelatedTube,
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
      path: '/ui/request-creation',
      name: 'request_creation',
      component: RequestCreation,
      meta: {
        title: 'Создание и исполнение заявок',
        groups: ['Создание и исполнение заявок'],
      },
    },
    {
      path: '/ui/requests-fill',
      name: 'requests_fill',
      component: RequestsFill,
      meta: {
        title: 'Заполнение заявок',
        groups: ['Заполнение заявок'],
      },
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
