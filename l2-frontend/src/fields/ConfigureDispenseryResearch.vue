<template>
  <div style="margin-top: 10px">
    <h5 style="text-align: center">
      Глобальная настройка для всей системы
    </h5>
    <table class="table table-bordered">
      <colgroup>
        <col width="110">
        <col>
        <col width="70">
        <col width="30">
      </colgroup>
      <thead>
        <tr>
          <th>Тип</th>
          <th>Наименование</th>
          <th>Кол-во в год</th>
          <th>Посещение</th>
          <th />
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(val, index) in tbData"
          :key="index"
        >
          <td class="cl-td">
            <select
              v-model="val.type"
              class="form-control"
              style="border: none"
            >
              <option
                v-for="t in types"
                :key="t"
                :value="t"
              >
                {{ t }}
              </option>
            </select>
          </td>
          <td class="cl-td">
            <Treeselect
              v-if="val.type === 'Услуга'"
              v-model="val.current_researches"
              class="treeselect-noborder"
              :multiple="false"
              :options="researches"
              placeholder="Не выбран"
            />
            <Treeselect
              v-if="val.type === 'Врач'"
              v-model="val.current_researches"
              class="treeselect-noborder"
              :multiple="false"
              :options="specialities"
              placeholder="Не выбран"
            />
          </td>
          <td class="cl-td">
            <div class="input-group">
              <input
                v-model="val.count"
                type="number"
                class="form-control"
                style="border: none"
                placeholder="Кол-во в год"
              >
            </div>
          </td>
          <td class="text-center cl-td">
            <label>
              <input
                v-model="val.is_visit"
                type="checkbox"
              >
            </label>
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
    <div class="row">
      <div class="col-xs-8" />
      <div class="col-xs-2">
        <button
          class="btn btn-blue-nb add-row"
          @click="save_dispensary_data(tbData)"
        >
          Сохранить
        </button>
      </div>
      <div class="col-xs-2">
        <button
          class="btn btn-blue-nb add-row"
          @click="add_new_row"
        >
          Добавить
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import * as actions from '@/store/action-types';

const types = ['Услуга', 'Врач'];
const makeDefaultRow = (type = null) => ({ type: type || types[0], is_visit: false });

export default {
  name: 'ConfigureDispenseryResearch',
  components: { Treeselect },
  model: {
    event: 'modified',
  },
  props: {
    diagnos_code: {
      default: '',
      required: false,
    },
  },
  data() {
    return {
      tbData: [makeDefaultRow()],
      types,
      researches: [],
      specialities: [],
    };
  },
  watch: {
    tbData: {
      handler() {
        this.changeValue(this.tbData);
      },
      immediate: true,
    },
  },
  mounted() {
    this.$api('researches/research-dispensary').then(rows => {
      this.researches = rows;
    });
    this.$api('researches/research-specialities').then(rows => {
      this.specialities = rows;
    });
    this.$api('researches/load-research-by-diagnos', { diagnos_code: this.diagnos_code }).then(rows => {
      this.tbData = rows;
    });
  },
  methods: {
    async save_dispensary_data(tbData) {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await this.$api('researches/save-dispensary-data', {
        diagnos: this.diagnos_code,
        tb_data: tbData,
      });
      if (ok) {
        this.$root.$emit('msg', 'ok', message);
      } else {
        this.$root.$emit('msg', 'error', message);
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    add_new_row() {
      const tl = this.tbData.length;
      this.tbData.push(makeDefaultRow(tl > 0 ? this.tbData[tl - 1].type : null));
    },
    delete_row(index) {
      this.tbData.splice(index, 1);
    },
    changeValue(newVal) {
      this.$emit('modified', newVal);
    },
  },
};
</script>

<style scoped lang="scss">
.add-row {
  float: right;
}

.cl-td ::v-deep {
  label {
    justify-content: left;
  }
}
</style>
