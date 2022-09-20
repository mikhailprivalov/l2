import Vue from 'vue';

import promiseFinally from 'promise.prototype.finally';
// @ts-ignore
import VueAutosize from 'vue-autosize';
// @ts-ignore
import VueCollapse from 'vue2-collapse';
// @ts-ignore
import frag from 'vue-frag';
// @ts-ignore
import VuejsDialog from 'vuejs-dialog';
import PortalVue from 'portal-vue';
// @ts-ignore
import Inputmask from 'inputmask';
import Toast from 'vue-toastification';
import VueFullscreen from 'vue-fullscreen';
import 'vue-toastification/dist/index.css';
// @ts-ignore
import plural from 'plural-ru';
import moment from 'moment';
import VueFormulate from '@braid/vue-formulate';
import { ru } from '@braid/vue-formulate-i18n';
import { sendEvent } from '@/metrics';
import error2json from '@stdlib/error-to-json';
import VueTippy from './vue-tippy-2.1.3/dist/vue-tippy.min';

import api from './api';

import ReplaceAppendModal from './ui-cards/ReplaceAppendModal.vue';

export default (): void => {
  Vue.prototype.$orgTitle = () => window.ORG_TITLE;
  Vue.prototype.$asVI = () => window.SYSTEM_AS_VI;
  Vue.prototype.$systemTitle = () => (Vue.prototype.$asVI() ? 'VI' : 'L2');
  Vue.prototype.$l2LogoClass = () => window.L2_LOGO_CLASS;
  Vue.prototype.$api = api;

  const VueInputMask = {
    install(Vue$) {
      Vue$.directive('mask', {
        bind(el, binding) {
          Inputmask(binding.value).mask(el);
        },
      });
    },
  };

  Vue.directive('frag', frag);
  Vue.use(VuejsDialog, {
    okText: 'Подтвердить',
    cancelText: 'Отмена',
    animation: 'fade',
  });
  Vue.use(VueAutosize);
  Vue.use(VueTippy);
  Vue.use(VueInputMask);
  Vue.use(VueCollapse);
  Vue.use(PortalVue);
  Vue.use(VueFullscreen);
  Vue.use(VueFormulate, {
    plugins: [ru],
    locale: 'ru',
  });
  Vue.prototype.$api = api;
  Vue.filter('pluralAge', (amount) => `${amount} ${plural(amount, 'год', 'года', 'лет')}`);
  Vue.filter('pluralRecords', (amount) => `${amount} ${plural(amount, 'запись', 'записи', 'записей')}`);
  Vue.filter('pluralCount', (amount) => `${amount} ${plural(amount, 'штука', 'штуки', 'штук')}`);
  Vue.filter('formatDate', (s) => moment(s).format('DD.MM.YYYY'));
  Vue.filter('formatDateShort', (s) => moment(s).format('DD.MM'));

  Vue.directive('click-outside', {
    bind(el, binding, vnode) {
      // @ts-ignore
      // eslint-disable-next-line no-param-reassign
      el.clickOutsideEvent = function (event) {
        if (!(el === event.target || el.contains(event.target))) {
          // @ts-ignore
          vnode.context[binding.expression](event);
        }
      };
      // @ts-ignore
      document.body.addEventListener('click', el.clickOutsideEvent);
    },
    unbind(el) {
      // @ts-ignore
      document.body.removeEventListener('click', el.clickOutsideEvent);
    },
  });

  promiseFinally.shim();

  // @ts-ignore
  Vue.dialog.registerComponent('replace-append-modal', ReplaceAppendModal);
  Vue.use(Toast, {
    transition: 'Vue-Toastification__bounce',
    maxToasts: 20,
    newestOnTop: false,
  });

  Vue.config.errorHandler = (error, vm) => {
    console.error(error);
    vm.$root.$emit('msg', 'error', `Vue Error: ${error}`);
    sendEvent('vue_error', { error: error2json(error) });
  };
};
