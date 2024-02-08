<template>
  <Modal
    ref="modal"
    margin-top
    margin-left-right="auto"
    max-width="680px"
    height="450px"
    show-footer="true"
    white-bg="true"
    width="100%"
    @close="hide_modal"
  >
    <span slot="header">Подгруппы в подразделении</span>
    <div
      slot="body"
      class="registry-body"
      style="min-height: 100px"
    >
      <table
        class="table table-bordered table-condensed table-sm-pd"
        style="table-layout: fixed; font-size: 12px; margin-bottom: 0"
      >
        <colgroup>
          <col>
          <col width="35">
        </colgroup>
        <thead>
          <tr>
            <th>Подгруппа</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(val, index) in tbData"
            :key="index"
          >
            <td class="cl-td">
              <Treeselect
                v-model="val.subgroupId"
                class="treeselect-noborder treeselect-32px"
                :multiple="false"
                :options="subGroupsAll"
                placeholder="Не выбран"
              />
            </td>
            <td class="text-center cl-td">
              <button
                v-tippy="{ placement: 'bottom' }"
                class="btn btn-blue-nb"
                title="Удалить строку"
                @click="delete_row(index)"
              >
                <i class="fa fa-times" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <div
        class="flex add-row-div"
      >
        <button
          v-tippy="{ placement: 'bottom' }"
          class="btn btn-blue-nb nbr add-button"
          title="Добавить строку"
          @click="add_new_row"
        >
          <i class="fa fa-plus" />
        </button>
      </div>
    </div>
    <div slot="footer">
      <div class="flex flex-row">
        <div>
          <button
            class="btn btn-blue-nb add-row margin-button"
            :disabled="disabledButtons"
            @click="saveSubGroupsDepartment(tbData)"
          >
            Сохранить
          </button>
          <button
            class="btn btn-blue-nb add-row margin-button"
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
import Treeselect from '@riophae/vue-treeselect';

import Modal from '@/ui-cards/Modal.vue';
import * as actions from '@/store/action-types';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

const makeDefaultRow = (subGroupId = null) => ({ subGroupId });
export default {
  name: 'SubGroupsDepartment',
  components: { Modal, Treeselect },
  props: {
    department_pk: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      rows: [],
      tbData: [makeDefaultRow()],
      disabledButtons: false,
      dateMedExam: '',
      subGroupsAll: [],
    };
  },
  mounted() {
    this.$api('construct/department/get-subgroups', {
      department_pk: this.department_pk,
    }).then(rows => {
      this.tbData = rows;
    });
    this.$api('construct/get-subgroups-all').then(rows => {
      this.subGroupsAll = rows;
    });
  },
  methods: {
    hide_modal() {
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
      this.$root.$emit('hide_subgroups_department');
    },
    async load_data() {
      await this.$store.dispatch(actions.INC_LOADING);
      const rows = await this.$api('construct/department/get-subgroups', {
        department_pk: this.department_pk,
      });
      this.tbData = rows;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async saveSubGroupsDepartment(tbData) {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await this.$api('construct/department/save-subgroups', {
        tb_data: tbData,
        department_pk: this.department_pk,
      });
      if (ok) {
        this.$root.$emit('msg', 'ok', message);
      } else {
        this.$root.$emit('msg', 'error', message);
      }
      await this.load_data();
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    add_new_row() {
      this.tbData.push(makeDefaultRow(null));
    },
    delete_row(index) {
      this.tbData.splice(index, 1);
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
.flex-row {
  justify-content: space-between;
  height: 34px;
  margin: 10px;
}
.flex {
  display: flex;
}
.med-date {
  border-radius: 0 4px 4px 0;
  width: 125px;
}
.med-label {
  width: 125px;
  height: 34px;
}
::v-deep .input-group-addon {
  padding: 8px 12px;
}
.margin-button {
  margin-left: 10px;
  margin-right: 10px;
}

.add-row-div {
  justify-content: flex-end;
  height: 35px;
}
.add-button {
  width: 35px;
}
</style>
