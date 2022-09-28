<template>
  <div class="root">
    <div class="card-no-hover card card-1">
      <h4 class="text-center">
        Настройка скрининга
      </h4>

      <table class="table table-bordered table-condensed table-striped table-screening">
        <colgroup>
          <col style="width: 80px">
          <col>
          <col style="width: 180px">
          <col style="width: 180px">
          <col style="width: 180px">
          <col style="width: 180px">
          <col style="width: 40px">
        </colgroup>
        <thead>
          <tr>
            <th />
            <th>Исследование</th>
            <th>Пол</th>
            <th>Возраст</th>
            <th>Период, раз в N лет</th>
            <th>Скрыть</th>
            <th />
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in orderBy(rows, 'sort_weight')"
            :key="row.pk"
          >
            <td class="cl-td">
              <div class="incdec">
                <button
                  class="btn btn-primary-nb btn-sm"
                  :disabled="isFirst(row)"
                  @click="dec(row)"
                >
                  <i class="glyphicon glyphicon-arrow-up" />
                </button>
                <button
                  class="btn btn-primary-nb btn-sm"
                  :disabled="isLast(row)"
                  @click="inc(row)"
                >
                  <i class="glyphicon glyphicon-arrow-down" />
                </button>
              </div>
            </td>
            <td>
              {{ researches_obj[row.research_id].title }}
            </td>
            <td class="cl-td">
              <select
                v-model="row.sex_client"
                class="form-control"
                @change="changeRow(row)"
              >
                <option
                  v-for="s in SEX"
                  :key="s.id"
                  :value="s.id"
                >
                  {{ s.label }}
                </option>
              </select>
            </td>
            <td class="cl-td">
              <div class="input-group">
                <input
                  v-model.number="row.age_start_control"
                  class="form-control"
                  type="number"
                  :min="0"
                  :max="row.age_end_control"
                  placeholder="от"
                  @change="changeRow(row)"
                  @keypress="changeRow(row)"
                  @input="changeRow(row)"
                >
                <span class="input-group-addon addon-splitter">—</span>
                <input
                  v-model.number="row.age_end_control"
                  class="form-control"
                  type="number"
                  :min="row.age_start_control"
                  :max="120"
                  placeholder="до (вкл)"
                  @change="changeRow(row)"
                  @keypress="changeRow(row)"
                  @input="changeRow(row)"
                >
              </div>
            </td>
            <td class="cl-td">
              <input
                v-model.number="row.period"
                class="form-control"
                type="number"
                :min="1"
                :max="100"
                placeholder="период"
                @change="changeRow(row)"
                @keypress="changeRow(row)"
                @input="changeRow(row)"
              >
            </td>
            <td class="cl-td">
              <label>
                <input
                  v-model="row.hide"
                  type="checkbox"
                  @change="changeRow(row)"
                  @keypress="changeRow(row)"
                  @input="changeRow(row)"
                >
              </label>
            </td>
            <td
              :key="`${row.pk}_${row.hasChanges}`"
              class="cl-td"
            >
              <div class="save-td">
                <button
                  v-if="row.hasChanges"
                  v-tippy
                  class="btn btn-primary-nb btn-sm btn-block btn-save"
                  :disabled="isRowDisabled(row)"
                  :title="isRowDisabled(row) ? 'Некорректные данные' : 'Сохранить'"
                  @click="saveRow(row)"
                >
                  <i class="fas fa-save" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="card-no-hover card card-1">
      <h5 class="text-center">
        Добавить новую запись
      </h5>
      <h6>Услуга или исследование</h6>
      <div class="researches-wrapper">
        <researches-picker
          v-model="serviceToCreate"
          autoselect="none"
          :hidetemplates="true"
          :oneselect="true"
          kk="screening"
        />
      </div>
      <h6>Параметры</h6>
      <table
        class="table table-bordered table-condensed"
        style="width: 360px"
      >
        <colgroup>
          <col style="width: 180px">
          <col>
        </colgroup>
        <tbody>
          <tr>
            <th>Пол</th>
            <td class="cl-td">
              <select
                v-model="sexToCreate"
                class="form-control"
              >
                <option
                  v-for="s in SEX"
                  :key="s.id"
                  :value="s.id"
                >
                  {{ s.label }}
                </option>
              </select>
            </td>
          </tr>
          <tr>
            <th>Возраст</th>
            <td class="cl-td">
              <div class="input-group">
                <input
                  v-model.number="ageFromToCreate"
                  class="form-control"
                  type="number"
                  :min="0"
                  :max="ageToToCreate"
                  placeholder="от"
                >
                <span class="input-group-addon addon-splitter">—</span>
                <input
                  v-model.number="ageToToCreate"
                  class="form-control"
                  type="number"
                  :min="ageFromToCreate"
                  :max="120"
                  placeholder="до"
                >
              </div>
            </td>
          </tr>
          <tr>
            <th>Период, раз в {{ periodToCreate | pluralAge }}</th>
            <td class="cl-td">
              <input
                v-model.number="periodToCreate"
                class="form-control"
                type="number"
                :min="1"
                :max="100"
                placeholder="период"
              >
            </td>
          </tr>
        </tbody>
      </table>

      <button
        class="btn btn-primary-nb"
        :disabled="!serviceToCreate || !periodToCreate || !ageFromToCreate || !ageToToCreate"
        @click="create"
      >
        <template v-if="!serviceToCreate || !researches_obj[serviceToCreate]">
          Услуга или исследование не выбрано
        </template>
        <template v-else>
          Создать запись «{{ researches_obj[serviceToCreate].title }}, {{ sexToCreate }}, {{ ageFromToCreate }} —
          {{ ageToToCreate }}, раз в {{ periodToCreate | pluralAge }}»
        </template>
      </button>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import Vue2Filters from 'vue2-filters';
import { mapGetters } from 'vuex';

import * as actions from '@/store/action-types';
import ResearchesPicker from '@/ui-cards/ResearchesPicker.vue';

Vue.use(Vue2Filters);

const SEX = [
  { id: 'в', label: 'все' },
  { id: 'м', label: 'м' },
  { id: 'ж', label: 'ж' },
];

@Component({
  components: {
    ResearchesPicker,
  },
  mixins: [Vue2Filters.mixin],
  data() {
    return {
      SEX,
      rows: [],
      serviceToCreate: null,
      sexToCreate: SEX[0].id,
      ageFromToCreate: 18,
      ageToToCreate: 100,
      periodToCreate: 1,
    };
  },
  computed: {
    ...mapGetters(['researches_obj']),
    hasResearches() {
      return this.researches_obj && Object.keys(this.researches_obj).length > 0;
    },
  },
  watch: {
    hasResearches: {
      immediate: true,
      handler() {
        if (this.hasResearches) {
          this.loadRows();
        }
      },
    },
  },
})
export default class ConstructScreening extends Vue {
  researches_obj: any;

  SEX: any;

  rows: any[];

  orderBy: any;

  serviceToCreate: number | null;

  sexToCreate: string;

  ageFromToCreate: number;

  ageToToCreate: number;

  periodToCreate: number;

  async loadRows() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { rows } = await this.$api('screening/get-directory');
    this.rows = rows;
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  inc(row) {
    let next = row.sort_weight + 1;
    if (Number.isNaN(next)) {
      next = 0;
    }
    const nextRow = this.rows.find(r => r.sort_weight === next);
    if (nextRow) {
      nextRow.sort_weight = row.sort_weight;
    }

    // eslint-disable-next-line no-param-reassign
    row.sort_weight = next;

    setTimeout(() => this.saveRows({ ...row }, { ...nextRow }), 10);
  }

  dec(row) {
    let next = row.sort_weight - 1;
    if (Number.isNaN(next)) {
      next = 0;
    }
    const nextRow = this.rows.find(r => r.sort_weight === next);
    if (nextRow) {
      nextRow.sort_weight = row.sort_weight;
    }

    // eslint-disable-next-line no-param-reassign
    row.sort_weight = next;

    setTimeout(() => this.saveRows({ ...row }, { ...nextRow }), 10);
  }

  // eslint-disable-next-line class-methods-use-this
  isFirst(row) {
    return row.sort_weight === 0;
  }

  isLast(row) {
    return row.sort_weight === Math.max(...this.rows.map(r => r.sort_weight));
  }

  // eslint-disable-next-line class-methods-use-this
  isRowDisabled(row) {
    return !row.period || !row.age_start_control || !row.age_end_control;
  }

  // eslint-disable-next-line class-methods-use-this
  changeRow(row) {
    // eslint-disable-next-line no-param-reassign
    row.hasChanges = true;
  }

  get nextOrder() {
    return this.rows.length > 0 ? Math.max(...this.rows.map(r => r.sort_weight)) + 1 : 0;
  }

  async create() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { ok, message } = await this.$api('screening/save', {
      service: this.serviceToCreate,
      sex: this.sexToCreate,
      ageFrom: this.ageFromToCreate,
      ageTo: this.ageToToCreate,
      period: this.periodToCreate,
      sortWeight: this.nextOrder,
    });
    if (ok) {
      this.serviceToCreate = null;
      this.$root.$emit('researches-picker:deselect_allscreening');
      this.$root.$emit('msg', 'ok', 'Скрининг добавлен!');
    } else {
      this.$root.$emit('msg', 'error', `Ошибка: ${message}`);
    }
    await this.loadRows();
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async saveRows(row1, row2) {
    await Promise.all([
      row1 ? this.saveRow(row1, true) : Promise.resolve(null),
      row2 ? this.saveRow(row2, true) : Promise.resolve(null),
    ]);
  }

  async saveRow(row, disableReloading = false) {
    await this.$store.dispatch(actions.INC_LOADING);
    const { ok, message } = await this.$api('screening/save', {
      screening: row.pk,
      service: row.research_id,
      sex: row.sex_client,
      ageFrom: row.age_start_control,
      ageTo: row.age_end_control,
      period: row.period,
      sortWeight: row.sort_weight,
      hide: row.hide,
    });
    if (ok) {
      this.$root.$emit('msg', 'ok', 'Скрининг обновлён!');
    } else {
      this.$root.$emit('msg', 'error', `Ошибка: ${message}`);
    }
    if (!disableReloading) {
      await this.loadRows();
    }
    await this.$store.dispatch(actions.DEC_LOADING);
  }
}
</script>

<style lang="scss" scoped>
.table-screening {
  table-layout: fixed;
}

.incdec {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  gap: 1px;
  padding: 1px;
  justify-content: stretch;
  align-items: stretch;

  .btn {
    flex: 0 50%;
    width: unset !important;
  }
}

.root {
  max-width: 1200px;
  margin: 0 auto;
}

.addon-splitter {
  background-color: #fff;
  color: #000;
  padding: 6px;
}

.researches-wrapper {
  position: relative;
  height: 345px;
  background: #fff;
  border-bottom: 1px solid #aaa;
}

.card {
  padding: 6px 12px;
  margin-left: 0;
  margin-right: 0;
  margin-bottom: 18px;
}

.cl-td .input-group {
  display: flex;
  flex-direction: row;

  .form-control {
    width: calc(50% - 14px);
    flex: 1 calc(50% - 14px);
  }

  .addon-splitter {
    width: 28px;
    flex: 1 28px;
  }
}

.cl-td .btn {
  height: 32px;
}

.save-td {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  gap: 1px;
  padding: 1px;
  justify-content: stretch;
  align-items: stretch;

  .btn {
    flex: 0 100%;
    width: unset !important;
  }
}
</style>
