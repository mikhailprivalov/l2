<template>
  <div ref="root">
    <div id="cont_left" class="split split-horizontal">
      <div id="left_top" class="split content">
        <individual-picker v-model="selected_individual"/>
      </div>
      <div id="left_bottom" class="split content" style="padding: 0;">
        <researches-picker v-model="selected_researches" autoselect="report" :hidetemplates="true"/>
      </div>
    </div>
    <div id="cont_right" class="split split-horizontal">
      <div id="right_top" class="split content" style="padding: 0;">
        <results-report-viewer :individual_pk="selected_individual" :params="selected_params"
                               :params_directory="params_directory"/>
      </div>
      <div id="right_bottom" class="split content" style="padding: 0;box-shadow: none">
        <report-selected-researches :researches="selected_researches" v-model="selected_params"
                                    :params_directory="params_directory"/>
      </div>
    </div>
  </div>
</template>

<script>
  import ResearchesPicker from '../ui-cards/ResearchesPicker'
  import IndividualPicker from '../ui-cards/IndividualPicker'
  import ResultsReportViewer from '../ui-cards/ResultsReportViewer'
  import ReportSelectedResearches from '../ui-cards/ReportSelectedResearches'
  import researches_point from '../api/researches-point'
  import * as action_types from '../store/action-types'

  export default {
    components: {
      ResearchesPicker,
      IndividualPicker,
      ReportSelectedResearches,
      ResultsReportViewer,
    },
    name: 'results-report',
    data() {
      return {
        selected_individual: -1,
        selected_researches: [],
        selected_params: [],
        inLoad: false,
        params_directory: {}
      }
    },
    watch: {
      selected_researches() {
        let r_to_load = []
        for (let pk of this.selected_researches) {
          if (!(pk in this.params_directory)) {
            r_to_load.push(pk)
          }
        }
        this.load_params(r_to_load)
      }
    },
    mounted() {
      $(document).ready(() => {
        this.resize()
        $(window).resize(() => {
          this.resize()
        })
        Split(['#cont_left', '#cont_right'], {
          gutterSize: 5,
          cursor: 'col-resize',
          minSize: 200,
          onDrag: this.resize
        })

        Split(['#left_top', '#left_bottom'], {
          direction: 'vertical',
          gutterSize: 5,
          cursor: 'row-resize',
          minSize: 200,
          onDrag: this.resize
        })

        Split(['#right_top', '#right_bottom'], {
          direction: 'vertical',
          gutterSize: 5,
          cursor: 'row-resize',
          minSize: 200,
          onDrag: this.resize
        })
      })
    },
    methods: {
      resize() {
        const $fp = $(this.$refs.root)
        $fp.height($(window).height() - $fp.position().top - 5)
      },
      load_params(pks) {
        if (this.inLoad || pks.length === 0)
          return
        this.inLoad = true
        this.$store.dispatch(action_types.INC_LOADING)
        researches_point.getResearchesParams({pks}).then(data => {
          for(let r of data.researches) {
            this.params_directory[r.pk] = r
          }
          this.$root.$emit('params-load')
        }).finally(() => {
          this.$store.dispatch(action_types.DEC_LOADING)
          this.inLoad = false
        })
      }
    },
    computed: {}
  }
</script>

<style scoped>
  #right_top {
    overflow: visible !important;
  }
</style>
