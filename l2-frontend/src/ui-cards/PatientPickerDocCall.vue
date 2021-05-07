<template>
  <div>
    <div class="input-group" style="width: 100%;">
      <template v-if="!selected_card.pk || selected_card.pk === -1">
        <div class="autocomplete">
          <input type="text" class="form-control bob" v-model="query" placeholder="Поиск по пациенту" ref="q"
                 maxlength="255" @keyup.enter="search" @keypress="keypress" @keydown="keypress_arrow"
                 @click="click_input" @blur="blur"
                 @keyup.esc="suggests.open = false"
                 :disabled="disabled"
                 @focus="suggests_focus">
          <div class="suggestions" v-if="(suggests.open && normalized_query.length > 0) || suggests.loading">
            <div class="item" v-if="suggests.loading && suggests.data.length === 0">поиск...</div>
            <div class="item" v-else-if="suggests.data.length === 0">не найдено карт в L2</div>
            <template v-else>
              <div class="item item-selectable" :class="{'item-selectable-focused': i === suggests.focused}"
                   v-for="(row, i) in suggests.data"
                   :key="row.pk"
                   @mouseover="suggests.focused = i"
                   @click.stop="select_suggest(i)">
                {{ row.family }} {{ row.name }} {{ row.twoname }}, {{ row.sex }}, {{ row.birthday }} ({{ row.age }})
                <div>
                  <span class="b" style="display: inline-block;margin-right: 4px;">
                    {{ row.type_title }} {{ row.num }}
                  </span>
                  <span class="item-doc" v-for="d in row.docs" :key="d.pk">
                    {{ d.type_title }}: {{ d.serial }} {{ d.number }};
                  </span>
                </div>
              </div>
            </template>
          </div>
        </div>
      </template>
      <template v-else>
        <span class="input-group-btn bcl">
          <button class="btn last btn-blue-nb nbr" type="button"
                  v-tippy="{ placement : 'bottom'}"
                  title="Очистить" @click="clear_selected_card">
            X
          </button>
        </span>
        <span class="input-group-addon" style="width: 100%;">
          {{ selected_card.family }} {{ selected_card.name }} {{ selected_card.twoname }},
          {{ selected_card.birthday }}, {{ selected_card.age }}, {{ selected_card.sex }}
        </span>
      </template>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex';
import { debounce } from 'lodash';
import * as actions from '../store/action-types';
import patientsPoint from '../api/patients-point';

const tfoms_re = /^([А-яЁё-]+) ([А-яЁё-]+)( ([А-яЁё-]+))? (([0-9]{2})\.?([0-9]{2})\.?([0-9]{4}))$/;

export default {
  name: 'PatientPickerDocCall',
  props: {
    value: {},
    disabled: {},
  },
  data() {
    return {
      base: -1,
      query: '',
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
      open_edit_after_loading: false,
      editor_pk: -2,
      inc_rmis: false,
      inc_tfoms: false,
      anamnesis: false,
      anamnesis_data: {},
      an_state: {
        tab: 'text',
      },
      suggests: {
        focused: -1,
        open: false,
        loading: false,
        data: [],
      },
    };
  },
  created() {
    this.$store.watch((state) => state.bases, () => {
      this.check_base();
    });
    this.$root.$on('search', () => {
      this.search();
    });
    this.$root.$on('search-value', (value) => {
      this.query = value;
      this.search();
    });
    this.$root.$on('select_card', (data) => {
      this.base = data.base_pk;
      this.query = `card_pk:${data.card_pk}`;
      this.search_after_loading = true;
      this.emit_input();
      if (!data.hide) {
        this.editor_pk = data.card_pk;
      } else {
        this.editor_pk = -2;
      }
      setTimeout(() => {
        this.search();
        if (!data.hide) {
          setTimeout(() => {
            this.$root.$emit('reload_editor');
          }, 5);
        }
      }, 5);
    });
    this.inited();
  },
  watch: {
    normalized_query() {
      this.keypress_other({ keyCode: -1 });
    },
    bases() {
      this.check_base();
    },
    inLoading() {
      if (!this.inLoading && (this.directive_department === '-1' || this.directive_doc === '-1')) {
        this.update_ofname();
      }
      if (!this.inLoading && this.search_after_loading) {
        this.search();
      }
    },
  },
  computed: {
    bases() {
      return this.$store.getters.bases.filter((b) => !b.hide);
    },
    selected_base() {
      for (const b of this.bases) {
        if (b.pk === this.base) {
          return b;
        }
      }
      return {
        title: 'Не выбрана база',
        pk: -1,
        hide: false,
        history_number: false,
        fin_sources: [],
        internal_type: false,
      };
    },
    normalized_query() {
      return this.fixedQuery.trim();
    },
    tfoms_query() {
      return this.selected_base.internal_type && this.l2_tfoms && this.normalized_query.match(tfoms_re);
    },
    query_valid() {
      return this.normalized_query.length > 0;
    },
    l2_cards() {
      return this.$store.getters.modules.l2_cards_module;
    },
    tfoms_as_l2() {
      return Boolean(this.$store.getters.modules.l2_tfoms_as_l2);
    },
    is_l2_cards() {
      if ('groups' in this.$store.getters.user_data) {
        for (const g of this.$store.getters.user_data.groups) {
          if (g === 'Картотека L2' || g === 'Admin' || g === 'Лечащий врач' || g === 'Оператор лечащего врача') {
            return true;
          }
        }
      }
      return false;
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
    ...mapGetters(['user_data']),
    fixedQuery() {
      return this.query.split(' ')
        .map((s) => s.split('-').map((x) => x.charAt(0).toUpperCase() + x.substring(1).toLowerCase()).join('-'))
        .join(' ');
    },
  },
  model: {
    event: 'modified',
  },
  methods: {
    fixQuery() {
      this.query = this.fixedQuery;
    },
    keypress(e) {
      if (!this.keypress_arrow(e)) {
        this.keypress_other(e);
      }
    },
    keypress_arrow(e) {
      if (e.keyCode === 38) {
        this.move_focus(-1);
        e.preventDefault();
        e.stopPropagation();
        e.cancelBubble = true;
        return true;
      } if (e.keyCode === 40) {
        this.move_focus(1);
        e.preventDefault();
        e.stopPropagation();
        e.cancelBubble = true;
        return true;
      }
      return false;
    },
    keypress_other: debounce(function (e) {
      if (e.keyCode !== 27 && e.keyCode !== 13) {
        this.loadSuggests();
      }
    }, 200),
    blur() {
      this.fixQuery();
      setTimeout(() => {
        this.suggests.open = false;
      }, 200);
    },
    suggests_focus() {
      if (this.normalized_query.length === 0) {
        return;
      }
      this.suggests.focused = -1;
      this.suggests.open = true;
      if (this.selected_card.pk) {
        this.$refs.q.setSelectionRange(0, this.query.length);
      }
    },
    move_focus(d) {
      this.suggests.focused += d;
      if (this.suggests.focused < -1) {
        this.suggests.focused = this.suggests.data.length - 1;
      } else if (this.suggests.focused > this.suggests.data.length - 1) {
        this.suggests.focused = -1;
      }
    },
    async loadSuggests() {
      if (this.normalized_query.length === 0) {
        this.suggests.open = false;
        this.suggests.loading = false;
        this.suggests.data = [];
        return;
      }
      this.suggests.loading = true;
      this.suggests.open = true;

      this.suggests.data = (await patientsPoint.searchCard({
        type: this.base,
        query: this.normalized_query,
        list_all_cards: false,
        inc_rmis: false,
        inc_tfoms: false,
        suggests: true,
        always_phone_search: true,
      })).results;

      if (this.suggests.data.length === 0) {
        this.suggests.focused = -1;
      }

      this.move_focus(0);

      this.suggests.loading = false;
    },
    select_suggest(i) {
      this.founded_cards = this.suggests.data;
      window.$('input').each(function () {
        window.$(this).trigger('blur');
      });
      this.select_card(i);
    },
    clear_input() {
      this.query = '';
    },
    clear_selected_card() {
      this.clear();
    },
    click_input() {
      this.loadSuggests();
    },
    async inited() {
      await this.$store.dispatch(actions.INC_LOADING);
      await this.$store.dispatch(actions.GET_DIRECTIVE_FROM);
      await this.$store.dispatch(actions.DEC_LOADING);

      setTimeout(() => {
        this.local_directive_departments = this.$store.getters.directive_from;
        this.directive_departments_select = [];
        for (const dep of this.local_directive_departments) {
          this.directive_departments_select.push({ label: dep.title, value: dep.pk });
        }

        if (this.$store.getters.user_data
          && this.$store.getters.user_data.department
          && this.local_directive_departments.length > 0 && this.ofname_to_set === '-1') {
          for (const dep of this.local_directive_departments) {
            if (dep.pk === this.$store.getters.user_data.department.pk) {
              this.directive_department = `${dep.pk}`;
              this.check_base();
              return;
            }
          }
          this.directive_department = this.local_directive_departments[0].pk.toString();
        }

        this.check_base();
      }, 10);
    },
    an_tab(tab) {
      this.an_state.tab = tab;
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
    update_ofname(force) {
      if (this.ofname_to_set === '-2' || (this.inLoading && !force)) return;
      if (this.ofname_to_set !== '-1') {
        if (this.ofname_to_set_dep !== '-1') {
          this.directive_department = this.ofname_to_set_dep;
          this.directive_doc = this.ofname_to_set;
          this.$root.$emit('resync');
          this.emit_input();
          this.ofname_to_set = '-2';
          return;
        }
        const dps = Object.keys(this.directive_from_departments);
        if (dps.length > 0 && !this.inLoading) {
          const onts = this.ofname_to_set;
          this.ofname_to_set = '-1';
          for (const d of dps) {
            const users = this.directive_from_departments[d].docs;
            for (const u of users) {
              if (u.pk.toString() === onts.toString()) {
                this.directive_department = d.toString();
                this.directive_doc = onts;
                this.emit_input();
                this.ofname_to_set = '-2';
                return;
              }
            }
          }
        }
        return;
      }
      let dpk = -1;
      if (this.directive_department !== '-1') {
        for (const d of this.directive_docs_select) {
          if (d.value === this.$store.getters.user_data.doc_pk) {
            dpk = d.value;
            break;
          }
        }
        if (dpk === -1 && this.directive_docs_select.length > 0) {
          dpk = this.directive_docs_select[0].value;
        }
      }
      this.directive_doc = dpk.toString();
    },
    select_base(pk) {
      this.base = pk;
      this.emit_input();
      this.search();
    },
    select_card(index) {
      this.hide_modal();
      this.suggests.open = false;
      this.suggests.loading = false;
      this.suggests.data = [];
      this.selected_card = this.founded_cards[index];
      if (this.selected_card.base_pk) {
        if (this.base && this.base !== this.selected_card.base_pk) {
          this.query = '';
        }
        this.base = this.selected_card.base_pk;
      }
      setTimeout(() => {
        if (this.selected_card.status_disp === 'need' && this.$refs.disp) {
          window.$(this.$refs.disp).click();
        }
      }, 10);
      this.emit_input();
      this.query = '';
      this.loaded = true;
      this.$root.$emit('patient-picker:select_card');
    },
    check_base() {
      if (this.base === -1 && this.bases.length > 0) {
        const params = new URLSearchParams(window.location.search);
        const rmis_uid = params.get('rmis_uid');
        const base_pk = params.get('base_pk');
        const card_pk = params.get('card_pk');
        const open_edit = params.get('open_edit') === 'true';
        const ofname = params.get('ofname');
        const ofname_dep = params.get('ofname_dep');
        if (rmis_uid) {
          window.history.pushState('', '', window.location.href.split('?')[0]);
          let has_internal = false;
          for (const row of this.bases) {
            if (row.internal_type) {
              this.base = row.pk;
              this.query = rmis_uid;
              this.search_after_loading = true;
              has_internal = true;
              break;
            }
          }
          if (!has_internal) {
            for (const row of this.bases) {
              if (row.code === 'Р') {
                this.base = row.pk;
                this.query = rmis_uid;
                this.search_after_loading = true;
                break;
              }
            }
          }
          if (this.base === -1) {
            this.base = this.bases[0].pk;
          }
        } else if (base_pk) {
          window.history.pushState('', '', window.location.href.split('?')[0]);
          if (ofname) {
            this.ofname_to_set = ofname;
          }
          if (ofname_dep) {
            this.ofname_to_set_dep = ofname_dep;
          }
          for (const row of this.bases) {
            if (row.pk === parseInt(base_pk, 10)) {
              this.base = row.pk;
              break;
            }
          }
          if (this.base === -1) {
            this.base = this.bases[0].pk;
          }
          if (card_pk) {
            this.query = `card_pk:${card_pk}`;
            this.search_after_loading = true;
            this.open_edit_after_loading = open_edit;
          }
        } else {
          this.base = this.bases[0].pk;
        }
        this.emit_input();
      }
    },
    emit_input() {
      this.$emit('modified', this.selected_card.pk || -1);
    },
    clear() {
      this.loaded = false;
      this.selected_card = {};
      this.history_num = '';
      this.founded_cards = [];
      this.query = '';
      this.emit_input();
    },
    open_as_l2_card() {
      this.$store.dispatch(actions.ENABLE_LOADING, { loadingLabel: 'Загрузка' });
      patientsPoint.searchL2Card({ card_pk: this.selected_card.pk }).then((result) => {
        this.clear();
        if (result.results) {
          this.founded_cards = result.results;
          if (this.founded_cards.length > 1) {
            this.showModal = true;
          } else if (this.founded_cards.length === 1) {
            this.select_card(0);
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
    search() {
      if (!this.query_valid || this.inLoading) return;
      this.suggests.open = false;
      this.suggests.loading = false;
      if (this.suggests.focused > -1 && this.suggests.data.length > 0) {
        this.select_suggest(this.suggests.focused);
        return;
      }
      this.suggests.data = [];
      const q = this.query;
      this.check_base();
      window.$('input').each(function () {
        window.$(this).trigger('blur');
      });
      this.$store.dispatch(actions.ENABLE_LOADING, { loadingLabel: 'Поиск карты' });
      patientsPoint.searchCard({
        type: this.base,
        query: q,
        list_all_cards: false,
        inc_rmis: this.inc_rmis || this.search_after_loading,
        inc_tfoms: this.inc_tfoms && this.tfoms_query,
        always_phone_search: true,
      }).then((result) => {
        this.clear();
        if (result.results) {
          this.founded_cards = result.results;
          if (this.founded_cards.length > 1) {
            this.showModal = true;
          } else if (this.founded_cards.length === 1) {
            this.select_card(0);
            if (this.open_edit_after_loading) {
              this.open_editor();
            }
          } else {
            window.errmessage('Не найдено', 'Карт по такому запросу не найдено');
          }
        } else {
          window.errmessage('Ошибка на сервере');
        }
        if (this.search_after_loading) {
          this.search_after_loading = false;
          this.query = '';
        }
      }).catch((error) => {
        window.errmessage('Ошибка на сервере', error.message);
      }).finally(() => {
        this.open_edit_after_loading = false;
        this.$store.dispatch(actions.DISABLE_LOADING);
      });
    },
    add_researches(pks, full = false) {
      for (const pk of pks) {
        this.$root.$emit('researches-picker:add_research', pk);
      }
      if (full) {
        if (this.$refs.disp) {
          window.$(this.$refs.disp).click();
          window.$(this.$refs.disp).blur();
        }
      }
    },
    show_results(pk) {
      this.$root.$emit('print:results', pk);
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
  bottom: 34px;
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

.dropdown-menu {
  max-width: 350px;
  min-width: 1%;
}

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

.bob {
  border-radius: 5px !important;
}

.bcl {
  margin: 0 !important;

  button {
    border-top-left-radius: 5px !important;
    border-bottom-left-radius: 5px !important;
  }
}

.internal_type {
  width: 100%;
  display: flex;
  flex-wrap: nowrap;
  flex-direction: row;
  justify-content: stretch;

  .btn {
    align-self: stretch;
    flex: 1;
    padding: 6px 0;
  }
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

.hospital input {
  border-radius: 0;
}

.disp {
  a:not(.btn):not(.not-black) {
    color: #0d0d0d !important;
    text-decoration: dotted underline;

    &:hover {
      text-decoration: none;
    }
  }

  &_need, &_need:focus, &_need:active, &_need:hover {
    background: #F4D03F !important;
  }

  &_finished, &_finished:focus, &_finished:active, &_finished:hover {
    background: #049372 !important;
  }

  .btn {
    width: 100%;
    padding: 4px;
  }
}

.disp_row {
  font-weight: bold;
  display: inline-block;
  width: 76px;

  &_need, &_need a {
    color: #ff0000 !important;
  }

  &_finished, &_finished a {
    color: #049372 !important;
  }

  a {
    text-decoration: dotted underline;

    &:hover {
      text-decoration: none;
    }
  }
}

.base-toggle {
  max-width: 200px;
  min-width: 60px;
  text-align: left !important;
}

.autocomplete {
  position: relative;
  overflow: visible;
  height: 34px;

  input {
    border-radius: 0;
  }

  .suggestions {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: #fff;
    border-radius: 0 0 5px 5px;
    border: 1px solid #3bafda;
    border-top: none;
    box-shadow: 0 10px 20px rgba(#3bafda, 0.19), 0 6px 6px rgba(#3bafda, 0.23);
    overflow: hidden;
    z-index: 1000;

    .item {
      padding: 3px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      word-break: keep-all;

      &-doc {
        color: #888;
        font-size: 85%;
      }

      &-selectable {
        cursor: pointer;

        &-focused {
          background: rgba(#3bafda, .1);
        }
      }
    }
  }

  .clear-input {
    display: none;
    position: absolute;
    cursor: pointer;
    top: 0;
    right: 0;
    width: 34px;
    height: 34px;
    opacity: .6;

    &:hover {
      background: rgba(0, 0, 0, .15);
      opacity: 1;
    }

    &.display {
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 10;
    }
  }
}
</style>
