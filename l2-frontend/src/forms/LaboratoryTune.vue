<template>
  <div class="root">
    <h4>{{title}} – коды ФСЛИ</h4>

    <table class="table table-bordered table-condensed">
      <colgroup>
        <col width="280" />
        <col />
      </colgroup>
      <thead>
        <tr>
          <th>Название теста (фракции)</th>
          <th>Код ФСЛИ</th>
        </tr>
      </thead>
      <tbody>
      <tr v-for="f in fractions" :key="`${f.pk}_${f.title}`">
        <td>
          {{f.title}}{{f.units ?  ', ' + f.units : ''}}
        </td>
        <td class="cl-td">
          <TypeAhead :delayTime="150" :getResponse="resp => [...resp.data.data]"
                     NoResultText="Не найдено"
                     placeholder="Код ФСЛИ"
                     SearchingText="Поиск..."
                     :highlighting="(item, vue) => item.toString().replace(vue.query, `<b>${vue.query}</b>`)"
                     :limit="14" :minChars="1"
                     :render="items => (
                       items.map(i => (
                         // eslint-disable-next-line max-len
                         `${i.code_fsli} – ${i.title} – ${i.sample}${i.synonym ? ' – ' + i.synonym : ''}${i.nmu ? ' – ' + i.nmu : ''}`
                       ))
                     )"
                     :onHit="onHit(f)"
                     :selectFirst="true"
                     maxlength="128"
                     src="/api/autocomplete?value=:keyword&type=fsli&limit=14" v-model="f.fsli"
          />
        </td>
      </tr>
      </tbody>
    </table>

    <button type="button" @click="save" class="btn btn-primary-nb btn-blue-nb">
      Сохранить изменения
    </button>
  </div>
</template>

<script>
import TypeAhead from 'vue2-typeahead';
import * as actions from '../store/action-types';
import laboratory_point from '../api/laboratory-point';

export default {
  components: { TypeAhead },
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
    };
  },
  mounted() {
    this.loadData();
  },
  methods: {
    async loadData() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { fractions, title } = await laboratory_point.getFractions(this, 'pk');
      this.fractions = fractions;
      this.title = title;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async save() {
      await this.$store.dispatch(actions.INC_LOADING);
      await laboratory_point.saveFsli(this, 'fractions');
      window.okmessage('Сохранено');
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    onHit(f) {
      return (item) => {
        // eslint-disable-next-line no-param-reassign
        f.fsli = item.split('–')[0].trim();
      };
    },
  },
};
</script>

<style scoped lang="scss">
  .root {
    max-width: 650px;

    ::v-deep ul {
      width: auto;
      font-size: 13px;
    }

    ::v-deep ul li {
      overflow: hidden;
      text-overflow: ellipsis;
      padding: 2px .25rem;
      margin: 0 .2rem;

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
</style>
