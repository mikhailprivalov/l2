<template>
  <div style="margin-top: 10px">
    <table class="table table-bordered">
      <colgroup>
        <col/>
        <col width='230'/>
        <col width='120'/>
        <col width='34'/>
      </colgroup>
      <thead>
      <tr>
        <th>Наименование</th>
        <th>Категория</th>
        <th>Показать по умолчанию</th>
        <th></th>
      </tr>
      </thead>
      <tbody>
      <tr v-for="(val, index) in tb_data" :key="index">
        <td class="cl-td">
          <div class="input-group">
            <div class="input-group-btn">
              <button type="button" class="btn btn-blue-nb nbr" @click="up_row(index)"
                      :disabled="is_first_in_template(index)">
                <i class="glyphicon glyphicon-arrow-up"></i>
              </button>
              <button type="button" class="btn btn-blue-nb" @click="down_row(index)"
                      :disabled="is_last_in_template(index)">
                <i class="glyphicon glyphicon-arrow-down"></i>
              </button>
            </div>
            <input type="text" class="form-control nbr" v-model="val.title" placeholder="Введите наименование">
          </div>
        <td class="cl-td">
          <select class="form-control nbr" v-model="val.type">
            <option :value="t" v-for="t in types" :key="t">{{t}}</option>
          </select>
        </td>
        <td class="text-center cl-td">
          <label>
            <input type="checkbox" v-model="val.default">
          </label>
        </td>
        <td class="text-center cl-td">
          <button class="btn btn-blue-nb" @click="delete_row(index)" v-tippy="{ placement : 'bottom'}"
                  title="Удалить строку">
            <i class="fa fa-times"/>
          </button>
        </td>
      </tr>
      </tbody>
    </table>
    <button class="btn btn-blue-nb add-row" @click="add_new_row">
      Добавить
    </button>
  </div>
</template>

<script>
const types = [
  'Показатели человека',
  'Сильнодействующие',
  'Наркотические',
];

const makeDefaultRow = (type = null) => ({ title: '', type: type || types[0], default: false });

export default {
  name: 'ConfigureAnesthesiaField',
  props: {
    value: {
      required: false,
    },
    disabled: {
      required: false,
      default: false,
      type: Boolean,
    },
  },
  data() {
    return {
      tb_data: this.value || [makeDefaultRow()],
      types,
    };
  },
  methods: {
    add_new_row() {
      const tl = this.tb_data.length;
      this.tb_data.push(makeDefaultRow(tl > 0 ? this.tb_data[tl - 1].type : null));
    },
    delete_row(index) {
      this.tb_data.splice(index, 1);
    },
    is_first_in_template(i) {
      return i === 0;
    },
    is_last_in_template(i) {
      return i === this.tb_data.length - 1;
    },
    down_row(i) {
      if (this.is_last_in_template(i)) {
        return;
      }
      const values = [...this.tb_data];
      [values[i + 1], values[i]] = [values[i], values[i + 1]];
      this.tb_data = values;
    },
    up_row(i) {
      if (this.is_first_in_template(i)) {
        return;
      }
      const values = [...this.tb_data];
      [values[i - 1], values[i]] = [values[i], values[i - 1]];
      this.tb_data = values;
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
</style>
