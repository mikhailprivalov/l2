<template>
  <Modal
    ref="modal"
    margin-top
    margin-left-right="auto"
    max-width="680px"
    show-footer="true"
    white-bg="true"
    width="100%"
    @close="hide_modal"
  >
    <span slot="header">Льготы пациента
      <span v-if="!card_data.fio_age">{{ card_data.family }} {{ card_data.name }} {{ card_data.twoname }},
        {{ card_data.age }}, карта {{ card_data.num }}</span>
      <span v-else>{{ card_data.fio_age }}</span>
    </span>
    <div
      slot="body"
      class="registry-body"
      style="min-height: 200px"
    >
      <table
        class="table table-bordered table-condensed table-sm-pd"
        style="table-layout: fixed; font-size: 12px"
      >
        <colgroup>
          <col width="130">
          <col>
          <col>
          <col>
          <col
            v-if="!readonly"
            width="45"
          >
        </colgroup>
        <thead>
          <tr>
            <th>Вид льготы</th>
            <th>Основание</th>
            <th>Постановка на льготу</th>
            <th>Снятие со льготы</th>
            <th v-if="!readonly" />
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="r in rows"
            :key="r.pk"
            :class="{stop: !!r.date_end}"
          >
            <td>{{ r.benefit }}</td>
            <td>{{ r.registration_basis }}</td>
            <td>{{ r.doc_start_reg }}<br>{{ r.date_start }}</td>
            <td>{{ r.doc_end_reg }}<br v-if="!!r.date_end">{{ r.date_end }}</td>
            <td v-if="!readonly">
              <button
                v-tippy="{ placement : 'bottom', arrow: true }"
                class="btn last btn-blue-nb nbr"
                style="margin-left: -1px"
                title="Редактирование"
                type="button"
                @click="edit(r.pk)"
              >
                <i class="glyphicon glyphicon-pencil" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <div
        v-if="!readonly"
        style="margin: 0 auto; width: 200px"
      >
        <button
          class="btn btn-primary-nb btn-blue-nb"
          type="button"
          @click="edit(-1)"
        >
          <i class="fa fa-plus" /> Создать запись
        </button>
      </div>
      <Modal
        v-if="edit_pk > -2"
        ref="modalEdit"
        margin-top
        margin-left-right="auto"
        max-width="710px"
        show-footer="true"
        white-bg="true"
        width="100%"
        @close="hide_edit"
      >
        <span
          v-if="edit_pk > -1"
          slot="header"
        >Редактор льготы</span>
        <span
          v-else
          slot="header"
        >Создание льготы</span>
        <div
          slot="body"
          class="registry-body"
          style="min-height: 200px;padding: 10px"
        >
          <div class="form-group">
            <label>Вид льготы:</label>
            <select
              v-model="edit_data.benefit_id"
              :readonly="edit_data.close"
              class="form-control"
            >
              <option
                v-for="x in edit_data.types"
                :key="x.pk"
                :value="x.pk"
              >
                {{ x.title }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label for="de-f3">Дата постановки на льготу:</label>
            <input
              id="de-f3"
              v-model="edit_data.date_start"
              :max="td"
              :readonly="edit_data.close"
              class="form-control"
              type="date"
            >
          </div>
          <div class="form-group">
            <label for="de-f6">Основание:</label>
            <textarea
              id="de-f6"
              v-model="edit_data.registration_basis"
              class="form-control"
              :readonly="edit_data.close"
            />
          </div>
          <div
            class="checkbox"
            style="padding-left: 15px;"
          >
            <label>
              <input
                v-model="edit_data.close"
                type="checkbox"
              > снят с льготы
            </label>
          </div>
          <div
            v-if="edit_data.close"
            class="form-group"
          >
            <label for="de-f5">Дата снятия:</label>
            <input
              id="de-f5"
              v-model="edit_data.date_end"
              :min="td"
              class="form-control"
              type="date"
            >
          </div>
        </div>
        <div slot="footer">
          <div class="row">
            <div class="col-xs-4">
              <button
                class="btn btn-primary-nb btn-blue-nb"
                type="button"
                @click="hide_edit"
              >
                Отмена
              </button>
            </div>
            <div class="col-xs-4">
              <button
                :disabled="!valid_reg"
                class="btn btn-primary-nb btn-blue-nb"
                type="button"
                @click="save()"
              >
                Сохранить
              </button>
            </div>
          </div>
        </div>
      </Modal>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-10" />
        <div class="col-xs-2">
          <button
            class="btn btn-primary-nb btn-blue-nb"
            type="button"
            @click="hide_modal"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script lang="ts">
import moment from 'moment';

import Modal from '@/ui-cards/Modal.vue';
import patientsPoint from '@/api/patients-point';
import * as actions from '@/store/action-types';

export default {
  name: 'Benefit',
  components: { Modal },
  props: {
    card_pk: {
      type: Number,
      required: true,
    },
    card_data: {
      type: Object,
      required: true,
    },
    readonly: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      td: moment().format('YYYY-MM-DD'),
      rows: [],
      edit_data: {},
      edit_pk: -2,
    };
  },
  computed: {
    valid_reg() {
      return this.edit_pk > -2
          && this.edit_data.date_start !== ''
          && this.edit_data.registration_basis !== ''
          && (!this.edit_data.close || this.edit_data.date_end !== '');
    },
  },
  created() {
    this.load_data();
  },
  methods: {
    async edit(pk) {
      const d = await patientsPoint.loadBenefitDetail({ pk });
      this.edit_data = {
        ...this.edit_data,
        ...d,
        date_start: d.date_start || this.td,
        date_end: d.date_end || this.td,
      };
      this.edit_pk = pk;
    },
    hide_edit() {
      if (this.$refs.modalEdit) {
        this.$refs.modalEdit.$el.style.display = 'none';
      }
      this.edit_pk = -2;
    },
    hide_modal() {
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
      this.$root.$emit('hide_benefit');
    },
    async save() {
      await this.$store.dispatch(actions.INC_LOADING);
      await patientsPoint.saveBenefit({ card_pk: this.card_pk, pk: this.edit_pk, data: this.edit_data });
      await this.$store.dispatch(actions.DEC_LOADING);
      this.$root.$emit('msg', 'ok', 'Сохранено');
      this.hide_edit();
      this.load_data();
    },
    load_data() {
      this.$store.dispatch(actions.INC_LOADING);
      patientsPoint.loadBenefit(this, 'card_pk').then(({ rows }) => {
        this.rows = rows;
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
      });
    },
  },
};
</script>

<style lang="scss" scoped>
  select.form-control {
    padding: 0;
    overflow: visible;
  }

  .nonPrior {
    opacity: .7;

    &:hover {
      opacity: 1;
    }
  }

  .prior {
    background-color: rgba(#000, .05);
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

  .form-row {
    width: 100%;
    display: flex;
    border-bottom: 1px solid #434a54;

    &:first-child:not(.nbt-i) {
      border-top: 1px solid #434a54;
    }

    justify-content: stretch;

    .row-t {
      background-color: #AAB2BD;
      padding: 7px 0 0 10px;
      width: 35%;
      flex: 0 35%;
      color: #fff;
    }

    .input-group {
      flex: 0 65%;
    }

    input, .row-v, ::v-deep input {
      background: #fff;
      border: none;
      border-radius: 0 !important;
      width: 65%;
      flex: 0 65%;
      height: 34px;
    }

    &.sm-f {
      .row-t {
        padding: 2px 0 0 10px;
      }

      input, .row-v, ::v-deep input {
        height: 26px;
      }
    }

    ::v-deep input {
      width: 100% !important;
    }

    .row-v {
      padding: 7px 0 0 10px;
    }

    ::v-deep .input-group {
      border-radius: 0;
    }

    ::v-deep ul {
      width: auto;
      font-size: 13px;
    }

    ::v-deep ul li {
      overflow: hidden;
      text-overflow: ellipsis;
      padding: 2px .25rem;
      margin: 0 .2rem;

      a {
        padding: 2px 10px;
      }
    }
  }

  .col-form {
    &.left {
      padding-right: 0 !important;

      .row-t, input, .row-v, ::v-deep input {
        border-right: 1px solid #434a54 !important;
      }
    }

    &:not(.left):not(.mid) {
      padding-left: 0 !important;

      .row-t {
        border-right: 1px solid #434a54;
      }
    }
  }

  .info-row {
    padding: 7px;
  }

  .individual {
    cursor: pointer;

    &:hover {
      background-color: rgba(0, 0, 0, .15);
    }
  }

  .str ::v-deep .input-group {
    width: 100%;
  }

  .lst {
    margin: 0;
    line-height: 1;
  }

  .mkb10 {
    z-index: 0;
  }

  .mkb10 ::v-deep .input-group {
    width: 100%;
  }

  .mkb10 ::v-deep ul {
    font-size: 13px;
    z-index: 1000;
  }

  .mkb10 ::v-deep ul li {
    overflow: hidden;
    text-overflow: ellipsis;
    padding: 2px .25rem;
    margin: 0 .2rem;

    a {
      padding: 2px 10px;
    }
  }

  tr.stop {
    opacity: .7;
    text-decoration: line-through;

    &:hover {
      opacity: 1;
      text-decoration: none;
    }
  }
</style>
