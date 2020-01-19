<template>
  <div class="root-agg">
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
      },
      r_type: {
        type: String,
        required: true,
      },
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
        this.data = await stationar_point.aggregateDesc(this, ['pk', 'extract', 'r_type'])
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
