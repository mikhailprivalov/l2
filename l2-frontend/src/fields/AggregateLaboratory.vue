<template>
  <div class="root-agg">
    <div v-for="(lab, title) in data">
      <div><strong>{{title}}</strong></div>
      <div v-for="row in lab.vertical">
        <div><strong>{{row.title_research}}</strong></div>
        <table>
          <colgroup>
            <col width="60" />
          </colgroup>
          <thead>
          <tr>
            <th>Дата, напр.</th>
            <th v-for="t in row.title_fracions" :key="t">{{t}}</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="(r, dateDir) in row.result" :key="dateDir">
            <td>{{dateDir}}</td>
            <td v-for="(v, i) in r" :key="i">{{v}}</td>
          </tr>
          </tbody>
        </table>
      </div>
      <div v-for="row in lab.horizontal">
        <div><strong>{{row.title_research}}</strong></div>
        <table>
          <colgroup>
            <col width="120" />
          </colgroup>
          <thead>
          <tr>
            <th>Дата, напр.</th>
            <td v-for="(_, dateDir) in row.result" :key="dateDir">{{dateDir}}</td>
          </tr>
          </thead>
          <tbody>
          <tr v-for="(t, i) in row.title_fracions" :key="i">
            <th class="th2">{{t}}</th>
            <td v-for="(v, dateDir) in row.result" :key="dateDir">{{v[i]}}</td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
  import stationar_point from '../api/stationar-point'

  export default {
    props: {
      pk: {},
      extract: {
        type: Boolean,
        default: false
      }
    },
    data() {
      return {
        data: {}
      }
    },
    mounted() {
      this.load()
    },
    methods: {
      async load() {
        this.data = await stationar_point.aggregateLaboratory(this, ['pk', 'extract'])
      },
    },
  }
</script>

<style scoped lang="scss">
  .root-agg {
    table {
      width: 100%;
      table-layout: fixed;
      border-collapse: collapse;
    }

    table, th, td {
      border: 1px solid black;
    }

    th, td {
      word-break: break-word;
      white-space: normal;
      text-align: left;
    }

    table th:not(:first-child), .th2 {
      font-size: 12px;
    }

    td, th {
      padding: 2px;
    }
  }
</style>
