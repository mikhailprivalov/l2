<template>
  <div class="root">
    <div class="left-bar">
      <div class="inner">
        <h5>Фильтры</h5>

        <table class="table table-bordered table-condensed">
          <colgroup>
            <col style="width: 120px">
            <col>
          </colgroup>
          <tbody>
            <tr>
              <th>Год</th>
              <td class="x-cell">
                <input
                  v-model="year"
                  type="number"
                  class="form-control"
                  min="2018"
                  max="2100"
                >
              </td>
            </tr>
            <tr>
              <th>Услуга</th>
              <td class="cl-td">
                <Treeselect
                  v-model="research"
                  :multiple="false"
                  :disable-branch-nodes="true"
                  :options="researches"
                  placeholder="Услуга не выбрана"
                  :append-to-body="true"
                  class="treeselect-noborder"
                  :clearable="false"
                />
              </td>
            </tr>
            <tr>
              <th>Номер случая</th>
              <td class="x-cell">
                <input
                  v-model.trim="caseNumber"
                  type="text"
                  class="form-control"
                >
              </td>
            </tr>
            <tr>
              <th>
                <div class="mh-34">
                  Стационар
                </div>
              </th>
              <td class="x-cell">
                <label>
                  <input
                    v-model="hosp"
                    type="checkbox"
                  >
                </label>
              </td>
            </tr>
            <tr v-if="hosp">
              <th>
                <div class="mh-34">
                  Дата выписки
                </div>
              </th>
              <td class="x-cell">
                <DateRange v-model="dateExaminationRange" />
              </td>
            </tr>
            <tr>
              <th>
                <div class="mh-34">
                  Исполнитель
                </div>
              </th>
              <td class="x-cell">
                <Treeselect
                  v-model="docConfirm"
                  class="treeselect-noborder"
                  :multiple="false"
                  :disable-branch-nodes="true"
                  :options="usersConfirm"
                  placeholder="Пользователь не выбран"
                  :clearable="true"
                />
              </td>
            </tr>
          </tbody>
        </table>

        <button
          class="btn btn-blue-nb btn-block"
          :disabled="!isValid"
        >
          Поиск
        </button>
      </div>
    </div>
    <div class="right-content">
      <div class="inner">
        TODO 2
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import moment from 'moment';
import Vue from 'vue';
import Component from 'vue-class-component';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import Paginate from 'vuejs-paginate';

// import * as actions from '@/store/action-types';
import usersPoint from '@/api/user-point';
import RadioFieldById from '@/fields/RadioFieldById.vue';
import DateFieldNav2 from '@/fields/DateFieldNav2.vue';
import DoctorProfileTreeselectField from '@/fields/DoctorProfileTreeselectField.vue';
import DateRange from '@/ui-cards/DateRange.vue';

@Component({
  components: {
    Treeselect,
    RadioFieldById,
    DateFieldNav2,
    DateRange,
    DoctorProfileTreeselectField,
    Paginate,
  },
  data() {
    return {
      year: moment().year(),
      research: -1,
      researches: [],
      hosp: false,
      caseNumber: '',
      dateExaminationRange: [moment().subtract(2, 'month').format('DD.MM.YYYY'), moment().format('DD.MM.YYYY')],
      docConfirm: null,
      usersConfirm: [],
    };
  },
  mounted() {
    this.$api('researches/descriptive-research').then(rows => {
      this.researches = rows;
    });
  },
  watch: {
  },
})
export default class SearchPage extends Vue {
  year: number;

  research: number;

  researches: any[];

  caseNumber: string;

  hosp: boolean;

  dateExaminationRange: string[];

  docConfirm: null | number;

  get isValid() {
    return !!this.year && !!this.research && this.research !== -1;
  }
}
</script>

<style lang="scss" scoped>
$sidebar-width: 400px;

.root {
  position: absolute;
  top: 36px;
  left: 0;
  right: 0;
  bottom: 0;

  overflow-x: hidden;
  overflow-y: hidden;
}

.left-bar, .right-content {
  position: absolute;
  top: 0;
  bottom: 0;

  overflow-x: visible;
  overflow-y: auto;

  .inner {
    padding: 10px;
  }
}

.left-bar {
  left: 0;
  right: calc(100% - #{$sidebar-width});

  background: #f2f2f2;

  h5 {
    margin-top: 0;
  }

  table {
    table-layout: fixed;

    .x-cell {
      .form-control {
        border: none;
      }
    }
  }
}

.right-content {
  right: 0;
  left: $sidebar-width;

  border-left: 1px solid #b1b1b1;
  background: #fff;
}

.mh-34 {
  min-height: 24px;
}
</style>

<style>
.pagination {
  margin-top: 0 !important;
}
</style>
