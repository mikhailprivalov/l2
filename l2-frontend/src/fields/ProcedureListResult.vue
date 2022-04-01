<template>
  <div>
    <table
      class="table table-bordered table-condensed"
      style="table-layout: fixed"
    >
      <colgroup>
        <col width="30%">
        <col>
        <col width="36">
      </colgroup>
      <thead>
        <tr>
          <th>Наименование</th>
          <th>Режим</th>
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
              v-model="val.researchTitle"
              type="text"
              class="form-control"
              :readonly="disabled"
              placeholder="Наименование"
            >
          </td>

          <td class="cl-td">
            <input
              v-model="val.fractionTitle"
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
      Добавить
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
      tb_data: (this.value && this.value !== 'undefined' ? JSON.parse(this.value) : null) || [],
      result: [],
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
    this.insertProcedureListResult();
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
    async insertProcedureListResult() {
      const resultData = await this.$api('procedural-list/procedure-for-extract', {
        pk: this.pk,
      });
      console.log(resultData);
    },
  },
};
</script>
