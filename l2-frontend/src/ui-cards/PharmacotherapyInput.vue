<template>
  <div style="height: 100%; width: 100%; position: relative; min-height: 100px">
    <table
      class="table table-responsive table-bordered table-condensed"
      style="table-layout: fixed; margin-bottom: 0; background-color: #fff"
    >
      <colgroup>
        <col width="240">
        <col>
        <col>
        <col width="90">
        <col width="70">
        <col width="160">
        <col width="130">
        <col width="70">
        <col width="60">
        <col width="96">
      </colgroup>
      <thead>
        <tr>
          <th>Наименование ЛП</th>
          <th>Форма выпуска</th>
          <th>Способ применения</th>
          <th>Дозировка</th>
          <th>Ед.изм</th>
          <th>Режим приёма</th>
          <th>Дата начала</th>
          <th>Кол-во дней</th>
          <th>Шаг, дней</th>
          <th>Дата окончания</th>
        </tr>
      </thead>
      <tbody>
        <PharmacotherapyRow
          v-for="v in valueFiltered"
          :key="`${v.pk}-${v.remove}`"
          :data="v"
          :confirmed="confirmed"
          :params="params"
        />
        <tr v-if="value.length === 0">
          <td
            class="text-center"
            colspan="10"
          >
            нет назначений
          </td>
        </tr>
      </tbody>
    </table>
    <hr v-if="!confirmed">
    <div
      v-if="!confirmed"
      class="row"
    >
      <div class="col-xs-3">
        <div
          class="input-group"
          style="z-index: 0"
        >
          <input
            v-model="search"
            class="form-control"
            placeholder="Поиск назначения"
          >
          <span class="input-group-btn">
            <button
              class="btn btn-blue-nb"
              type="button"
              @click="search = ''"
            ><i class="fa fa-times" /></button>
          </span>
        </div>
        <div v-if="variants.length > 0">
          <small>выберите назначение из списка справа</small>
        </div>
      </div>
      <div
        class="col-xs-9"
        style="padding-left: 0"
      >
        <div
          v-for="v in variants"
          :key="v.pk"
          class="variant"
          @click="add(v.value, v.titleOrig)"
          v-html="/*eslint-disable-line vue/no-v-html*/ v.title"
        />
        <div
          v-if="search === ''"
          class="variant-msg"
        >
          выполните поиск для добавления назначений
        </div>
        <div
          v-else-if="variants.length === 0"
          class="variant-msg"
        >
          не найдено
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import moment from 'moment';

import * as actions from '@/store/action-types';
import PharmacotherapyRow from '@/ui-cards/PharmacotherapyRow.vue';

export default {
  name: 'PharmacotherapyInput',
  components: { PharmacotherapyRow },
  props: {
    value: {
      type: Array,
    },
    confirmed: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      search: '',
      variants: [],
      toRemove: [],
      params: {},
    };
  },
  computed: {
    valueFiltered() {
      return this.value.filter((v) => !v.remove);
    },
  },
  watch: {
    async search() {
      if (this.search.trim() === '') {
        this.variants = [];
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      const { data } = await fetch(`/api/autocomplete?type=drugs&value=${this.search}&limit=60`).then((r) => r.json());
      this.variants = [];
      const lowerSearch = this.search.trim().toLowerCase();
      const l = lowerSearch.length;
      for (const v of data) {
        const { title } = v;

        const parts = [];

        const indexes = [];
        let i = -1;

        // eslint-disable-next-line no-cond-assign
        while ((i = title.toLocaleLowerCase().indexOf(lowerSearch, i + 1)) !== -1) {
          indexes.push(i);
        }

        let lastIdx = 0;
        for (const idx of indexes) {
          parts.push(title.substring(lastIdx, idx), `<strong>${title.substring(idx, idx + l)}</strong>`);

          lastIdx = idx + l;
        }

        parts.push(title.substring(lastIdx));

        this.variants.push({
          value: v.pk,
          title: parts.join(''),
          titleOrig: title,
        });
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
  async mounted() {
    await this.$store.dispatch(actions.INC_LOADING);
    this.params = await this.$api('procedural-list/params');
    await this.$store.dispatch(actions.DEC_LOADING);
  },
  methods: {
    add(drugPk, drug) {
      // eslint-disable-next-line vue/no-mutating-props
      this.value.push({
        pk: Math.random() + Math.random(),
        isNew: true,
        remove: false,
        drug,
        drugPk,
        timesSelected: [],
        form_release: -1,
        method: -1,
        dosage: 1,
        step: 1,
        dateStart: moment().format('YYYY-MM-DD'),
        dateEnd: null,
        countDays: 1,
        units: null,
        comment: '',
      });
      this.search = '';
    },
  },
};
</script>

<style scoped lang="scss">
.variant {
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);

  &:hover {
    color: #fff;
    background-color: #049372;
    box-shadow: 0 14px 28px rgba(#049372, 0.35), 0 10px 10px rgba(#049372, 0.32);
    position: relative;
    z-index: 1;
    transform: scale(1.008) translateX(-2px);
  }
}

.variant,
.variant-msg {
  color: #000;
  background: rgba(0, 0, 0, 0.05);
  padding: 7px 5px;
  margin: 4px 0 2px 4px;
  border-radius: 5px;

  &:first-child {
    margin-top: 0;
  }
}

.prec {
  margin-right: -1px;
  z-index: 0;
}

.prec ::v-deep .input-group {
  border-radius: 0;
  width: 100%;
  z-index: 0;
}

.prec ::v-deep input {
  border-radius: 0 !important;
}

.prec ::v-deep ul {
  position: relative;
  font-size: 13px;
  z-index: 1000;
}

.prec ::v-deep ul li {
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 2px 0.25rem;
  margin: 0 0.2rem;
  a {
    padding: 2px 10px;
  }
}
</style>
