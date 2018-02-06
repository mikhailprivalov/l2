<template>
  <div ref="root" class="split content">
    <div ref="ct" style="display: flex">
      <div ref="tl" class="split content">
        <patient-picker v-model="selected_card" directive_from_need="false" search_results="false" history_n="false">
          <div v-if="can_create_directions" slot="for_card" class="text-right">
            <a :href="directions_url">Создать направления</a>
          </div>
        </patient-picker>
      </div>
      <div ref="tr" class="split content" style="overflow: visible;display: flex;padding-bottom: 0">
        <statistics-ticket-creator :base="selected_card.base" :card_pk="selected_card.pk"/>
      </div>
    </div>
    <div ref="cb" class="split content" style="padding: 0;">
      <statistics-tickets-viewer/>
    </div>
  </div>
</template>

<script>
  import Split from 'split.js'
  import PatientPicker from './PatientPicker'
  import StatisticsTicketCreator from './StatisticsTicketCreator'
  import StatisticsTicketsViewer from './StatisticsTicketsViewer'

  export default {
    name: 'statistics-tickets',
    components: {
      PatientPicker,
      StatisticsTicketCreator,
      StatisticsTicketsViewer
    },
    data() {
      return {
        selected_card: {pk: -1, base: {}, ofname: -1, operator: false, history_num: ''},
      }
    },
    computed: {
      directions_url() {
        return `/mainmenu/directions?base_pk=${this.selected_card.base.pk}&card_pk=${this.selected_card.pk}`
      },
      can_create_directions() {
        if('groups' in this.$store.getters.user_data) {
          for (let g of this.$store.getters.user_data.groups) {
            if (g === "Лечащий врач" || g === "Оператор лечащего врача") {
              return true
            }
          }
        }
        return false
      }
    },
    mounted() {
      let vm = this
      $(document).ready(function () {
        vm.resize()
        $(window).resize(function () {
          vm.resize()
        })

        Split([vm.$refs.ct, vm.$refs.cb], {
          direction: 'vertical',
          gutterSize: 5,
          cursor: 'row-resize',
          minSize: 200,
          sizes: [45, 55],
          onDrag: vm.resize
        })

        Split([vm.$refs.tl, vm.$refs.tr], {
          gutterSize: 5,
          cursor: 'col-resize',
          minSize: 200,
          onDrag: vm.resize,
          elementStyle: function (dimension, size, gutterSize) {
            return {
              'flex-basis': 'calc(' + size + '% - ' + gutterSize + 'px)'
            }
          },
          gutterStyle: function (dimension, gutterSize) {
            return {
              'flex-basis': gutterSize + 'px'
            }
          }
        })
      })
    },
    methods: {
      resize() {
        const $fp = $(this.$refs.root)
        $fp.height($(window).height() - $fp.position().top - 11)
      }
    }
  }
</script>

<style scoped>

</style>
