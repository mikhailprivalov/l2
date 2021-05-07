<template>
  <td class="ref" :class="{withoutBorderRight: !withBorderRight}">
    <table v-if="parsedData" :class="bordered && 'table table-bordered table-condensed'">
      <tr v-for="(v, k) in parsedData" :key="k">
        <td>{{ k }}</td>
        <td v-html="v"></td>
      </tr>
    </table>
  </td>
</template>

<script>
export default {
  name: 'Ref',
  props: {
    data: {},
    bordered: {
      type: Boolean,
      default: false,
    },
    withBorderRight: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    parsedData() {
      if (!this.data) {
        return null;
      }
      let r = this.data;
      if (typeof r === 'string') {
        try {
          r = JSON.parse(r);
        } catch (e) {
          r = {};
        }
      }

      return r;
    },
  },
};
</script>

<style scoped lang="scss">
.ref {
  padding: 0 !important;
  position: relative;
  z-index: 0;

  &:before {
    background-color: #ddd;
    content: "";
    display: block;
    width: 1px;
    height: 100%;
    position: absolute;
    z-index: -1;
    top: 0;
    left: calc(50% - 1px);
  }

  table {
    width: 100%;
    background: transparent !important;
    table-layout: fixed;

    td, th {
      border: 1px solid #ddd;
      background: transparent;
    }

    tr {
      background: transparent;
    }

    td {
      width: 50%;
      font-size: 12px;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    tr:first-child th {
      border-top: 0 !important;
    }

    tr:first-child td {
      border-top: 0 !important;
    }

    tr:last-child th {
      border-bottom: 0 !important;
    }

    tr:last-child td {
      border-bottom: 0 !important;
    }

    tr td {
      border-left: 0 !important;
      line-height: 1.2;

      &:first-child {
        border-right: 0 !important;
      }
    }
  }

  &.withoutBorderRight {
    table {
      tr td {
        border-right: 0 !important;
      }
    }
  }
}
</style>
