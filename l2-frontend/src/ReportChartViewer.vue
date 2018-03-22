<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true">
    <span slot="header">Построение графиков по полученным значениям</span>
    <div slot="body" style="min-width: 800px;">
      // TODO
    </div>
    <div slot="footer">
      // TODO
    </div>
  </modal>
</template>

<script>
  import Modal from './ui-cards/Modal'

  export default {
    name: 'report-chart-viewer',
    components: {Modal},
    props: {
      rows_data: {
        type: Array
      },
      directory: {
        type: Object
      },
    },
    computed: {
      params_types() {

      }
    },
    methods: {
      hide_modal() {
        this.$root.$emit('hide_report-chart-viewer')
        this.$refs.modal.$el.style.display = 'none'
      },
    }
  }
</script>

<style scoped lang="scss">

</style>
