<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" max-width="680px" width="100%"
         marginLeftRight="auto" margin-top>
    <span slot="header">Сообщения</span>
    <div slot="body" style="min-height: 200px" class="registry-body">
      <table class="table table-bordered table-condensed table-sm-pd layout">
        <colgroup>
          <col width="100"/>
          <col width="160"/>
          <col width="370"/>
        </colgroup>
        <thead>
        <tr>
          <th>Дата</th>
          <th>Создатель</th>
          <th>Сообщение</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="r in rows" :key="r.date">
          <td>{{r.createdAt}}</td>
          <td>{{r.who_create}}</td>
          <td><span v-html="r.message.replace(/\n/g, '<br/>')"></span></td>
        </tr>
        </tbody>
      </table>
      <div style="margin: 0 auto; width: 200px">
        <button class="btn btn-primary-nb btn-blue-nb"
                @click="edit(-1)"
                type="button"><i class="fa fa-plus"></i> Создать сообщение
        </button>
      </div>
      <modal v-if="edit_pk > -2" ref="modalEdit" @close="hide_edit" show-footer="true" white-bg="true" max-width="710px"
             width="100%" marginLeftRight="auto" margin-top>
        <span slot="header">Создание записи</span>
        <div slot="body" style="min-height: 200px;padding: 10px" class="registry-body">
          <div class="form-group">
            <label>Введите текст:</label>
            <textarea class="form-control" rows="10" v-model="data"/>
          </div>
        </div>
        <div slot="footer">
          <div class="row">
            <div class="col-xs-4">
              <button @click="hide_edit" class="btn btn-primary-nb btn-blue-nb" type="button">
                Отмена
              </button>
            </div>
            <div class="col-xs-4">
              <button :disabled="!valid" @click="save()" class="btn btn-primary-nb btn-blue-nb" type="button">
                Сохранить
              </button>
            </div>
          </div>
        </div>
      </modal>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-12">
          <div class="col-xs-4"/>
          <div class="col-xs-4">
            <button @click="hide_modal" class="btn btn-primary-nb btn-blue-nb" type="button">
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </div>
  </modal>
</template>

<script lang="ts">
import Modal from '@/ui-cards/Modal.vue';
import * as actions from '@/store/action-types';

export default {
  name: 'MessagesData',
  components: { Modal },
  props: {
    plan_pk: {
      type: Number,
      required: false,
    },
    card_pk: {
      type: Number,
      required: false,
    },
  },
  data() {
    return {
      rows: [],
      edit_pk: -2,
      data: '',
    };
  },
  created() {
    this.load_data(this.plan_pk);
  },
  computed: {
    valid() {
      return this.data !== '';
    },
  },
  methods: {
    async edit(pk) {
      this.data = '';
      this.edit_pk = pk;
    },
    hide_modal() {
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
      this.$root.$emit('hide_messages_data');
    },
    hide_edit() {
      if (this.$refs.modalEdit) {
        this.$refs.modalEdit.$el.style.display = 'none';
      }
    },
    async load_data(plan_pk) {
      this.$store.dispatch(actions.INC_LOADING);
      const { rows } = await this.$api('plans/plan-messages', { plan_pk });
      this.rows = rows;
      this.$store.dispatch(actions.DEC_LOADING);
    },

    async save() {
      await this.$store.dispatch(actions.INC_LOADING);
      await this.$api('plans/save-message', { card_pk: this.card_pk, plan_pk: this.plan_pk, data: this.data });
      await this.$store.dispatch(actions.DEC_LOADING);
      this.$root.$emit('msg', 'ok', 'Сохранено');
      this.hide_edit();
      this.load_data(this.plan_pk);
    },
  },
};
</script>

<style scoped lang="scss">
  .align-button {
    float: right;
  }

  .layout {
    table-layout: fixed;
    font-size: 12px
  }

  .date {
    width: 200px;
  }

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
