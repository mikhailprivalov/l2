<template>
  <div class="row">
    <div class="col-xs-4" style="padding-right: 3px;">
      <select-picker :val.sync="date_type" :options.sync="date_types" :func="change_type"></select-picker>
    </div>
    <div class="col-xs-8">
      <div :class="[{hidden: date_type !== 'd'}]">
        <date-field :val.sync="values.date" :def="values.date"></date-field>
      </div>
      <div class="row" :class="[{hidden: date_type !== 'm'}]">
        <div class="col-xs-6" style="padding-right: 3px;">
          <select-picker :val.sync="values.month" :options.sync="monthes" :func="change_month"></select-picker>
        </div>
        <div class="col-xs-6">
          <input type="number" class="form-control year" v-model="values.year" min="2015" max="2100"/>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import SelectPicker from './SelectPicker.vue'
  import DateField from './DateField.vue'

  export default {
    name: 'date-selector',
    props: {
      users: {
        type: Array
      }
    },
    data() {
      return {
        date_type: 'd',
        date_types: [{value: 'd', label: 'За день'}, {value: 'm', label: 'За месяц'}],
        monthes: [
          {value: '0', label: 'Январь'},
          {value: '1', label: 'Февраль'},
          {value: '2', label: 'Март'},
          {value: '3', label: 'Апрель'},
          {value: '4', label: 'Май'},
          {value: '5', label: 'Июнь'},
          {value: '6', label: 'Июль'},
          {value: '7', label: 'Август'},
          {value: '8', label: 'Сентябрь'},
          {value: '9', label: 'Октябрь'},
          {value: '10', label: 'Ноябрь'},
          {value: '11', label: 'Декабрь'},
        ],
        values: {
          date: getFormattedDate(today),
          month: (new Date()).getMonth() + '',
          year: (new Date()).getFullYear() + ''
        }
      }
    },
    methods: {
      change_type(v) {
        this.date_type = v
      },
      change_month(v) {
        this.values.month = v
      }
    },
    components: {SelectPicker, DateField}
  }
</script>
