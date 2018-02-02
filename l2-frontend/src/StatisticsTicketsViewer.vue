<template>
  <div style="height: 100%;width: 100%;position: relative">
    <div class="top-picker">
      <date-field style="width: 94px;display: inline-block;align-self: stretch" :val.sync="date" :def="date"/>
      <button class="btn btn-blue-nb" style="width: 42px;display: inline-block;align-self: stretch"><i class="glyphicon glyphicon-refresh"></i></button>
      <button class="btn btn-blue-nb" style="width: 94px;display: inline-block;align-self: stretch"><i class="glyphicon glyphicon-print"></i> Печать</button>
    </div>
    <div class="content-picker">

    </div>
  </div>
</template>

<script>
  import moment from 'moment'
  import DateField from './DateField.vue'
  export default {
    name: 'statistics-tickets-viewer',
    components: {
      DateField
    },
    data() {
      return {
        date: moment().format('DD.MM.YYYY')
      }
    }
  }
</script>

<style scoped lang="scss">
  .top-picker {
    height: 34px;
    background-color: #AAB2BD;
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    display: flex;
    align-items: stretch;
    justify-content: center;
    align-content: stretch;
  }

  .content-picker {
    display: flex;
    flex-wrap: wrap;
    justify-content: stretch;
    align-items: stretch;
    overflow-y: auto;
    align-content: flex-start;
    position: absolute;
    top: 34px;
    bottom: 0;
    left: 0;
    right: 0;
  }

  .top-picker .form-control, .top-picker .btn {
    border-radius: 0;
    border: none;
  }

  .top-picker .form-control {
    border-bottom: 1px solid #AAB2BD;
  }
</style>
