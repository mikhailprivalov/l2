<template>
  <div style="height: 100%;width: 100%;position: relative">
    <div class="content-picker" style="overflow: auto">
      <div style="width: 100%;display: contents">
        <research-params-select v-for="r in params_researches" v-model="r.selected_params" :research="r" :key="r.pk"/>
        <div class="text-center" v-if="params_researches.length === 0"
             style="width: 100%;display: flex;align-items: center;justify-content: center;">Ничего не выбрано</div>
      </div>
    </div>
  </div>
</template>

<script>
import _ from 'lodash';
import ResearchParamsSelect from './ResearchParamsSelect.vue';

export default {
  name: 'report-selected-researches',
  components: {
    ResearchParamsSelect,
  },
  props: {
    researches: {
      type: Array,
      required: true,
    },
    params_directory: {
      type: Object,
      required: true,
    },
    value: {},
  },
  data() {
    return {
      params_researches: [],
    };
  },
  computed: {
    selected_params() {
      let p = [];
      for (const rp of this.params_researches) {
        p = _.union(p, rp.selected_params);
      }
      return p;
    },
  },
  created() {
    this.$root.$on('researches-picker:clear_all', this.clear_all);
    this.$root.$on('params-load', this.params_researches_update);
  },
  methods: {
    has_in_directory(pk) {
      return pk in this.params_directory;
    },
    get_research(pk) {
      return this.params_directory[pk];
    },
    clear_all() {
      this.$root.$emit('researches-picker:deselect_all');
    },
    params_researches_update() {
      this.params_researches.length = 0;

      for (const rpk of Object.keys(this.params_directory)) {
        if (this.researches.includes(parseInt(rpk, 10))) {
          this.params_researches.push(this.params_directory[rpk]);
          continue;
        }
        this.params_directory[rpk].selected_params = [];
      }
    },
  },
  watch: {
    params_directory: {
      handler() {
        this.params_researches_update();
      },
      deep: true,
    },
    researches() {
      this.params_researches_update();
      this.$root.$emit('report-researches:update');
    },
    selected_params() {
      this.$emit('input', this.selected_params);
    },
  },
};
</script>

<style scoped>
  .top-picker, .bottom-picker {
    height: 34px;
    background-color: #AAB2BD;
    position: absolute;
    left: 0;
    right: 0;
  }

  .top-picker {
    top: 0;
  }

  .top-inner, .content-picker, .bottom-picker {
    display: flex;
    flex-wrap: wrap;
    justify-content: stretch;
    align-content: center;
    align-items: stretch;
    overflow-y: auto;
  }

  .content-picker {
    align-content: flex-start;
  }

  .top-inner {
    position: absolute;
    left: 180px;
    top: 0;
    right: 0;
    height: 34px;
    align-content: stretch;
    overflow: hidden;
  }

  .top-picker .form-control {
    width: 180px;
    border-radius: 0;
    border: none;
    border-bottom: 1px solid #AAB2BD;
  }

  .top-inner-select {
    align-self: stretch;
    display: flex;
    align-items: center;
    padding: 1px 2px 1px;
    color: #000;
    background-color: #fff;
    text-decoration: none;
    cursor: pointer;
    flex: 1;
    margin: 0;
    font-size: 12px;
    min-width: 0;
  }

  .top-inner-select {
    background-color: #AAB2BD;
    color: #fff;
  }

  .research-select {
    flex: 0 1 auto;
    width: 25%;
    height: 34px;
    border: 1px solid #6C7A89 !important;
  }

  .top-inner-select.active {
    background: #049372 !important;
    color: #fff;
  }

  .top-inner-select.disabled {
    color: #fff;
    cursor: not-allowed;
    opacity: .8;
    background-color: rgba(255, 255, 255, .7) !important;
  }

  .top-inner-select span {
    display: block;
    text-overflow: ellipsis;
    overflow: hidden;
    word-break: keep-all;
    max-height: 2.2em;
    line-height: 1.1em;
    margin: 0 auto;
  }

  .top-inner-select:hover {
    background-color: #434a54;
  }

  .research-select:hover {
    box-shadow: inset 0 0 8px rgba(0, 0, 0, .8) !important;
  }

  .content-picker, .content-none {
    position: absolute;
    top: 0;
    bottom: 0;
    left: 0;
    right: 0;
    overflow-y: auto;
  }

  .bottom-picker {
    bottom: 0;
    align-content: stretch;
    overflow: hidden;
  }

  .bottom-picker .top-inner-select span {
    margin: 0 auto;
    text-align: center;
  }
</style>
