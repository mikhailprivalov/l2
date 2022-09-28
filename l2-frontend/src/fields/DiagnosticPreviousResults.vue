<template>
  <div>
    <table
      v-for="(val, index) in tb_data"
      :key="index"
      class="table table-bordered table-condensed"
      style="table-layout: fixed"
    >
      <colgroup>
        <col width="50%">
        <col width="20%">
        <col>
        <col width="36">
      </colgroup>
      <tbody>
        <tr>
          <td class="cl-td">
            <input
              v-model="val.researchTitle"
              type="text"
              class="form-control"
              :readonly="disabled"
              placeholder="Услуга"
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
              placeholder="Врач"
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
        <tr>
          <td
            colspan="4"
            class="cl-td"
          >
            <textarea
              v-model="val.value"
              rows="4"
              name="text"
              class="form-control"
              :readonly="disabled"
              placeholder="Описание"
            />
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
  date: '',
  docConfirm: '',
  value: '',
});

export default {
  name: 'DiagnosticPreviousResults',
  model: {
    event: 'modified',
  },
  props: {
    value: {
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
    this.$root.$on('protocol:paraclinicResult', (direction) => {
      this.insertParaclinicResult(direction);
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
    async insertParaclinicResult(direction) {
      const resultData = await this.$api('directions/result-patient-by-direction', {
        isLab: false,
        isDocReferral: false,
        isParaclinic: true,
        dir: direction,
      });
      this.result = resultData.results[0] || {};
      const researches: Research[] = Object.values(this.result.researches);

      for (const r of researches) {
        for (const f of r.fractions) {
          this.tb_data.push({
            researchTitle: r.title,
            date: r.dateConfirm,
            docConfirm: r.fio,
            value: f.value,
          });
        }
      }
    },
  },
};
</script>

<style scoped></style>
