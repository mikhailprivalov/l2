<template>
  <div class="root">
    <div class="row">
      <div class="col-xs-5">
        <h4>{{ title }} – коды ФСЛИ</h4>
      </div>
      <div class="col-xs-5">
        <h4>Период действия результата (в днях)</h4>
      </div>
      <div class="col-xs-2 display-header align-header">
        <input
          v-model="actualPeriod"
          type="number"
          min="0"
          max="365"
          step="1"
          class="form-control"
        >
      </div>
    </div>
    <table class="table table-bordered table-condensed">
      <colgroup>
        <col width="280">
        <col width="100">
        <col>
      </colgroup>
      <thead>
        <tr>
          <th>Название теста (фракции)</th>
          <th>Код ФСЛИ</th>
          <th>Единицы измерения</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="f in fractions"
          :key="`${f.pk}_${f.title}`"
        >
          <td>{{ f.title }}{{ f.units && !f.unit ? ', ' + f.units : '' }}</td>
          <td class="cl-td">
            <TypeAhead
              v-model="f.fsli"
              :delay-time="150"
              :get-response="resp => [...resp.data.data]"
              no-result-text="Не найдено"
              placeholder="Код ФСЛИ"
              searching-text="Поиск..."
              :highlighting="(item, vue) => item.toString().replace(vue.query, `<b>${vue.query}</b>`)"
              :limit="14"
              :min-chars="1"
              :render="
                items =>
                  items.map(
                    i =>
                      // eslint-disable-next-line max-len
                      `${i.code_fsli} – ${i.title} – ${i.sample}${i.synonym ? ' – ' + i.synonym : ''}${
                        i.nmu ? ' – ' + i.nmu : ''
                      }`,
                  )
              "
              :on-hit="onHit(f)"
              :select-first="true"
              maxlength="128"
              src="/api/autocomplete?value=:keyword&type=fsli&limit=14"
            />
          </td>
          <td class="cl-td">
            <Treeselect
              v-model="f.unit"
              class="treeselect-noborder"
              :multiple="false"
              :disable-branch-nodes="true"
              :options="unitOptions"
              placeholder="не выбрано"
              :append-to-body="true"
              :clearable="true"
            />
          </td>
        </tr>
      </tbody>
    </table>

    <button
      type="button"
      class="btn btn-primary-nb btn-blue-nb"
      @click="save"
    >
      Сохранить изменения
    </button>
  </div>
</template>

<script lang="ts">
import TypeAhead from 'vue2-typeahead';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import * as actions from '@/store/action-types';
import laboratoryPoint from '@/api/laboratory-point';

export default {
  components: { TypeAhead, Treeselect },
  props: {
    pk: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      fractions: [],
      title: '',
      unitOptions: [],
      actualPeriod: 0,
    };
  },
  mounted() {
    this.loadData();
  },
  methods: {
    async loadData() {
      await this.$store.dispatch(actions.INC_LOADING);
      const [{ fractions, title, actualPeriod }, { rows }] = await Promise.all([
        laboratoryPoint.getFractions(this, 'pk'),
        this.$api('/laboratory/units'),
      ]);

      this.unitOptions = rows;
      this.fractions = fractions;
      this.title = title;
      this.actualPeriod = actualPeriod;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async save() {
      await this.$store.dispatch(actions.INC_LOADING);
      await laboratoryPoint.saveFsli(this, ['fractions', 'pk', 'actualPeriod']);
      this.$root.$emit('msg', 'ok', 'Сохранено');
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    onHit(f) {
      return item => {
        // eslint-disable-next-line no-param-reassign
        f.fsli = item.split('–')[0].trim();
      };
    },
  },
};
</script>

<style scoped lang="scss">
.root {
  max-width: 1000px;

  td:not(.x-cell) {
    ::v-deep ul {
      width: auto;
      font-size: 13px;
    }

    ::v-deep ul li {
      overflow: hidden;
      text-overflow: ellipsis;
      padding: 2px 0.25rem;
      margin: 0 0.2rem;

      a {
        padding: 2px 10px;
      }
    }

    ::v-deep input {
      background: #fff;
      border: none;
      border-radius: 0 !important;
      width: 100%;
      flex: 0 100%;
    }

    ::v-deep .input-group {
      border-radius: 0;
      width: 100%;
    }
  }
.display-header {
  padding-top: 5px;
}
}
</style>
