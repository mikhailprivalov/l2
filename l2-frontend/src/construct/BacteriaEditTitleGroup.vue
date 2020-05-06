<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" min-width="40%"
         max-width="40%" width="100%" marginLeftRight="auto" margin-top="20%">
    <span slot="header">Настройка группы</span>
    <div slot="body" style="min-height: 20px" class="directions-manage">
      <input type="text" v-model="group_obj.title">
       <p>
         Скрыть
         <input type="checkbox" id="checkbox" v-model="group_obj.hide">
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
  import * as action_types from "../store/action-types";
  import bacteria_point from '../api/bacteria-point'

    export default {
      name: "BacteriaEditTitleGroup",
      components: {Modal, },
      props: {
      typesObject: {
        type: String,
        required: true
      },
      group_obj: {
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
        this.$root.$emit('hide_ge');
        if (this.$refs.modal) {
          this.$refs.modal.$el.style.display = 'none'
        }
      },
      async updateGroup() {
        await this.$store.dispatch(action_types.INC_LOADING);
        const {ok, message} = await bacteria_point.updateGroup({'TypesObject': this.typesObject ,'typeGroups': this.typesGroups,
        'obj':{'pk': this.group_obj.pk, 'title': this.group_obj.title, 'hide': this.group_obj.hide} });
        if (ok) {
          okmessage('Группа сохранён', `${this.group_obj.title}`)
        } else {
          errmessage('Ошибка', message)
        }
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      },
    }
</script>

<style scoped lang="scss">
  .directions-manage {
    width: 100%;
    height: 60%;
    display: flex;
    align-items: stretch;
    flex-direction: column;
    flex-wrap: nowrap;
    align-content: stretch;
    & > div {
      align-self: stretch;
    }
  }
  p {
    display: flex;
    padding-top: 10px }

</style>
