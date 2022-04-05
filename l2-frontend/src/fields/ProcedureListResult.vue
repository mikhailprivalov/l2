<template>
  <div>
    <button
      class="btn btn-blue-nb add-row"
      :disabled="disabled"
      @click="insertProcedureListResult"
    >
      Загрузить из процедурного листа
    </button>
    <table
      class="table table-bordered table-condensed"
      style="table-layout: fixed"
    >
      <colgroup>
        <col width="40%">
        <col>
        <col width="36">
      </colgroup>
      <thead>
        <tr>
          <th>Наименование</th>
          <th>Параметры</th>
          <th class="cl-td">
            <button
              v-tippy="{ placement: 'bottom' }"
              class="btn btn-blue-nb"
              :disabled="disabled"
              title="Очистить строки"
              @click="deleteRows"
            >
              <i class="fa fa-times" />
            </button>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(val, index) in tb_data"
          :key="index"
        >
          <td class="cl-td">
            <input
              v-model="val.pharmaTitle"
              type="text"
              class="form-control"
              :readonly="disabled"
              placeholder="Наименование"
            >
          </td>

          <td class="cl-td">
            <input
              v-model="val.mode"
              type="text"
              class="form-control"
              :readonly="disabled"
              placeholder="Режим"
            >
          </td>

          <td class="cl-td">
            <button
              v-tippy="{ placement: 'bottom' }"
              class="btn btn-blue-nb"
              :disabled="disabled"
              title="Удалить строку"
              @click="deleteRow(index)"
            >
              <i class="fa fa-times" />
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <button
      class="btn btn-blue-nb add-row"
      :disabled="disabled"
      @click="addNewRow"
    >
      Добавить строку
    </button>
  </div>
</template>

<script lang="ts">
import { debounce } from 'lodash';

const makeDefaultRow = () => ({
  pharmaTitle: '',
  mode: '',
});

export default {
  name: 'ProcedureListResults',
  model: {
    event: 'modified',
  },
  props: {
    value: {
      type: String,
      required: false,
    },
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
    pk: {
      type: [String, Number],
      required: false,
    },
  },
  data() {
    return {
      tb_data: [],
    };
  },
  watch: {
    tb_data: {
      handler() {
        this.changeValueDebounce();
      },
      immediate: true,
      deep: true,
    },
  },
  mounted() {
    const jsonObject = JSON.parse(this.value);
    this.insertProcedureData(jsonObject);
  },
  methods: {
    addNewRow() {
      this.tb_data.push(makeDefaultRow());
    },
    deleteRow(index) {
      this.tb_data.splice(index, 1);
    },
    deleteRows() {
      this.tb_data = [];
    },
    changeValue() {
      this.$emit('modified', JSON.stringify(this.tb_data));
    },
    changeValueDebounce: debounce(function () {
      this.changeValue();
    }, 500),
    insertProcedureData(procedureData) {
      for (const r of procedureData) {
        this.tb_data.push({
          pharmaTitle: r.pharmaTitle,
          mode: r.mode,
        });
      }
    },
    async insertProcedureListResult() {
      const resultData = await this.$api('procedural-list/procedure-for-extract', {
        pk: this.pk,
      });
      this.insertProcedureData(resultData.data);
    },
  },
};
</script>
