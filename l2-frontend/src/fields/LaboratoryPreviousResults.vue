<template>
  <div>
    <table
      class="table table-bordered table-condensed"
      style="table-layout: fixed"
    >
      <colgroup>
        <col width="14%">
        <col>
        <col width="14%">
        <col width="14%">
        <col width="14%">
        <col width="14%">
        <col width="36">
      </colgroup>
      <thead>
        <tr>
          <th>Анализ</th>
          <th>Тест</th>
          <th>Значение</th>
          <th>Ед. изм</th>
          <th>Дата</th>
          <th>Исполнитель</th>
          <th class="cl-td">
            <button
              v-tippy="{ placement: 'bottom' }"
              class="btn btn-blue-nb"
              :disabled="disabled"
              title="Очистить строки"
              @click="delete_rows"
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
              placeholder="Анализ-наименование"
            >
          </td>

          <td class="cl-td">
            <input
              v-model="val.fractionTitle"
              type="text"
              class="form-control"
              :readonly="disabled"
              placeholder="Тест-наименование"
            >
          </td>

          <td class="cl-td">
            <input
              v-model="val.value"
              type="text"
              class="form-control"
              :readonly="disabled"
              placeholder="Значение"
            >
          </td>

          <td class="cl-td">
            <input
              v-model="val.units"
              type="text"
              class="form-control"
              :readonly="disabled"
              placeholder="Ед. изм"
            >
          </td>

          <td class="cl-td">
            <input
              v-model="val.date"
              type="text"
              class="form-control"
              :readonly="disabled"
              placeholder="Дата"
            >
          </td>

          <td class="cl-td">
            <input
              v-model="val.docConfirm"
              type="text"
              class="form-control"
              :readonly="disabled"
              placeholder="Исполнитель"
            >
          </td>

          <td class="cl-td">
            <button
              v-tippy="{ placement: 'bottom' }"
              class="btn btn-blue-nb"
              :disabled="disabled"
              title="Удалить строку"
              @click="delete_row(index)"
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
      @click="add_new_row"
    >
      Добавить
    </button>
  </div>
</template>

<script lang="ts">
import { debounce } from 'lodash';

import { Research } from '@/types/research';

const makeDefaultRow = () => ({
  researchTitle: '',
  fractionTitle: '',
  value: '',
  units: '',
  date: '',
  docConfirm: '',
});

export default {
  name: 'LaboratoryPreviousResults',
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
    this.$root.$on('protocol:laboratoryResult', (direction) => {
      this.insertLaboratoryResult(direction);
    });
  },
  methods: {
    add_new_row() {
      this.tb_data.push(makeDefaultRow());
    },
    delete_row(index) {
      this.tb_data.splice(index, 1);
    },
    delete_rows() {
      this.tb_data = [];
    },
    changeValue() {
      this.$emit('modified', JSON.stringify(this.tb_data));
    },
    changeValueDebounce: debounce(function () {
      this.changeValue();
    }, 500),
    async insertLaboratoryResult(direction) {
      const resultData = await this.$api('directions/result-patient-by-direction', {
        isLab: true,
        isDocReferral: false,
        isParaclinic: false,
        dir: direction,
      });
      this.result = resultData.results[0] || {};
      const researches: Research[] = Object.values(this.result.researches);

      for (const r of researches) {
        for (const f of r.fractions) {
          this.tb_data.push({
            researchTitle: r.title,
            fractionTitle: f.title,
            value: f.value,
            units: f.units,
            date: r.dateConfirm,
            docConfirm: r.fio,
          });
        }
      }
    },
  },
};
</script>
