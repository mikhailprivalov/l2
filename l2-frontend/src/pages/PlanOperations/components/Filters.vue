<template>
  <table class="table" style="table-layout: fixed">
    <colgroup>
      <col width='201'/>
      <col/>
      <col width='180'/>
      <col width='180'/>
    </colgroup>
    <thead>
    <tr>
      <th>
        <date-range v-model="filters.date"/>
      </th>
      <th></th>
      <th>Отделение</th>
      <th>Анестезиолог</th>
    </tr>
    </thead>
  </table>
</template>
<script>
  import DateRange from "../../../ui-cards/DateRange"

  export default {
    name: 'Filters',
    components: {DateRange},
    props: {
      filters: {
        type: Object,
        required: true,
      }
    }
  }
</script>
