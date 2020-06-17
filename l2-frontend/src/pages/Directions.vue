<template>
  <div class="root" :class="{noGrid: !hasGrid, hasGrid}">
    <div class="a">
      <patient-picker v-model="selected_card" directive_from_need="true" search_results="true" bottom_picker="true">
        <div slot="for_card" class="text-right">
          <div v-if="selected_researches.length > 0"
               style="margin-top: 5px;text-align: left">
            <table class="table table-bordered lastresults">
              <colgroup>
                <col width="180">
                <col>
                <col width="110">
                <col width="110">
              </colgroup>
              <tbody>
              <last-result :individual="selected_card.individual_pk" v-for="p in selected_researches" :key="p"
                           :research="p"/>
              </tbody>
            </table>
          </div>
        </div>
        <div slot="for_card_bottom" class="bottom-inner" v-if="selected_card.pk >= 0">
          <!--<a href="#" @click.prevent="do_show_rmis_send_directions" v-if="selected_card.is_rmis">
            <span>Направить в другую МО</span>
          </a>-->
          <div class="dropup">
            <button class="btn btn-blue-nb btn-ell dropdown-toggle" type="button" data-toggle="dropdown"
                    style="text-align: right!important;border-radius: 0;width: 100%">
              Печатные формы <span class="caret"></span>
            </button>
            <ul class="dropdown-menu">
              <li v-for="f in forms" v-if="selected_card.base.internal_type || f.not_internal">
                <a :href="f.url" target="_blank" class="ddm">{{f.title}}</a>
              </li>
            </ul>
          </div>
          <a href="#" class="a-under" @click.prevent="do_show_rmis_directions" v-if="selected_card.is_rmis">
            <span>Направления из РМИС</span>
          </a>
          <a class="a-under" :href="report_url">
            <span>Отчёт по результатам</span>
          </a>
          <a class="a-under" v-if="can_create_tickets" :href="ticket_url">
            <span>Создать статталон</span>
          </a>
        </div>
      </patient-picker>
    </div>
    <div class="b gutter gutter-col gutter-column-1"></div>
    <div class="c">
      <directions-history :patient_pk="selected_card.pk"/>
    </div>
    <div class="d gutter gutter-row gutter-row-1"></div>
    <div class="e">
      <researches-picker v-model="selected_researches"/>
    </div>
    <div class="f gutter gutter-col gutter-column-2"></div>
    <div class="g">
      <selected-researches :operator="selected_card.operator" :ofname="selected_card.ofname"
                           :main_diagnosis="selected_card.main_diagnosis"
                           :history_num="selected_card.history_num" :valid="patient_valid"
                           :researches="selected_researches" :base="selected_card.base" :card_pk="selected_card.pk"/>
    </div>
    <results-viewer :pk="show_results_pk" v-if="show_results_pk > -1"/>
    <rmis-directions-viewer v-if="show_rmis_directions && selected_card.is_rmis" :card="selected_card"/>
    <!--<rmis-send-directions v-if="show_rmis_send_directions && selected_card.is_rmis" :card="selected_card"/>-->
  </div>
</template>

<script>
  import Split from "split-grid";
  import ResearchesPicker from '../ui-cards/ResearchesPicker'
  import PatientPicker from '../ui-cards/PatientPicker'
  import SelectedResearches from '../ui-cards/SelectedResearches'
  import DirectionsHistory from '../ui-cards/DirectionsHistory'
  import ResultsViewer from '../modals/ResultsViewer'
  import RmisDirectionsViewer from '../modals/RmisDirectionsViewer'
  import LastResult from '../ui-cards/LastResult'
  import forms from '../forms';

  export default {
    components: {
      PatientPicker,
      ResearchesPicker,
      SelectedResearches,
      DirectionsHistory,
      ResultsViewer,
      RmisDirectionsViewer,
      LastResult,
    },
    name: 'directions',
    data() {
      return {
        selected_card: {
          pk: -1,
          base: {},
          ofname: -1,
          ofname_dep: -1,
          individual_pk: -1,
          operator: false,
          is_rmis: false,
          history_num: '',
          family: '',
          name: '',
          twoname: '',
          birthday: '',
          age: '',
          main_diagnosis: '',
        },
        selected_researches: [],
        show_results_pk: -1,
        show_rmis_directions: false,
        show_rmis_send_directions: false,
        diagnos: '',
        fin: -1,
        hasGrid: Modernizr.cssgrid,
      }
    },
    created() {
      this.$root.$on('show_results', (pk) => {
        this.show_results_pk = pk
      })

      this.$root.$on('hide_results', () => {
        this.show_results_pk = -1
      })

      this.$root.$on('hide_rmis_directions', () => {
        this.show_rmis_directions = false
        this.show_rmis_send_directions = false
      })

      this.$root.$on('update_diagnos', (diagnos) => {
        this.diagnos = diagnos
      })

      this.$root.$on('update_fin', (fin) => {
        this.fin = fin
      })
    },
    mounted() {
      if (this.hasGrid) {
        Split({
          columnGutters: [{
            track: 1,
            element: document.querySelector('.gutter-column-1'),
          }, {
            track: 1,
            element: document.querySelector('.gutter-column-2'),
          }],
          rowGutters: [{
            track: 1,
            element: document.querySelector('.gutter-row-1'),
          }],
          minSize: 200,
        })
      }
      $(window).on('beforeunload', () => {
        if (this.selected_card.pk === -1 || this.selected_researches.length <= 0 || document.activeElement && document.activeElement.href && document.activeElement.href.startsWith('sip:')) {
          if (document.activeElement) {
            $(document.activeElement).blur()
          }
        } else {
          return 'Исследования выбраны, но направления не созданы. Вы уверены, что хотите покинуть страницу?'
        }
      })
    },
    methods: {
      do_show_rmis_directions() {
        this.show_rmis_directions = true
      },
      do_show_rmis_send_directions() {
        this.show_rmis_send_directions = true
      }
    },
    computed: {
      forms() {
        return forms.map(f => {
          return {
            ...f, url: f.url.kwf({
              card: this.selected_card.pk,
              individual: this.selected_card.individual_pk,
            })
          }
        });
      },
      patient_valid() {
        return this.selected_card.pk !== -1
      },
      ticket_url() {
        return `/mainmenu/statistics-tickets?base_pk=${this.selected_card.base.pk}&card_pk=${this.selected_card.pk}&ofname=${this.selected_card.ofname}&ofname_dep=${this.selected_card.ofname_dep}`
      },
      report_url() {
        return `/mainmenu/results_report?individual_pk=${this.selected_card.individual_pk}&base_pk=${this.selected_card.base.pk}&card_pk=${this.selected_card.pk}`
      },
      can_create_tickets() {
        if ('groups' in this.$store.getters.user_data) {
          for (let g of this.$store.getters.user_data.groups) {
            if (g === 'Оформление статталонов' || g === 'Лечащий врач' || g === 'Оператор лечащего врача') {
              return true
            }
          }
        }
        return false
      },
      step() {
        if (this.patient_valid) {
          if (this.selected_researches.length > 0) {
            if (this.diagnos !== '') {
              if (this.fin === -1) {
                return 3
              }
              return 4
            }
            return 2
          }
          return 1
        }
        return 0
      }
    },
    watch: {
      step() {
        this.$root.$emit('set-step', this.step)
      }
    }
  }
</script>

<style scoped lang="scss">
  .noGrid .gutter {
    display: none;
  }

  .noGrid {
    // FALLBACK FROM CSS GRID TO FLEXBOX START

    display: flex;
    flex-wrap: wrap;
    flex-direction: row;

    justify-items: stretch;
    align-items: stretch;

    & > div {
      flex-basis: 50%;
    }

    // FALLBACK FROM CSS GRID TO FLEXBOX END
  }

  .root {
    position: absolute;
    top: 36px;
    left: 0;
    right: 0;
    bottom: 0;

    &.hasGrid {
      display: grid;
      grid-template-columns: 1fr 5px 1fr;
      grid-template-rows: 1fr 5px 1fr;
      gap: 0;
      height: calc(calc(100vh - calc(100vh - 100%)) - 36px);
    }

    .a {
      grid-area: 1 / 1 / 2 / 2;

      padding-right: 0;
      padding-bottom: 0;
      text-align: left;
      background: #fff;
    }

    .b {
      grid-area: 1 / 2 / 2 / 3;
      display: block;
    }

    .c {
      grid-area: 1 / 3 / 2 / 4;

      padding-left: 0;
      padding-bottom: 0;
      text-align: left;
      background: #fff;
    }

    .d {
      grid-area: 2 / 1 / 3 / 4;
      display: block;
    }

    .e {
      grid-area: 3 / 1 / 4 / 2;

      padding-top: 0;
      padding-right: 0;
      text-align: left;
      background: #fff;
    }

    .f {
      grid-area: 3 / 2 / 4 / 3;
      display: block;
    }

    .g {
      grid-area: 3 / 3 / 4 / 4;

      padding-top: 0;
      padding-left: 0;
      text-align: left;
      background: #fff;
    }

    @media (max-width: 760px) {
      grid-template-columns: 1fr;
      grid-template-rows: repeat(4, 320px);
      gap: 5px;

      & > div {
        padding: 5px!important;
      }

      .a {
        grid-area: 1 / 1 / 2 / 2;
      }

      .b {
        display: none
      }

      .c {
        grid-area: 2 / 1 / 3 / 2;
      }

      .d {
        display: none
      }

      .e {
        grid-area: 3 / 1 / 4 / 2;
      }

      .f {
        display: none
      }

      .g {
        grid-area: 4 / 1 / 5 / 2;
      }
    }

    & > div {
      padding: 5px;

      & > div {
        border: 1px solid #AAB2BD;
        position: relative;
      }
    }
  }

  #right_top {
    overflow: visible !important;
  }

  .lastresults {
    table-layout: fixed;
    padding: 0;
    margin: 0;
    color: #000;
    background-color: #ffdb4d;
    border-color: #000;

    /deep/ th, /deep/ td {
      border-color: #000;
    }

    /deep/ a {
      color: #000;
      text-decoration: dotted underline;
    }

    /deep/ a:hover {
      text-decoration: none;
    }
  }

  .fli {
    text-decoration: underline;
    margin-left: 5px;
  }

  .fli:hover {
    text-decoration: none;
  }

  .hasGrid {
    .gutter-col {
      cursor: col-resize;
      position: relative;
      padding: 0 !important;
      width: 5px;

      &::after {
        position: absolute;
        height: 10px;
        width: 1px;
        background-color: gray;
        top: calc(50% - 5px);
        left: 2px;

        content: " ";
      }
    }

    .gutter-row {
      cursor: row-resize;
      position: relative;
      padding: 0 !important;
      height: 5px;

      &::before {
        position: absolute;
        height: 1px;
        width: 10px;
        background-color: gray;
        top: 2px;
        left: calc(25% - 5px);

        content: " ";
      }

      &::after {
        position: absolute;
        height: 1px;
        width: 10px;
        background-color: gray;
        top: 2px;
        right: calc(25% - 5px);

        content: " ";
      }
    }
  }
</style>
