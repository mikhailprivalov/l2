<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" min-width="40%"
         max-width="40%" width="100%" marginLeftRight="auto" margin-top="20%">
    <span slot="header">Настройка группы</span>
    <div slot="body" style="min-height: 200px" class="manage">
      <div class="form-group">
        <label for="change-group-title">
          Название
        </label>

        <input id="change-group-title" class="form-control" v-model="group_obj.title">
      </div>
      <div class="checkbox">
        <label>
          <input type="checkbox" v-model="group_obj.hide"> Скрыть
        </label>
      </div>
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
import Modal from '../ui-cards/Modal.vue';
import * as actions from '../store/action-types';
import bacteriaPoint from '../api/bacteria-point';

export default {
  name: 'BacteriaEditTitleGroup',
  components: { Modal },
  props: {
    typesObject: {
      type: String,
      required: true,
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
        this.$refs.modal.$el.style.display = 'none';
      }
    },
    async updateGroup() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await bacteriaPoint.updateGroup({
        TypesObject: this.typesObject,
        typeGroups: this.typesGroups,
        obj: { pk: this.group_obj.pk, title: this.group_obj.title, hide: this.group_obj.hide },
      });
      if (ok) {
        window.okmessage('Группа сохранена', `${this.group_obj.title}`);
      } else {
        window.errmessage('Ошибка', message);
      }
      await this.$store.dispatch(actions.DEC_LOADING);
      this.hide_modal();
    },
  },
};
</script>

<style scoped lang="scss">
  .manage {
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
    padding-top: 10px
  }

</style>
