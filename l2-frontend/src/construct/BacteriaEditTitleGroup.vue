<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" min-width="40%"
         max-width="40%" width="100%" marginLeftRight="auto" margin-top="20%">
    <span slot="header">Настройка группы</span>
    <div slot="body" style="min-height: 20px" class="registry-body">
      <input type="text" v-model="group_title.title">
       <p>
         Скрыть
         <input type="checkbox" id="checkbox" v-model="group_title.hide">
       </p>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-4">
          <button type="button" @click="updateGroup" class="btn btn-primary-nb btn-blue-nb">
            Сохранить
          </button>
        </div>
        <div class="col-xs-4">
          <button type="button" @click="hide_modal" class="btn btn-primary-nb btn-blue-nb">
            Отмена
          </button>
        </div>
      </div>
    </div>
  </modal>

</template>

<script>
  import Modal from '../ui-cards/Modal'
  import bacteria_point from '../api/bacteria-point'
  import * as action_types from "../store/action-types";

    export default {
      name: "BacteriaEditTitleGroup",
      components: {Modal, },
      props: {
      group_pk: {
        type: Number,
        required: true
      },
      group_title: {
        type: Object,
        required: true,
      },
      typesGroups: {
        type: String,
        required: true,
      },
    },
      methods: {
       hide_modal() {
        this.$root.$emit('hide_fte')
        if (this.$refs.modal) {
          this.$refs.modal.$el.style.display = 'none'
        }
      },
        async updateGroup() {
        this.$store.dispatch(action_types.INC_LOADING).then();

        this.$store.dispatch(action_types.DEC_LOADING).then()
      },
      },
    }
</script>

<style scoped lang="scss">
  .directions-manage {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: stretch;
    flex-direction: row;
    flex-wrap: nowrap;
    align-content: stretch;
    & > div {
      align-self: stretch;
    }
  }
  p { padding-top: 10px }

</style>
