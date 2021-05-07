<template>
  <div class="row">
    <div class="col-xs-4" style="padding-right: 3px;">
      <select-picker :val="date_type" :options="date_types" :func="change_type" :multiple="false" :actions_box="false"/>
    </div>
    <div class="col-xs-8">
      <div :class="[{hidden: date_type !== 'd'}]">
        <date-field :val.sync="values.date" :def="values.date"/>
      </div>
      <div class="row" :class="[{hidden: date_type !== 'm'}]">
        <div class="col-xs-6" style="padding-right: 3px;">
          <select-picker :val="values.month" :options="monthes" :func="change_month" :multiple="false"
                         :actions_box="false"/>
        </div>
        <div class="col-xs-6">
          <input type="number" class="form-control year" v-model="values.year" min="2015" max="2100"/>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import SelectPicker from './SelectPicker.vue';
import DateField from './DateField.vue';

export default {
  name: 'date-selector',
  props: {
    values_def: {
      type: Object,
      default() {
        return {
          date: window.getFormattedDate(window.today),
          month: `${window.today.getMonth()}`,
          year: `${window.today.getFullYear()}`,
        };
      },
    },
  },
  data() {
    return {
      date_type: 'd',
      date_types: [{ value: 'd', label: 'За день' }, { value: 'm', label: 'За месяц' }],
      monthes: [
        { value: '0', label: 'Январь' },
        { value: '1', label: 'Февраль' },
        { value: '2', label: 'Март' },
        { value: '3', label: 'Апрель' },
        { value: '4', label: 'Май' },
        { value: '5', label: 'Июнь' },
        { value: '6', label: 'Июль' },
        { value: '7', label: 'Август' },
        { value: '8', label: 'Сентябрь' },
        { value: '9', label: 'Октябрь' },
        { value: '10', label: 'Ноябрь' },
        { value: '11', label: 'Декабрь' },
      ],
      values: this.values_def,
    };
  },
  watch: {
    date_type() {
      this.$emit('update:date_type', this.date_type);
    },
    values: {
      handler() {
        this.$emit('update:values', this.values);
      },
      deep: true,
    },
  },
  created() {
    this.$emit('update:date_type', this.date_type);
    this.$emit('update:values', this.values);
  },
  methods: {
    change_type(v) {
      this.date_type = v;
    },
    change_month(v) {
      this.values.month = v;
    },
  },
  components: { SelectPicker, DateField },
};
</script>
