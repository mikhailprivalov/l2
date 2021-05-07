<template>
  <div style="margin-top: 10px">
     <h5 style="text-align: center">Глобальная настройка для всей системы</h5>
    <table class="table table-bordered">
      <colgroup>
        <col width='110'/>
        <col/>
        <col width='70'/>
        <col width='30'/>
      </colgroup>
      <thead>
      <tr>
        <th>Тип</th>
        <th>Наименование</th>
        <th>Кол-во в год</th>
        <th>Посещение</th>
        <th></th>
      </tr>
      </thead>
      <tbody>
      <tr v-for="(val, index) in tb_data" :key="index">
        <td class="cl-td">
          <select class="form-control" style="border: none" v-model="val.type">
            <option :value="t" v-for="t in types" :key="t">{{ t }}</option>
          </select>
        </td>
        <td class="cl-td">
          <treeselect v-if="val.type==='Услуга'" class="treeselect-noborder" :multiple="false" :options="researches"
                      placeholder="Не выбран" v-model="val.current_researches"
          />
          <treeselect v-if="val.type==='Врач'" class="treeselect-noborder" :multiple="false" :options="specialities"
                      placeholder="Не выбран" v-model="val.current_researches"
          />
        </td>
        <td class="cl-td">
          <div class="input-group">
            <input type="number" class="form-control" style="border: none" v-model="val.count"
                   placeholder="Кол-во в год">
          </div>
        </td>
        <td class="text-center cl-td">
          <label>
            <input type="checkbox" v-model="val.is_visit">
          </label>
        </td>
        <td class="text-center cl-td">
          <button class="btn btn-blue-nb" @click="delete_row(index)" v-tippy="{ placement: 'bottom'}"
                  title="Удалить строку">
            <i class="fa fa-times"/>
          </button>
        </td>
      </tr>
      </tbody>
    </table>
    <div class="row">
      <div class="col-xs-8">
      </div>
      <div class="col-xs-2">
        <button class="btn btn-blue-nb add-row" @click="save_dispensary_data(tb_data)">
          Сохранить
        </button>
      </div>
      <div class="col-xs-2">
        <button class="btn btn-blue-nb add-row" @click="add_new_row">
          Добавить
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import * as actions from '@/store/action-types';
import api from '@/api';

const types = ['Услуга', 'Врач'];
const makeDefaultRow = (type = null) => ({ type: type || types[0], is_visit: false });

export default {
  name: 'ConfigureDispenseryResearch',
  components: { Treeselect },
  props: {
    diagnos_code: {
      default: '',
      required: false,
    },
  },
  data() {
    return {
      tb_data: [makeDefaultRow()],
      types,
      researches: [],
      specialities: [],
    };
  },
  mounted() {
    api('researches/research-dispensary').then((rows) => {
      this.researches = rows;
    });
    api('researches/research-specialities').then((rows) => {
      this.specialities = rows;
    });
    api('researches/load-research-by-diagnos', { diagnos_code: this.diagnos_code }).then((rows) => {
      this.tb_data = rows;
    });
  },
  methods: {
    async save_dispensary_data(tb_data) {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await api('researches/save-dispensary-data', {
        diagnos: this.diagnos_code,
        tb_data,
      });
      if (ok) {
        window.okmessage(message);
      } else {
        window.errmessage(message);
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    add_new_row() {
      const tl = this.tb_data.length;
      this.tb_data.push(makeDefaultRow(tl > 0 ? this.tb_data[tl - 1].type : null));
    },
    delete_row(index) {
      this.tb_data.splice(index, 1);
    },
    changeValue(newVal) {
      this.$emit('modified', newVal);
    },
  },
  watch: {
    tb_data: {
      handler() {
        this.changeValue(this.tb_data);
      },
      immediate: true,
    },
  },
  model: {
    event: 'modified',
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
