<template>
  <div>
    <table class="table table-bordered table-condensed" style="table-layout: fixed">
      <colgroup>
        <col width='14%'/>
        <col />
        <col width='14%'/>
        <col width='14%'/>
        <col width='14%'/>
        <col width='14%'/>
        <col width='36'/>
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
          <button class="btn btn-blue-nb" @click="delete_rows" :disabled="disabled" v-tippy="{ placement : 'bottom'}"
                  title="Очистить строки">
            <i class="fa fa-times"/>
          </button>
        </th>
      </tr>
      </thead>
      <tbody>
      <tr v-for="(val, index) in tb_data" :key="`${val.researchTitle}_${val.fractionTitle}_${index}`">
        <td class="cl-td"><input type="text" class="form-control" :readonly="disabled" placeholder="Анализ-наименование"
                                 v-model="val.researchTitle"></td>
        <td class="cl-td"><input type="text" class="form-control" :readonly="disabled" placeholder="Тест-наименование"
                                 v-model="val.fractionTitle"></td>
        <td class="cl-td"><input type="text" class="form-control" :readonly="disabled" placeholder="Значение"
                                 v-model="val.value"></td>
        <td class="cl-td"><input type="text" class="form-control" :readonly="disabled" placeholder="Ед. изм"
                                 v-model="val.units"></td>
        <td class="cl-td"><input type="text" class="form-control" :readonly="disabled" placeholder="Дата"
                                 v-model="val.date"></td>
        <td class="cl-td"><input type="text" class="form-control" :readonly="disabled" placeholder="Исполнитель"
                                 v-model="val.docConfirm"></td>
        <td class="cl-td">
          <button class="btn btn-blue-nb" @click="delete_row(index)" :disabled="disabled"
                  v-tippy="{ placement : 'bottom'}"
                  title="Удалить строку">
            <i class="fa fa-times"/>
          </button>
        </td>
      </tr>
      </tbody>
    </table>
    <button class="btn btn-blue-nb add-row" @click="add_new_row" :disabled="disabled">
      Добавить
    </button>
  </div>
</template>

<script>
import api from '@/api';
import { debounce } from 'lodash';

const makeDefaultRow = () => ({
  researchTitle: '', fractionTitle: '', value: '', units: '', date: '', docConfirm: '',
});

export default {
  name: 'LaboratoryPreviousResults',
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
      tb_data: ((this.value && this.value !== 'undefined') ? JSON.parse(this.value) : null) || [],
      result: [],
    };
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
      const result_data = await api('directions/result-patient-by-direction',
        {
          isLab: true, isDocReferral: false, isParaclinic: false, dir: direction,
        });
      this.result = result_data.results[0] || {};

      for (const r of Object.values(this.result.researches)) {
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
  watch: {
    tb_data: {
      handler() {
        this.changeValueDebounce();
      },
      immediate: true,
      deep: true,
    },
  },
  model: {
    event: 'modified',
  },
};
</script>
