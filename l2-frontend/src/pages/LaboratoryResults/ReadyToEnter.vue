<template>
  <div>
    <div class="filters">
      <div class="filters-header">Дата приёма материала:</div>
      <date-range v-model="date_range"/>
    </div>
    <div class="work-list">
      <div class="work-list-left">
        <table class="table table-bordered table-condensed">
          <thead>
          <tr>
            <th>
              Направления
              <small class="badge">{{ directions.length }}</small>
            </th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="d in directions">
            <td class='num' @click="searchDirection(d.id)"><span>{{ d.date }}</span> {{ d.id }}</td>
          </tr>
          </tbody>
        </table>
      </div>
      <div class="work-list-right">
        <table class="table table-bordered table-condensed">
          <thead>
          <tr>
            <th>
              Ёмкости
              <small class="badge">{{ tubes.length }}</small>
            </th>
          </tr>
          </thead>
          <tbody>
          <tr class='select-tube' :title='t.tube.title' v-for="t in tubes">
            <td class='num' @click="searchTube(t.id)">
              <span>{{ t.date }}</span>
              <div :style='`background-color: ${t.tube.color};color: ${t.tube.color};`' class='circle'></div>
              {{ t.id }}
            </td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import moment from "moment";
import DateRange from "@/ui-cards/DateRange";
import api from "@/api";
import * as action_types from "@/store/action-types";
import _ from "lodash";
import {SEARCH_MODES} from "@/pages/LaboratoryResults/constants";

export default {
  name: "ReadyToEnter",
  components: {DateRange},
  props: {
    laboratory: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      date_range: [moment().format('DD.MM.YYYY'), moment().format('DD.MM.YYYY')],
      directions: [],
      tubes: [],
    };
  },
  computed: {
    watchParams() {
      return _.pick(this, [
        'laboratory',
        'date_range',
      ]);
    },
  },
  watch: {
    watchParams() {
      if (this.laboratory === -1) {
        return;
      }

      this.load();
    },
  },
  methods: {
    async load() {
      await this.$store.dispatch(action_types.INC_LOADING);
      const {directions, tubes} = await api('laboratory/ready', this, ['date_range', 'laboratory']);
      this.directions = directions;
      this.tubes = tubes;
      await this.$store.dispatch(action_types.DEC_LOADING);
    },
    search(mode, pk) {
      this.$root.$emit('laboratory:results:search', mode, pk);
    },
    searchDirection(pk) {
      this.search(SEARCH_MODES.DIRECTION, pk);
    },
    searchTube(pk) {
      this.search(SEARCH_MODES.TUBE, pk);
    },
  },
}
</script>

<style scoped lang="scss">
.filters {
  background-color: #edeeef;

  &-header {
    margin: 5px 5px 0 5px;
  }

  ::v-deep .form-control {
    width: 100% !important;
    border-radius: 0 !important;
  }
}

.addon-splitter {
  background-color: #fff;
  color: #000;
  height: 34px;

  &.disabled {
    opacity: .4;
  }
}

.work-list {
  position: absolute;
  top: 59px;
  left: 0;
  right: 0;
  bottom: 0;

  .work-list-left, .work-list-right {
    position: absolute;
    top: 0;
    bottom: 0;
    overflow: auto;

    th {
      text-align: center;
      white-space: nowrap;
      position: sticky;
      top: 0;
      box-shadow: 0 1px 1px rgba(0, 0, 0, .2);
      z-index: 11;
    }

    td, th {
      background-color: #fff;
    }
  }

  .work-list-left {
    left: 0;
    right: 175px;
    border-right: 1px solid #b1b1b1;
  }

  .work-list-right {
    left: 174px;
    right: 0;
  }
}

.num {
  background-color: #fff;
  cursor: pointer;

  span {
    float: right;
  }

  &:hover {
    background-color: #f5f5f5 !important;
    z-index: 10;
  }
}

.circle {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
  vertical-align: middle;
  margin-bottom: 3px;
  border: 1px #e2e2e2 solid;
}

:not(.active) .circle {
  box-shadow: 0 0 3px;
}
</style>
