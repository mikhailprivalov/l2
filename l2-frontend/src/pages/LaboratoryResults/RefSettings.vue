<template>
  <Modal
    ref="modal"
    show-footer="true"
    white-bg="true"
    max-width="50%"
    min-width="800px"
    width="50%"
    margin-left-right="auto"
    margin-top="48px"
    @close="close"
  >
    <span slot="header">Настройка референсов результата</span>
    <div
      slot="body"
      style="min-height: 340px"
    >
      <table class="table table-bordered table-condensed">
        <colgroup>
          <col width="200">
          <col width="200">
          <col>
        </colgroup>
        <thead>
          <tr>
            <th>Фракция</th>
            <th>Выбор референса</th>
            <th>Референс</th>
          </tr>
        </thead>
        <tbody>
          <!-- eslint-disable-next-line vue/require-v-for-key -->
          <tr v-for="r in result">
            <RefSettingsRow :r="r" />
          </tr>
        </tbody>
      </table>
    </div>
    <div slot="footer">
      <div class="row">
        <div
          class="col-xs-5"
          style="float: right"
        >
          <button
            class="btn btn-primary-nb btn-blue-nb"
            type="button"
            @click="closeWithFastHide"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script lang="ts">
import Modal from '@/ui-cards/Modal.vue';
import RefSettingsRow from '@/pages/LaboratoryResults/RefSettingsRow.vue';

export default {
  name: 'RefSettings',
  components: { RefSettingsRow, Modal },
  props: {
    close: {
      type: Function,
      required: true,
    },
    result: {
      type: Array,
      required: true,
    },
  },
  methods: {
    closeWithFastHide() {
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
      this.close();
    },
  },
};
</script>
