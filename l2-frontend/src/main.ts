import Vue from 'vue';

// @ts-ignore
import * as actions from './store/action-types';
import store from './store';
import './styles/index.scss';
import registerHooks from './registerHooks';
import registerVue from './registerVue';

registerVue();

// eslint-disable-next-line no-new
new Vue({
  el: '#app',
  store,
  components: {
    LaboratoryTune: () => import('@/forms/LaboratoryTune.vue'),
  },
  data: {
    timeouts: {},
  },
  computed: {
    inLoading() {
      return this.$store.getters.inLoading;
    },
    loadingLabel() {
      return this.$store.getters.loadingLabel;
    },
    loaderInHeader() {
      return this.$store.getters.loaderInHeader;
    },
  },
  watch: {
    inLoading(n, o) {
      if (n && !o) {
        // @ts-ignore
        window.sl();
      }
      if (!n && o) {
        // @ts-ignore
        window.hl();
      }
    },
  },
  created() {
    Promise.all([
      this.$store.dispatch(actions.INC_LOADING),
      this.$store.dispatch(actions.GET_ALL_DEPARTMENTS),
      this.$store.dispatch(actions.GET_BASES),
      this.$store.dispatch(actions.GET_USER_DATA),
      this.$store.dispatch(actions.LOAD_HOSPITALS),
    ]).then(() => {
      this.$store.dispatch(actions.DEC_LOADING);
    });

    registerHooks(this);
  },
});
