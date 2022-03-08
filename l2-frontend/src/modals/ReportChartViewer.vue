<template>
  <Modal
    ref="modal"
    show-footer="true"
    white-bg="true"
    @close="hide_modal"
  >
    <span slot="header">Построение графиков по полученным значениям</span>
    <div
      slot="body"
      style="min-width: 800px;"
    >
      // TODO
    </div>
    <div slot="footer">
      // TODO
    </div>
  </Modal>
</template>

<script lang="ts">
import Modal from '../ui-cards/Modal.vue';

export default {
  name: 'ReportChartViewer',
  components: { Modal },
  props: {
    rows_data: {
      type: Array,
    },
    directory: {
      type: Object,
    },
  },
  methods: {
    hide_modal() {
      this.$root.$emit('hide_report-chart-viewer');
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
    },
  },
};
</script>

<style scoped lang="scss">

</style>
