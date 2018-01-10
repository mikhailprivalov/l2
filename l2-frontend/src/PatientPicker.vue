<template>
  <div>
    <div class="input-group">
      <div class="input-group-btn">
        <button class="btn btn-blue-nb btn-ell dropdown-toggle" type="button" data-toggle="dropdown"
                style="width: 200px;text-align: left!important;"><span class="caret"></span> {{selected_base.title}}
        </button>
        <ul class="dropdown-menu">
          <li v-for="row in bases" :value="row.pk" v-if="!row.hide && row.pk !== selected_base.pk"><a href="#"
                                                                                                      @click.prevent="select_base(row.pk)">{{row.title}}</a>
          </li>
        </ul>
      </div>
      <input type="text" class="form-control" v-model="query" placeholder="Введите запрос" autofocus
             :maxlength="query_limit">
      <span class="input-group-btn"><button style="margin-right: -2px" class="btn last btn-blue-nb" type="button"
                                            :disabled="!query_valid">Поиск</button></span>
    </div>

    <table class="table table-bordered table-condensed table-responsive"
           style="table-layout: fixed;margin: 0; padding: 0;margin-top:5px">
      <col width="127">
      <col>
      <col width="50">
      <col width="127">
      <col>
      <tr>
        <td style="max-width: 127px;" class="table-header-row">ФИО:&nbsp;</td>
        <td style="max-width: 99%;" class="table-content-row" colspan="2"></td>
        <td style="max-width: 127px;" class="table-header-row">Номер карты:&nbsp;</td>
        <td style="max-width: 99%;" class="table-content-row"></td>
      </tr>
      <tr>
        <td class="table-header-row">Дата рождения:&nbsp;</td>
        <td class="table-content-row"></td>
        <td class="table-header-row">Пол:&nbsp;</td>
        <td class="table-content-row"></td>
        <td class="table-content-row">
          <a href="#" onclick='open_search_results();return false;' id="search-results-link">поиск результатов</a>
        </td>
      </tr>
      <tr v-if="selected_base.history_number">
        <td class="table-header-row">
          <span class="hospital" style="display: block;line-height: 1.2;">Номер истории:&nbsp;</span>
        </td>
        <td class="table-content-row" colspan="4">
          <div style="height: 34px">
            <span class="hospital"><input type="text" class="form-control" maxlength="11"/></span>
          </div>
        </td>
      </tr>
    </table>
  </div>
</template>

<script>
  import LinkSelector from './LinkSelector'
  import PatientCard from './ui-cards/PatientCard'

  export default {
    name: 'patient-picker',
    components: {LinkSelector, PatientCard},
    data() {
      return {
        base: -1,
        query: '',
        search_type: 'auto',
        search_types: [
          {key: 'auto', title: 'авто', about: 'Автоматическое определение типа запроса', pattern: '.+'},
          {
            key: 'full_fio',
            title: 'полное фио и дата рождения',
            about: 'Введите ФИО и дату раждения. Возможен ввод частями, например: Иванов Иван Иванович 01.01.1990 или Петров Пётр',
            pattern: '^([А-яЕё]+)( ([А-яЕё]+)( ([А-яЕё]*)( ([0-9]{2}\\.[0-9]{2}\\.[0-9]{4}))?)?)?$'
          },
          {
            key: 'short_fio',
            title: 'краткое фио и дата рождения',
            about: 'Введите инициалы и дату рождения, например: иии01011990',
            pattern: '^[а-яА-ЯёЁ]{3}[0-9]{8}$',
            limit: 11
          },
          {
            key: 'polis',
            title: 'номер полиса ОМС',
            about: 'Введите серию (при необходимости через пробел) и номер полиса, например: 1234АБВ 123456789 или 3876543213213413',
            pattern: '.+'
          },
        ]
      }
    },
    created() {
      if (this.bases.length === 0) {
        this.$store.watch(state => state.bases, (oldValue, newValue) => {
          this.check_base()
        })
      }

      this.check_base()
    },
    watch: {
      bases() {
        this.check_base()
      }
    },
    computed: {
      bases() {
        return this.$store.getters.bases
      },
      selected_base() {
        for (let b of this.bases) {
          if (b.pk === this.base) {
            return b
          }
        }
        return {title: 'Не выбрана база', pk: -1, hide: false, history_number: false}
      },
      selected_type() {
        for (let b of this.search_types) {
          if (b.key === this.search_type) {
            return b
          }
        }
        return {key: '', title: 'не выбрано', about: ''}
      },
      query_limit() {
        if (this.selected_type.limit !== undefined) {
          return this.selected_type.limit
        }
        return 255
      },
      selected_pattern() {
        if (this.selected_type.pattern !== undefined) {
          return this.selected_type.pattern
        }
        return '.*'
      },
      normalized_query() {
        return this.query.trim()
      },
      query_valid() {
        let re = new RegExp(this.selected_pattern)
        return this.normalized_query.match(re)
      },
      active_type() {
        for (let b of this.search_types) {
          let re = new RegExp(b.pattern)
          if (b.key !== 'auto' && this.normalized_query.match(re)) {
            return b
          }
        }
        return {key: '', title: 'тип запроса не распознан', about: ''}
      }
    },
    methods: {
      select_base(pk) {
        this.base = pk
      },
      check_base() {
        if (this.base === -1 && this.bases.length > 0) {
          this.base = JSON.parse(JSON.stringify(this.bases[0].pk))
        }
      }
    }
  }
</script>

<style scoped lang="scss">
</style>
