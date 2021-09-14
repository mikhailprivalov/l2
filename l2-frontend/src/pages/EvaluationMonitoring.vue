<template>
  <div>
    <form class="panel panel-default panel-flt" style="margin: 20px;" @submit.prevent="load()">
      <div class="panel-body" style="overflow: visible;">
        <div class="row" style="margin-top:5px;">
          <div class="col-xs-6">
            <div class="input-group treeselect-noborder-left">
              <span class="input-group-addon">Больница</span>
              <treeselect
                :multiple="false"
                :disable-branch-nodes="true"
                :options="visibleHospitals"
                placeholder="Больница не выбрана"
                v-model="params.hospital"
                :clearable="false"
                class="treeselect-wide"
              />
            </div>
          </div>
          <div class="col-xs-1">
            <div class="input-group">
              <span class="input-group-addon">Год</span>
              <input class="form-control" type="number" value="2021" v-model="params.year" style="min-width: 6em"/>
            </div>
          </div>
          <div class="col-xs-5">
            <div class="input-group treeselect-noborder-right">
              <span class="input-group-addon">Период</span>
              <treeselect
                :multiple="false"
                :disable-branch-nodes="true"
                :options="periods"
                placeholder="Больница не выбрана"
                v-model="params.quarter"
                :clearable="false"
                class="treeselect-wide "
              />
            </div>
          </div>
        </div>
      </div>
    </form>
    <div class="not-loaded" v-if="!loaded">
      Данные не загружены<br />
      <a class="a-under" href="#" @click.prevent="load">загрузить</a>
    </div>
    <div v-else class="data">
      <table class="table table-bordered table-condensed table-hover table-list">
        <colgroup>
          <col style="width: 400px"/>
          <col style="width: 200px" />
          <col style="width: 150px" />
          <col style="width: 80px" />
          <col style="width: 100px" />
          <col style="width: 200px" />
          <col v-if="canEdit" style="width: 100px" />
        </colgroup>
        <thead>
          <tr v-if="rows.length !== 0">
            <th>Показатель</th>
            <th>Показатель организации</th>
            <th>Оценка организации</th>
            <th>Куратор</th>
            <th>Оценка куратора</th>
            <th>Коментарий куратора</th>
            <th v-if="canEdit">Изменить</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" v-bind:key="r.editing">
            <td> {{ r.title }} </td>

            <td> {{ get_text_or_aggregate(r.fields[0]) }} </td>
            
            <td> {{ r.fields[1].value_aggregate }} </td>

            <td v-if="(can_view_field(r) & canEdit) || !canEdit"> {{ r.grade.grader }} </td>

            <td v-if="(can_view_field(r) & canEdit) || !canEdit"> {{ r.grade.grade}} </td>

            <td v-if="(can_view_field(r) & canEdit) || !canEdit"> {{ r.grade.comment }} </td>

            <th v-if="can_view_field(r) & canEdit">
              <button class="btn btn-blue-nb" @click="edit(r)">Изменить</button>
            </th>

            <td v-if="!can_view_field(r) & canEdit" colspan="4" class="text-center">
              <evaluation-monitoring-fast-editor :data="r" @sendData="load($event)" @cancelEdit="cancel_edit(r)"/>
            </td>

          </tr>
          <tr v-if="rows.length === 0">
            <td colspan="7" class="text-center">
              Нет отчетов организации за выбранный период
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import _ from 'lodash';

import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import * as actions from '@/store/action-types';
import EvaluationMonitoringFastEditor from '@/ui-cards/EvaluationMonitoringFastEditor.vue';
import { EvaluationMonitoringGroup, EvaluationMonitoringField, EvaluationMonitoringGrade } from '@/types/evaluationMonitoring';
import TreeSelectField from '@/fields/TreeSelectField.vue';

interface Params {
  hospital: number;
  quarter: number;
  year: number;
}

const EMPTY_ROWS: EvaluationMonitoringGroup[] = [];

@Component({
  components: {
    EvaluationMonitoringFastEditor,
    Treeselect,
    TreeSelectField,
  },
  data() {
    return {
      hospitals: [],
      rows: EMPTY_ROWS,
      loaded: false,
      edited_fields: [],
      params: {
        hospital: -1,
        quarter: -1,
        year: (new Date()).getFullYear(),
      },
      periods: [
        {
          id: -1,
          label: "Год"
        },
        {
          id: 1,
          label: "1 квартал"
        },
        {
          id: 2,
          label: "2 квартал"
        },
        {
          id: 3,
          label: "3 квартал"
        },
        {
          id: 4,
          label: "4 квартал"
        },
      ],
    };
  },
  beforeMount() {
    this.$store.watch(
      state => state.user.data,
      (oldValue, newValue) => {
        if (this.params.hospital === -1 && newValue) {
          this.params.hospital = newValue.hospital || -1;
        }
      },
      { immediate: true },
    );
    this.$store.dispatch(actions.GET_USER_DATA);
  },
  watch: {
    watchParams: {
      deep: true,
      handler() {
        this.load();
      },
    },
    watchParamsDebounce: {
      deep: true,
      handler: _.debounce(function () {
        this.load();
      }, 200),
    },
  },
  async mounted() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { hospitals } = await this.$api('hospitals', { filterByUserHospital: false });
    this.hospitals = hospitals;
    await this.$store.dispatch(actions.DEC_LOADING);
  },
})
export default class ExtraNotification extends Vue {
  params: Params;

  rows: EvaluationMonitoringGroup[];

  loaded: boolean;

  edited_fields: EvaluationMonitoringGroup[];

  hospitals: any[];

  periods: any[];

  get canEdit() {
    for (const g of this.$store.getters.user_data.groups || []) {
      if (g === 'Просмотр мониторингов') {
        return true;
      }
    }
    return false;
  }

  get watchParams() {
    return _.pick(this.params, ['hospital', 'quarter', 'year']);
  }

  get visibleHospitals() {
    return this.canEdit ? this.hospitals : this.hospitals.filter(h => h.id === this.$store.getters.user_data.hospital);
  }

  edit(group: EvaluationMonitoringGroup) {
    group.editing = true;
    this.$forceUpdate();
  }

  cancel_edit(group: EvaluationMonitoringGroup) {
    group.editing = false;
    this.$forceUpdate();
  }

  get_text_or_aggregate(field: EvaluationMonitoringField) {
    return field.value_text === "" ? field.value_aggregate : field.value_text;
  }

  can_view_field(group: EvaluationMonitoringGroup) {
    return group.grade.grade !== null && !group.editing;
  }

  async load(arg) {
    await this.$store.dispatch(actions.INC_LOADING);
    const data = await this.$api('evaluation_monitoring/load', this.params);
    this.rows = data.rows.map((el: EvaluationMonitoringGroup) => {el.editing = false; return el;});
    await this.$store.dispatch(actions.DEC_LOADING);
    this.loaded = true;
  }

  covid() {
  }
}
</script>

<style>
.pagination {
  margin-top: 0 !important;
}
</style>

<style lang="scss" scoped>
.not-loaded {
  text-align: center;
  color: grey;
}

.data {
  padding: 0 20px;
}

.founded {
  text-align: center;
  padding: 5px;
  margin-top: -5px;
}

.addon-splitter {
  background-color: #fff;

  &.disabled {
    opacity: 0.4;
  }
}

.date-time {
  input {
    line-height: 1;
  }
}

.date-nav ::v-deep .btn:last-child {
  border-top-right-radius: 4px;
  border-bottom-right-radius: 4px;
}

.table-list {
  table-layout: fixed;

  thead th {
    position: sticky;
    top: -1px;
    background: #fff;
  }
}
</style>
