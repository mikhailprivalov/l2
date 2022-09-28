<template>
  <div
    ref="root"
    class="content-root"
  >
    <div
      id="cont_left"
      class="split split-horizontal"
    >
      <div
        id="left_top"
        class="split content"
      >
        <IndividualPicker v-model="selected_individual" />
      </div>
      <div
        id="left_bottom"
        class="split content"
        style="padding: 0;"
      >
        <ResearchesPicker
          v-model="selected_researches"
          autoselect="report"
          :hidetemplates="true"
        />
      </div>
    </div>
    <div
      id="cont_right"
      class="split split-horizontal"
    >
      <div
        id="right_top"
        class="split content"
        style="padding: 0;"
      >
        <ResultsReportViewer
          :individual_pk="selected_individual"
          :params="selected_params"
          :params_directory="params_directory"
        />
      </div>
      <div
        id="right_bottom"
        class="split content"
        style="padding: 0;box-shadow: none"
      >
        <ReportSelectedResearches
          v-model="selected_params"
          :researches="selected_researches"
          :params_directory="params_directory"
        />
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import Split from 'split.js';

import ResearchesPicker from '@/ui-cards/ResearchesPicker.vue';
import IndividualPicker from '@/ui-cards/IndividualPicker.vue';
import ResultsReportViewer from '@/ui-cards/ResultsReportViewer.vue';
import ReportSelectedResearches from '@/ui-cards/ReportSelectedResearches.vue';
import researchesPoint from '@/api/researches-point';
import * as actions from '@/store/action-types';

export default {
  name: 'ResultsReport',
  components: {
    ResearchesPicker,
    IndividualPicker,
    ReportSelectedResearches,
    ResultsReportViewer,
  },
  data() {
    return {
      selected_individual: -1,
      selected_researches: [],
      selected_params: [],
      inLoad: false,
      params_directory: {},
    };
  },
  computed: {},
  watch: {
    selected_researches() {
      const toLoad = [];
      for (const pk of this.selected_researches) {
        if (!(pk in this.params_directory)) {
          toLoad.push(pk);
        }
      }
      this.load_params(toLoad);
    },
  },
  mounted() {
    window.$(document).ready(() => {
      this.resize();
      window.$(window).resize(() => {
        this.resize();
      });
      Split(['#cont_left', '#cont_right'], {
        gutterSize: 5,
        cursor: 'col-resize',
        minSize: 200,
        onDrag: this.resize,
      });

      Split(['#left_top', '#left_bottom'], {
        direction: 'vertical',
        gutterSize: 5,
        cursor: 'row-resize',
        minSize: 200,
        onDrag: this.resize,
      });

      Split(['#right_top', '#right_bottom'], {
        direction: 'vertical',
        gutterSize: 5,
        cursor: 'row-resize',
        minSize: 200,
        onDrag: this.resize,
      });
    });
  },
  methods: {
    resize() {
      const $fp = window.$(this.$refs.root);
      $fp.height(window.$(window).height() - $fp.position().top - 5);
    },
    load_params(pks) {
      if (this.inLoad || pks.length === 0) return;
      this.inLoad = true;
      this.$store.dispatch(actions.INC_LOADING);
      researchesPoint.getResearchesParams({ pks }).then((data) => {
        for (const r of data.researches) {
          this.params_directory[r.pk] = r;
        }
        this.$root.$emit('params-load');
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
        this.inLoad = false;
      });
    },
  },
};
</script>

<style scoped>
  #right_top {
    overflow: visible !important;
  }

  .content-root {
    position: absolute;
    top: 41px;
    right: 5px;
    bottom: 5px;
    left: 5px;
  }
</style>
