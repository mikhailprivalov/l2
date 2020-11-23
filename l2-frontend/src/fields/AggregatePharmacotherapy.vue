<template>
  <table class="table table-responsive table-bordered table-condensed" style="table-layout: fixed;background-color: #fff">
    <colgroup>
      <col width="300" />
      <col v-for="d in dates" :key="d" />
    </colgroup>
    <thead>
    <tr>
      <th rowspan="2">Наименование ЛП</th>
      <th v-for="d in dates" :key="d">{{d}}</th>
    </tr>
    <tr>
      <th v-for="d in dates" :key="d" class="cl-td">
        <div class="time" v-for="t in times" :key="t">
          {{t}}
        </div>
      </th>
    </tr>
    </thead>
    <tbody>
    <tr v-for="r in rows">
      <td>{{r.drug}}, {{r.form_release}}, {{r.method}}, {{r.dosage}}</td>
      <td v-for="d in dates" :key="d" class="cl-td">
        <div class="time" v-for="t in times" :key="t">
          {{r.dates[d][t].empty ? ' ' : (r.dates[d][t].ok ? '✓' : (r.dates[d][t].cancel ? 'с' : '—'))}}
        </div>
      </td>
    </tr>
    </tbody>
  </table>
</template>

<script>
  import api from '@/api'

  export default {
    props: {
      direction: {},
    },
    data() {
      return {
        rows: [],
        dates: [],
        times: [],
      }
    },
    async mounted() {
      await this.load()
    },
    methods: {
      async load() {
        const {
          result,
          dates,
          times,
        } = await api('procedural-list/get-procedure', this, 'direction');
        this.rows = result;
        this.dates = dates;
        this.times = times;
      },
    },
  }
</script>

<style scoped lang="scss">
.time {
  display: inline-block;
  border-right: 1px solid #ddd;
  text-align: center;
  width: 25%;
  min-width: 25%;
  min-height: 21px;
  margin-bottom: -5px;
  margin-top: -2px;
  font-weight: normal;
  font-size: 10px;

  &:last-child {
    border-right: none;
  }
}
</style>
