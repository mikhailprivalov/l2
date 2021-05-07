<template>
  <div style="height: 100%;width: 100%;position: relative;min-height: 100px;">
    <table class="table table-responsive table-bordered table-condensed"
           style="table-layout: fixed;margin-bottom: 0;background-color: #fff">
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
        <PharmacotherapyRow :data="v" :confirmed="confirmed" :params="params" v-for="v in valueFiltered"
                            :key="`${v.pk}-${v.remove}`" />
        <tr v-if="value.length === 0">
          <td class="text-center" colspan="10">нет назначений</td>
        </tr>
        </tbody>
      </table>
    <hr v-if="!confirmed"/>
    <div class="row" v-if="!confirmed">
      <div class="col-xs-3">
        <div class="input-group" style="z-index: 0">
          <input class="form-control" placeholder="Поиск назначения" v-model="search">
          <span class="input-group-btn">
            <button @click="search = ''" class="btn btn-blue-nb" type="button"><i class="fa fa-times"></i></button>
          </span>
        </div>
        <div v-if="variants.length > 0">
          <small>выберите назначение из списка справа</small>
        </div>
      </div>
      <div class="col-xs-9" style="padding-left: 0">
        <div @click="add(v.value, v.titleOrig)" class="variant" v-for="v in variants" :key="v.pk" v-html="v.title" />
        <div class="variant-msg" v-if="search === ''">выполните поиск для добавления назначений</div>
        <div class="variant-msg" v-else-if="variants.length === 0">не найдено</div>
      </div>
    </div>
  </div>
</template>

<script>
import * as actions from '@/store/action-types';
import api from '@/api';
import PharmacotherapyRow from '@/ui-cards/PharmacotherapyRow.vue';
import moment from 'moment';

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
  async mounted() {
    await this.$store.dispatch(actions.INC_LOADING);
    this.params = await api('procedural-list/params');
    await this.$store.dispatch(actions.DEC_LOADING);
  },
  methods: {
    add(drugPk, drug) {
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
  computed: {
    valueFiltered() {
      return this.value.filter(v => !v.remove);
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
          parts.push(
            title.substring(lastIdx, idx),
            `<strong>${title.substring(idx, idx + l)}</strong>`,
          );

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
};
</script>

<style scoped lang="scss">
  .variant {
    cursor: pointer;
    transition: all .2s cubic-bezier(.25, .8, .25, 1);

    &:hover {
      color: #fff;
      background-color: #049372;
      box-shadow: 0 14px 28px rgba(#049372, 0.35), 0 10px 10px rgba(#049372, 0.32);
      position: relative;
      z-index: 1;
      transform: scale(1.008) translateX(-2px);
    }
  }

  .variant, .variant-msg {
    color: #000;
    background: rgba(0, 0, 0, .05);
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
    border-radius: 0!important;
  }

  .prec ::v-deep ul {
    position: relative;
    font-size: 13px;
    z-index: 1000;
  }

  .prec ::v-deep ul li {
    overflow: hidden;
    text-overflow: ellipsis;
    padding: 2px .25rem;
    margin: 0 .2rem;
    a {
      padding: 2px 10px;
    }
  }
</style>
