<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" min-width="85%" margin-top>
    <span slot="header">Направить в другую МО. Пациент: {{card.family}} {{card.name}} {{card.twoname}},
      {{card.birthday}} ({{card.age}})</span>
    <div slot="body" style="min-height: 200px" class="directions-manage">

    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-4">
        </div>
        <div class="col-xs-4">
        </div>
        <div class="col-xs-4">
          <button type="button" @click="hide_modal" class="btn btn-primary-nb btn-blue-nb">Закрыть</button>
        </div>
      </div>
    </div>
  </modal>
</template>

<script>
import Modal from '../ui-cards/Modal.vue';

export default {
  name: 'rmis-send-directions',
  components: { Modal },
  props: {
    card: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {};
  },
  methods: {
    hide_modal() {
      this.$root.$emit('hide_rmis_directions');
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
    },
  },
};
</script>

<style scoped lang="scss">
  .modal-mask {
    align-items: stretch !important;
    justify-content: stretch !important;
  }

  ::v-deep .panel-flt {
    margin: 41px;
    align-self: stretch !important;
    width: 100%;
    display: flex;
    flex-direction: column;
  }

  ::v-deep .panel-body {
    flex: 1;
    padding: 0;
    height: calc(100% - 91px);
    min-height: 200px;
  }
</style>
