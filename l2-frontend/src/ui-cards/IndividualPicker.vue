<template>
  <div>
    <div class="input-group">
      <input type="text" class="form-control" v-model="query" placeholder="Введите запрос" autofocus
             maxlength="255" @keyup.enter="search">
      <span class="input-group-btn"><button style="margin-right: -2px" class="btn last btn-blue-nb" type="button"
                                            :disabled="!query_valid || inLoading" @click="search">Поиск</button></span>
    </div>

    <table class="table table-bordered">
      <colgroup>
        <col width="127">
        <col>
      </colgroup>
      <tbody>
      <tr>
        <td style="max-width: 127px;" class="table-header-row">ФИО:</td>
        <td style="max-width: 99%;" class="table-content-row">
          {{selected_individual.family}}
          {{selected_individual.name}}
          {{selected_individual.patronymic}}
        </td>
      </tr>
      <tr>
        <td style="max-width: 127px;" class="table-header-row">Пол:</td>
        <td style="max-width: 99%;" class="table-content-row">{{selected_individual.sex}}</td>
      </tr>
      <tr>
        <td class="table-header-row">Дата рождения:</td>
        <td class="table-content-row">{{selected_individual.birthday}}</td>
      </tr>
      <tr>
        <td class="table-header-row">Возраст:</td>
        <td class="table-content-row">{{selected_individual.age}}</td>
      </tr>
      </tbody>
    </table>
    <slot name="for_card" v-if="loaded" style="margin-top: 5px">
      <div class="text-right">
      <a :href="directions_url" class="fli" v-if="return_base && return_card">Вернуться в направления</a>
      </div>
    </slot>
    <slot name="for_all" style="margin-top: 5px"/>
    <modal ref="modal" v-show="showModal" @close="hide_modal" show-footer="true">
      <span slot="header">Найдено несколько пациентов</span>
      <div slot="body">
        <table class="table table-responsive table-bordered table-hover"
               style="background-color: #fff;max-width: 650px">
          <colgroup>
            <col>
            <col width="40">
            <col width="140">
            <col width="120">
          </colgroup>
          <thead>
          <tr>
            <th>ФИО</th>
            <th class="text-center">Пол</th>
            <th class="text-center">Дата рождения</th>
            <th>Возраст</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="(row, i) in founded_individuals" :key="row.pk" class="cursor-pointer" @click="select_individual(i)">
            <td>{{row.family}} {{row.name}} {{row.patronymic}}</td>
            <td class="text-center">{{row.sex}}</td>
            <td class="text-center">{{row.birthday}}</td>
            <td>{{row.age}}</td>
          </tr>
          </tbody>
        </table>
      </div>
      <div slot="footer" class="text-center">
        <small>Показано не более 25-и записей</small>
      </div>
    </modal>
  </div>
</template>

<script>
import Modal from './Modal.vue';
import * as actions from '../store/action-types';
import patientsPoint from '../api/patients-point';

export default {
  name: 'individual-picker',
  components: { Modal },
  props: {
    directive_from_need: {
      default: 'false',
      type: String,
    },
    search_results: {
      default: 'false',
      type: String,
    },
    history_n: {
      default: 'true',
      type: String,
    },
    value: {},
  },
  data() {
    return {
      query: '',
      search_type: 'auto',
      showModal: false,
      founded_individuals: [],
      selected_individual: {},
      loaded: false,
      search_after_loading: false,
      return_base: null,
      return_card: null,
    };
  },
  created() {
    const params = new URLSearchParams(window.location.search);
    const individual_pk = params.get('individual_pk');
    const base_pk = params.get('base_pk');
    const card_pk = params.get('card_pk');
    if (individual_pk) {
      window.history.pushState('', '', window.location.href.split('?')[0]);
      this.query = `individual_pk:${individual_pk}`;
      this.search_after_loading = true;
      if (base_pk && card_pk) {
        this.return_base = base_pk;
        this.return_card = card_pk;
      }
    }

    this.$root.$on('search', () => {
      this.search();
    });
  },
  watch: {
    inLoading() {
      if (!this.inLoading && this.search_after_loading) {
        this.search();
      }
    },
  },
  computed: {
    directions_url() {
      return `/mainmenu/directions?base_pk=${this.return_base}&card_pk=${this.return_card}`;
    },
    normalized_query() {
      return this.query.trim();
    },
    query_valid() {
      return this.normalized_query.length > 1;
    },
    inLoading() {
      return this.$store.getters.inLoading;
    },
  },
  methods: {
    hide_modal() {
      this.showModal = false;
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
    },
    select_individual(index) {
      this.hide_modal();
      this.selected_individual = this.founded_individuals[index];
      this.emit_input();
      this.loaded = true;
    },
    emit_input() {
      let pk = -1;
      if ('pk' in this.selected_individual) pk = this.selected_individual.pk;
      this.$emit('input', pk);
    },
    clear() {
      this.loaded = false;
      this.selected_individual = {};
      this.founded_individuals = [];
      if (this.query.includes('individual_pk:')) {
        this.query = '';
      }
      this.emit_input();
    },
    search() {
      this.search_after_loading = false;
      if (!this.query_valid || this.inLoading) return;
      window.$('input').each(function () {
        window.$(this).trigger('blur');
      });
      if (!this.query.includes('individual_pk:')) {
        this.return_base = null;
        this.return_card = null;
      }
      this.$store.dispatch(actions.ENABLE_LOADING, { loadingLabel: 'Поиск пациента' });
      patientsPoint.searchIndividual(this, 'query').then((result) => {
        this.clear();
        if (result.results) {
          this.founded_individuals = result.results;
          if (this.founded_individuals.length > 1) {
            this.$refs.modal.$el.style.display = 'flex';
            this.showModal = true;
          } else if (this.founded_individuals.length === 1) {
            this.select_individual(0);
          } else {
            window.errmessage('Не найдено', 'Пациентов по такому запросу не найдено');
          }
        } else {
          window.errmessage('Ошибка на сервере');
        }
      }).catch((error) => {
        window.errmessage('Ошибка на сервере', error.message);
      }).finally(() => {
        this.$store.dispatch(actions.DISABLE_LOADING);
      });
    },
  },
};
</script>

<style scoped lang="scss">
  table {
    table-layout: fixed;
    padding: 0;
    margin: 5px 0 0;
  }

  td:not(.select-td) {
    padding: 2px !important;
  }

  .table-header-row {
    font-weight: bolder;
    overflow: hidden;
    text-overflow: ellipsis;
    vertical-align: middle;
  }

  .table-content-row {
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .cursor-pointer {
    cursor: pointer;
  }
</style>

<style lang="scss">
  .select-td {
    padding: 0 !important;

    .bootstrap-select {
      height: 38px;
      display: flex !important;
      button {
        border: none !important;
        border-radius: 0 !important;
        .filter-option {
          text-overflow: ellipsis;
        }
      }
    }
  }

  .fli {
    text-decoration: underline;
    margin-left: 5px;
  }

  .fli:hover {
    text-decoration: none;
  }
</style>
