<template>
  <div class="row">
    <div class="col-xs-4" style="padding-right: 3px;">
      <select class="selectpicker" data-width="100%" v-model="date_type">
        <option value="d">За день</option>
        <option value="m">За месяц</option>
      </select>
    </div>
    <div class="col-xs-8">
      <div v-if="date_type === 'd'">
        <input type="text" class="form-control no-context" name="dateday-type"/>
      </div>
      <div class="row" v-if="date_type === 'm'">
        <div class="col-xs-6" style="padding-right: 3px;">
          <select class="selectpicker" data-width="100%">
            <option value="0">Январь</option>
            <option value="1">Февраль</option>
            <option value="2">Март</option>
            <option value="3">Апрель</option>
            <option value="4">Май</option>
            <option value="5">Июнь</option>
            <option value="6">Июль</option>
            <option value="7">Август</option>
            <option value="8">Сентябрь</option>
            <option value="9">Октябрь</option>
            <option value="10">Ноябрь</option>
            <option value="11">Декабрь</option>
          </select>
        </div>
        <div class="col-xs-6">
          <input type="number" class="form-control year" id="m-year" value="" min="2015" max="2100"/>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  export default {
    name: 'date-selector',
    data() {
      return {
        date_type: 'd'
      }
    },
    methods: {},
  }
</script>
