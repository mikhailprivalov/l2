<template>
  <div ref="root">
    <div id="cont_left" class="split split-horizontal">
      <div id="left_top" class="split content">
        <patient-picker v-model="selected_card" directive_from_need="true" search_results="true">
          <div v-if="can_create_tickets" slot="for_card" class="text-right">
            <a :href="ticket_url">Создать статталон</a>
          </div>
        </patient-picker>
      </div>
      <div id="left_bottom" class="split content" style="padding: 0;">
        <researches-picker v-model="selected_researches"/>
      </div>
    </div>
    <div id="cont_right" class="split split-horizontal">
      <div id="right_top" class="split content" style="padding: 0;">
        <directions-history :patient_pk="selected_card.pk"/>
      </div>
      <div id="right_bottom" class="split content" style="padding: 0;">
        <selected-researches :operator="selected_card.operator" :ofname="selected_card.ofname"
                             :history_num="selected_card.history_num" :valid="patient_valid"
                             :researches="selected_researches" :base="selected_card.base" :card_pk="selected_card.pk"/>
      </div>
    </div>
    <results-viewer :pk="show_results_pk" v-if="show_results_pk > -1"/>
  </div>
</template>

<script>
  import ResearchesPicker from './ResearchesPicker'
  import PatientPicker from './PatientPicker'
  import SelectedResearches from './SelectedResearches'
  import DirectionsHistory from './DirectionsHistory'
  import ResultsViewer from './ResultsViewer'

  export default {
    components: {
      PatientPicker,
      ResearchesPicker,
      SelectedResearches,
      DirectionsHistory,
      ResultsViewer,
    },
    name: 'directions',
    data() {
      return {
        selected_card: {pk: -1, base: {}, ofname: -1, operator: false, history_num: ''},
        selected_researches: [],
        show_results_pk: -1,
      }
    },
    created() {
      let vm = this

      this.$root.$on('show_results', (pk) => {
        vm.show_results_pk = pk
      })

      this.$root.$on('hide_results', () => {
        vm.show_results_pk = -1
      })
    },
    mounted() {
      let vm = this
      $(document).ready(function () {
        vm.resize()
        $(window).resize(function () {
          vm.resize()
        })
        Split(['#cont_left', '#cont_right'], {
          gutterSize: 5,
          cursor: 'col-resize',
          minSize: 200,
          onDrag: vm.resize
        })

        Split(['#left_top', '#left_bottom'], {
          direction: 'vertical',
          gutterSize: 5,
          cursor: 'row-resize',
          minSize: 200,
          onDrag: vm.resize
        })

        Split(['#right_top', '#right_bottom'], {
          direction: 'vertical',
          gutterSize: 5,
          cursor: 'row-resize',
          minSize: 200,
          onDrag: vm.resize
        })
      })
      $(window).on('beforeunload', function () {
        if (vm.selected_card.pk !== -1 && vm.selected_researches.length > 0)
          return 'Исследования выбраны, но направления не созданы. Вы уверены, что хотите покинуть страницу?'
      })
    },
    methods: {
      resize() {
        const $fp = $(this.$refs.root)
        $fp.height($(window).height() - $fp.position().top - 5)
      }
    },
    computed: {
      patient_valid() {
        return this.selected_card.pk !== -1
      },
      ticket_url() {
        return `/mainmenu/statistics-tickets?base_pk=${this.selected_card.base.pk}&card_pk=${this.selected_card.pk}`
      },
      can_create_tickets() {
        if ('groups' in this.$store.getters.user_data) {
          for (let g of this.$store.getters.user_data.groups) {
            if (g === 'Оформление статталонов') {
              return true
            }
          }
        }
        return false
      }
    }
  }
</script>

<style scoped>
  #right_top {
    overflow: visible !important;
  }
</style>
