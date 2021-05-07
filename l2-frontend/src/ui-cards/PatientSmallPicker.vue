<template>
  <div style="height: 100%;width: 100%;position: relative">
    <div class="top-picker" :class="{internalType: selected_base.internal_type}">
      <div class="input-group">
        <div class="input-group-btn" v-if="bases.length > 1">
          <button class="btn btn-blue-nb btn-ell dropdown-toggle nbr" type="button" data-toggle="dropdown"
                  style="width: 200px;text-align: left!important;">
            <span class="caret"></span> {{selected_base.title}}
          </button>
          <ul class="dropdown-menu">
            <li v-for="row in basesFiltered" :value="row.pk" :key="row.pk">
              <a href="#" @click.prevent="select_base(row.pk)">{{row.title}}</a>
            </li>
          </ul>
        </div>
        <div class="input-group-btn" v-else>
          <button class="btn btn-blue-nb btn-ell dropdown-toggle nbr" type="button" data-toggle="dropdown"
                  style="max-width: 200px;text-align: left!important;">{{selected_base.title}}
          </button>
        </div>
        <input type="text" class="form-control bob" v-model="query" placeholder="Введите запрос" ref="q"
               maxlength="255" @keyup.enter="search">
        <span v-if="selected_base.internal_type" class="rmis-search input-group-btn">
          <label class="btn btn-blue-nb nbr" style="padding: 5px 12px;">
            <input type="checkbox" v-model="inc_rmis" /> Вкл. РМИС
          </label>
        </span>
        <span class="input-group-btn">
          <button style="margin-right: -2px"
                  class="btn last btn-blue-nb nbr" type="button" :disabled="!query_valid || inLoading" @click="search">
            Поиск
          </button>
        </span>
      </div>
    </div>
    <div class="content-picker scrolldown">
      <div style="padding-left: 5px;padding-right: 5px;">
        <table class="table table-bordered">
          <colgroup>
            <col width="124">
            <col>
            <col width="54">
            <col>
          </colgroup>
          <tbody>
          <tr>
            <td style="max-width: 124px;" class="table-header-row">ФИО:</td>
            <td style="max-width: 99%;" class="table-content-row">
              {{selected_card.family}} {{selected_card.name}} {{selected_card.twoname}}
            </td>
            <td style="max-width: 54px;" class="table-header-row">{{selected_card.is_rmis?'ID':'Карта'}}:</td>
            <td style="max-width: 99%;" class="table-content-row">{{selected_card.num}}</td>
          </tr>
          <tr>
            <td class="table-header-row">Дата рождения:</td>
            <td class="table-content-row">{{selected_card.birthday}}<span v-if="loaded"> ({{selected_card.age}})</span>
            </td>
            <td class="table-header-row">Пол:</td>
            <td class="table-content-row">{{selected_card.sex}}</td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>
    <modal ref="modal" v-if="showModal" @close="hide_modal" show-footer="true">
      <span slot="header">Найдено несколько карт</span>
      <div slot="body" style="padding: 10px">
        <div class="founded" v-for="(row, i) in founded_cards" :key="row.pk" @click="select_card(i)">
          <div class="founded-row">Карта <span class="b">{{row.type_title}} {{row.num}}</span></div>
          <div class="founded-row"><span class="b">ФИО, пол:</span> {{row.family}} {{row.name}} {{row.twoname}}, {{row.sex}}</div>
          <div class="founded-row"><span class="b">Дата рождения:</span> {{row.birthday}} ({{row.age}})</div>
          <div class="founded-row" v-for="d in row.docs" :key="d.pk">
            <span class="b">{{d.type_title}}:</span> {{d.serial}} {{d.number}}
          </div>
        </div>
      </div>
      <div slot="footer" class="text-center">
        <small>Показано не более 10 карт</small>
      </div>
    </modal>
  </div>
</template>

<script>
import Modal from './Modal.vue';
import * as actions from '../store/action-types';
import patientsPoint from '../api/patients-point';

export default {
  name: 'patient-small-picker',
  components: { Modal },
  props: {
    base_pk: {
      type: Number,
      required: true,
    },
    card: {
      type: Object,
      required: false,
    },
    value: {},
  },
  data() {
    return {
      base: -1,
      query: '',
      directive_department: '-1',
      directive_doc: '-1',
      ofname_to_set: '-1',
      ofname_to_set_dep: '-1',
      local_directive_departments: [],
      directive_departments_select: [],
      showModal: false,
      founded_cards: [],
      selected_card: {},
      loaded: false,
      history_num: '',
      search_after_loading: false,
      editor_pk: -2,
      inc_rmis: false,
      perf_val: false,
    };
  },
  created() {
    this.check_base();

    this.$store.watch((state) => state.bases, () => {
      this.check_base();
    });
  },
  watch: {
    query() {
      this.query = this.query.split(' ')
        .map((s) => s.charAt(0).toUpperCase() + s.substring(1))
        .join(' ');
    },
    bases() {
      this.check_base();
    },
    inLoading() {
      if (!this.inLoading && this.search_after_loading) {
        this.search();
      }
    },
  },
  computed: {
    bases() {
      return this.$store.getters.bases.filter((b) => b.pk === this.base_pk);
    },
    basesFiltered() {
      return this.bases.filter(row => !row.hide && row.pk !== this.selected_base.pk);
    },
    selected_base() {
      for (const b of this.bases) {
        if (b.pk === this.base) {
          return b;
        }
      }
      return {
        title: 'Не выбрана база', pk: -1, hide: false, history_number: false, fin_sources: [], internal_type: false,
      };
    },
    normalized_query() {
      return this.query.trim();
    },
    query_valid() {
      return this.normalized_query.length > 0;
    },
    l2_cards() {
      return this.$store.getters.modules.l2_cards_module;
    },
    is_operator() {
      if ('groups' in this.$store.getters.user_data) {
        for (const g of this.$store.getters.user_data.groups) {
          if (g === 'Оператор лечащего врача') {
            return true;
          }
        }
      }
      return false;
    },
    is_l2_cards() {
      if ('groups' in this.$store.getters.user_data) {
        for (const g of this.$store.getters.user_data.groups) {
          if (g === 'Картотека L2' || g === 'Admin') {
            return true;
          }
        }
      }
      return false;
    },
    directive_from_departments() {
      const r = {};
      for (const dep of this.local_directive_departments) {
        r[dep.pk] = dep;
      }
      return r;
    },
    directive_docs_select() {
      const o = [];
      if (this.directive_department in this.directive_from_departments) {
        for (const d of this.directive_from_departments[this.directive_department].docs) {
          o.push({ label: d.fio, value: d.pk });
        }
      }
      return o;
    },
    inLoading() {
      return this.$store.getters.inLoading;
    },
    phones() {
      if ('phones' in this.selected_card) {
        return this.selected_card.phones;
      }
      return [];
    },
  },
  methods: {
    open_editor(isnew) {
      if (isnew) {
        this.editor_pk = -1;
      } else {
        this.editor_pk = this.selected_card.pk;
      }
    },
    format_number(a) {
      if (a.length === 6) {
        return `${a.slice(0, 2)}-${a.slice(2, 4)}-${a.slice(4, 6)}`;
      } if (a.length === 11) {
        if (a.charAt(1) !== '9' && a.charAt(1) !== '8') {
          return `${a.slice(0, 1)}-${a.slice(1, 5)}-${a.slice(5, 7)}-${a.slice(7, 9)}-${a.slice(9, 11)}`;
        }
        return `${a.slice(0, 1)}-${a.slice(1, 4)}-${a.slice(4, 6)}-${a.slice(6, 8)}-${a.slice(8, 10)}-${a.slice(10, 11)}`;
      }
      return a;
    },
    hide_modal() {
      this.showModal = false;
      if (this.$refs.modal) this.$refs.modal.$el.style.display = 'none';
    },
    select_base(pk) {
      this.base = pk;
      this.emit_input();
      this.search();
    },
    select_card(index) {
      this.hide_modal();
      this.selected_card = this.founded_cards[index];
      if (this.selected_card.base_pk) {
        if (this.base && this.base !== this.selected_card.base_pk) {
          this.query = '';
        }
        this.base = this.selected_card.base_pk;
      }
      if (this.query.toLowerCase().includes('card_pk:')) {
        this.query = '';
      }
      this.emit_input();
      this.loaded = true;
    },
    check_base() {
      if ((this.base === -1 && this.bases.length > 0) || !this.perf_val) {
        let ns = false;
        if (!this.perf_val) {
          if (this.value) {
            this.query = `card_pk:${this.value}`;
            this.search_after_loading = true;
          }
          this.perf_val = true;
          ns = true;
        }
        if (this.base === -1) {
          this.base = this.bases[0].pk;
        }
        window.$(this.$refs.q).focus();
        this.emit_input();
        if (ns) {
          this.search();
        }
      }
    },
    emit_input() {
      let pk = null;
      if ('pk' in this.selected_card) pk = this.selected_card.pk;
      this.$emit('input', pk);
      if (this.card) {
        this.$emit('update:card', this.selected_card);
      }
    },
    clear() {
      this.loaded = false;
      this.selected_card = {};
      this.history_num = '';
      this.founded_cards = [];
      if (this.query.toLowerCase().includes('card_pk:')) {
        this.query = '';
      }
      this.emit_input();
    },
    search() {
      this.search_after_loading = false;
      if (!this.query_valid || this.inLoading) return;
      this.check_base();
      this.$store.dispatch(actions.ENABLE_LOADING, { loadingLabel: 'Поиск карты' });
      patientsPoint.searchCard(this, ['query', 'inc_rmis'], {
        type: this.base,
        list_all_cards: false,
      }).then((result) => {
        if (result.results) {
          this.founded_cards = result.results;
          if (this.founded_cards.length > 1) {
            this.showModal = true;
          } else if (this.founded_cards.length === 1) {
            this.select_card(0);
          } else {
            window.errmessage('Не найдено', 'Карт по такому запросу не найдено');
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
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    vertical-align: middle;
  }

  .table-content-row {
    overflow: hidden;
    text-overflow: ellipsis;
    vertical-align: middle;
  }

  .cursor-pointer {
    cursor: pointer;
  }

  .content-picker {
    position: absolute;
    top: 34px;
    left: 0;
    right: 0;
    bottom: 0;
    overflow-y: auto;
    overflow-x: hidden;
  }

  .top-picker, .bottom-picker {
    height: 34px;
    background-color: #AAB2BD;
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    white-space: nowrap;
  }

  .bottom-picker {
    bottom: 0;
  }

  .top-picker {
    top: 0;
  }

  .bottom-inner {
    display: flex;
    flex-wrap: wrap;
    flex-direction: row;
    justify-content: flex-end;
    align-items: stretch;
    position: absolute;
    left: 0;
    top: 0;
    right: 0;
    height: 34px;
    align-content: stretch;

    a:not(.ddm) {
      align-self: stretch;
      display: flex;
      align-items: center;
      padding: 1px 2px 1px;
      text-decoration: none;
      transition: .15s linear all;
      cursor: pointer;
      flex: 1;
      margin: 0;
      font-size: 12px;
      min-width: 0;
      max-width: 150px;
      background-color: #AAB2BD;
      color: #fff;
      text-align: right;
      justify-content: center;
      span {
        display: block;
        text-overflow: ellipsis;
        overflow: hidden;
        word-break: keep-all;
        max-height: 2.2em;
        line-height: 1.1em;
      }

      &:hover {
        background-color: #434a54;
      }
    }
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

  .hovershow {
    position: relative;

    a {
      font-size: 12px;
    }

    .hovershow1 {
      top: 1px;
      position: absolute;

      a {
        color: grey;
        display: inline-block;
      }
      color: grey;
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow: hidden;
    }
    .hovershow2 {
      opacity: 0;
    }

    &:hover {
      .hovershow1 {
        display: none;
      }
      .hovershow2 {
        opacity: 1;
        transition: .5s ease-in opacity;
      }
    }
  }

  .nbr {
    border-radius: 0;
  }

  .bob {
    border-left: none !important;
    border-top: none !important;
    border-right: none !important;
  }

  .internal_type {
    text-align: right;
  }

  .founded {
    background: #fff;
    margin-bottom: 10px;
    cursor: pointer;
    padding: 5px;
    border-radius: 5px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
    transition: all .2s cubic-bezier(.25, .8, .25, 1);
    position: relative;
    &:hover {
      transform: scale(1.03);
      box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
      z-index: 1;
    }
  }
  .b {
    font-weight: bold;
  }
</style>
