<template>
  <div ref="root">
    <div ref="ct" style="display: flex" class="split content">
      <div ref="tl" class="split content">
        <patient-picker v-model="selected_card" directive_from_need="false" search_results="false" history_n="false"/>
      </div>
      <div ref="tr" class="split content">

      </div>
    </div>
    <div ref="cb" class="split content">

    </div>
  </div>
</template>

<script>
  import Split from 'split.js'
  import PatientPicker from './PatientPicker'

  export default {
    name: 'statistics-tickets',
    components: {
      PatientPicker
    },
    data() {
      return {
        selected_card: {pk: -1, base: {}, ofname: -1, operator: false, history_num: ''},
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
        $fp.height($(window).height() - $fp.position().top - 5)
      }
    }
  }
</script>

<style scoped>

</style>
