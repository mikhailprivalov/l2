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
      <tr v-for="f in fractions">
        <td>
          {{f.title}}{{f.units ?  ', ' + f.units : ''}}
        </td>
        <td class="cl-td">
          <TypeAhead :delayTime="150" :getResponse="resp => [...resp.data.data]"
                     NoResultText="Не найдено"
                     placeholder="Код ФСЛИ"
                     SearchingText="Поиск..."
                     :highlighting="(item, vue) => item.toString().replace(vue.query, `<b>${vue.query}</b>`)"
                     :limit="10" :minChars="1"
                     :render="items => items.map(i => `${i.code_fsli} – ${i.short_title} – ${i.sample}${i.synonym ? ' – ' + i.synonym : ''}${i.nmu ? ' – ' + i.nmu : ''}`)"
                     :onHit="onHit(f)"
                     :selectFirst="true"
                     maxlength="128"
                     src="/api/autocomplete?value=:keyword&type=fsli&limit=10" v-model="f.fsli"
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
  import * as action_types from '../store/action-types'
  import laboratory_point from '../api/laboratory-point'
  import TypeAhead from 'vue2-typeahead'

  export default {
    components: {TypeAhead},
    props: {
      pk: {
        type: String,
        required: true,
      }
    },
    data() {
      return {
        fractions: [],
        title: '',
      }
    },
    mounted() {
      this.loadData();
    },
    methods: {
      async loadData() {
        await this.$store.dispatch(action_types.INC_LOADING)
        const {fractions, title} = await laboratory_point.getFractions(this, 'pk');
        this.fractions = fractions;
        this.title = title;
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      async save() {
        await this.$store.dispatch(action_types.INC_LOADING)
        await laboratory_point.saveFsli(this, 'fractions');
        okmessage('Сохранено');
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      onHit(f) {
        return item => {
          f.fsli = item.split('–')[0].trim();
        }
      },
    },
  }
</script>

<style scoped lang="scss">
  .root {
    max-width: 650px;
    margin: 0 auto;

    /deep/ ul {
      width: auto;
      font-size: 13px;
    }

    /deep/ ul li {
      overflow: hidden;
      text-overflow: ellipsis;
      padding: 2px .25rem;
      margin: 0 .2rem;

      a {
        padding: 2px 10px;
      }
    }

    /deep/ input {
      background: #fff;
      border: none;
      border-radius: 0 !important;
      width: 100%;
      flex: 0 100%;
    }

    /deep/ .input-group {
      border-radius: 0;
      width: 100%;
    }
  }
</style>
