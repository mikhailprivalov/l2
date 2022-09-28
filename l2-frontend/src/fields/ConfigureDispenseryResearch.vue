<template>
  <div style="margin-top: 10px">
    <h5
      v-if="type_plan==='Глобальный план' && diagnos_code"
      style="text-align: center"
    >
      Глобальная настройка для всей системы
    </h5>
    <h5
      v-else-if="type_plan==='Индивидуальный план'"
      style="text-align: center"
    >
      Индивидуальная настройка для пациента
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
    <div
      v-if="disabledButtons"
      style="color: red"
    >
      Выбранная услуга уже добавлена в глобальных настройках
    </div>
    <div class="row">
      <div class="col-xs-8" />
      <div class="col-xs-2">
        <button
          class="btn btn-blue-nb add-row"
          :disabled="disabledButtons"
          @click="save_dispensary_data(tbData)"
        >
          Сохранить
        </button>
      </div>
      <div class="col-xs-2">
        <button
          class="btn btn-blue-nb add-row"
          :disabled="disabledButtons"
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
    card_pk: {
      default: -1,
      required: false,
    },
    type_plan: {
      default: 'Глобальный план',
      required: false,
    },
    unique_research_pks: {
      type: Array,
      default: () => ([]),
      required: false,
    },
  },
  data() {
    return {
      tbData: [makeDefaultRow()],
      types,
      researches: [],
      specialities: [],
      disabledButtons: false,
    };
  },
  watch: {
    tbData: {
      handler() {
        this.changeValue(this.tbData);
        if (this.tbData.length > 0) {
          this.disabledButtons = this.unique_research_pks.includes(this.tbData.slice(-1)[0].current_researches)
            && this.type_plan === 'Индивидуальный план';
        }
      },
      immediate: true,
    },
    type_plan: {
      handler() {
        this.load_data();
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
    this.$api('researches/load-research-by-diagnos', {
      diagnos_code: this.diagnos_code,
      typePlan: this.type_plan,
      card_pk: this.card_pk,
    }).then(rows => {
      this.tbData = rows;
    });
  },
  methods: {
    async save_dispensary_data(tbData) {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await this.$api('researches/save-dispensary-data', {
        diagnos: this.diagnos_code,
        tb_data: tbData,
        typePlan: this.type_plan,
        card_pk: this.card_pk,
      });
      if (ok) {
        this.$root.$emit('msg', 'ok', message);
      } else {
        this.$root.$emit('msg', 'error', message);
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async load_data() {
      await this.$store.dispatch(actions.INC_LOADING);
      const rows = await this.$api('researches/load-research-by-diagnos', {
        diagnos_code: this.diagnos_code,
        typePlan: this.type_plan,
        card_pk: this.card_pk,
      });
      this.tbData = rows;
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
