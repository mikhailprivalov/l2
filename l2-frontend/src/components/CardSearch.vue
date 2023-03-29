<template>
  <div
    class="input-group"
    style="margin-right: -1px;"
  >
    <div class="input-group-btn">
      <button
        class="btn btn-blue-nb btn-ell dropdown-toggle nbr"
        type="button"
        data-toggle="dropdown"
        style="width: 115px;text-align: left!important;font-size: 12px;height: 34px;padding-right: 1px;"
        :title="selected_base.title"
      >
        {{ selected_base.title }}
      </button>
      <ul class="dropdown-menu">
        <li
          v-for="row in basesFiltered"
          :key="row.pk"
          :value="row.pk"
        >
          <a
            href="#"
            @click.prevent="select_base(row.pk)"
          >{{ row.title }}</a>
        </li>
      </ul>
    </div>
    <input
      ref="q"
      v-model="query"
      type="text"
      class="form-control bob"
      placeholder="Поиск пациента"
      maxlength="255"
      @keyup.enter="search"
    >
    <span class="input-group-btn">
      <button
        class="btn last btn-blue-nb nbr"
        type="button"
        :disabled="!query_valid || inLoading"
        @click="search"
      >
        <i class="fa fa-search" />
      </button>
    </span>
    <Modal
      v-show="showModal"
      ref="modal"
      show-footer="true"
      @close="hide_modal"
    >
      <span slot="header">Найдено несколько карт</span>
      <div slot="body">
        <table
          class="table table-responsive table-bordered table-hover"
          style="background-color: #fff;max-width: 680px"
        >
          <colgroup>
            <col width="95">
            <col width="155">
            <col>
            <col width="140">
          </colgroup>
          <thead>
            <tr>
              <th>Категория</th>
              <th>Карта</th>
              <th>ФИО, пол</th>
              <th>Дата рождения</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, i) in founded_cards"
              :key="row.num"
              class="cursor-pointer"
              @click="select_card(i)"
            >
              <td class="text-center">
                {{ row.type_title }}
              </td>
              <td>{{ row.num }}</td>
              <td>{{ row.family }} {{ row.name }} {{ row.twoname }}, {{ row.sex }}</td>
              <td class="text-center">
                {{ row.birthday }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div
        slot="footer"
        class="text-center"
      >
        <small>Показано не более 10 карт</small>
      </div>
    </Modal>
  </div>
</template>

<script lang="ts">
import Modal from '@/ui-cards/Modal.vue';
import * as actions from '@/store/action-types';
import patientsPoint from '@/api/patients-point';

export default {
  name: 'CardSearch',
  components: { Modal },
  props: {
    value: {},
  },
  data() {
    return {
      base: -1,
      query: '',
      founded_cards: [],
      selected_card: {},
      showModal: false,
      loaded: false,
    };
  },
  computed: {
    bases() {
      return this.$store.getters.bases;
    },
    basesFiltered() {
      return this.$store.getters.bases.filter(row => !row.hide && row.pk !== this.selected_base.pk);
    },
    selected_base() {
      for (const b of this.bases) {
        if (b.pk === this.base) {
          return b;
        }
      }
      return {
        title: 'Не выбрана база', pk: -1, hide: false, history_number: false, fin_sources: [],
      };
    },
    normalized_query() {
      return this.query.trim();
    },
    query_valid() {
      return this.normalized_query.length > 0;
    },
    inLoading() {
      return this.$store.getters.inLoading;
    },
  },
  watch: {
    bases() {
      this.check_base();
    },
  },
  created() {
    this.check_base();

    this.$store.watch((state) => state.bases, () => {
      this.check_base();
    });

    this.$root.$on('search', () => {
      this.search();
    });
  },
  methods: {
    hide_modal() {
      this.showModal = false;
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
    },
    select_base(pk) {
      this.base = pk;
      this.emit_input();
      this.search();
    },
    select_card(index) {
      this.hide_modal();
      this.selected_card = this.founded_cards[index];
      this.emit_input();
      this.loaded = true;
      this.$root.$emit('patient-picker:select_card');
    },
    clear() {
      this.loaded = false;
      this.selected_card = {};
      this.history_num = '';
      this.founded_cards = [];
      if (this.query.includes('card_pk:')) {
        this.query = '';
      }
      this.emit_input();
    },
    emit_input() {
      let pk = -1;
      if ('pk' in this.selected_card) {
        pk = this.selected_card.pk;
      }
      if (pk === -1) {
        this.$emit('input', {
          pk: -1,
          num: '',
          base: '',
          base_pk: -1,
          is_rmis: false,
          fio: '',
          sex: '',
          bd: '',
          age: '',
        });
        return;
      }
      this.$emit('input', {
        pk,
        num: this.selected_card.num,
        base: this.selected_base.title,
        base_pk: this.selected_base.pk,
        is_rmis: this.selected_card.is_rmis,
        fio: [this.selected_card.family, this.selected_card.name, this.selected_card.twoname].join(' ').trim(),
        sex: this.selected_card.sex,
        bd: this.selected_card.birthday,
        age: this.selected_card.age,
      });
    },
    check_base() {
      if (this.base === -1 && this.bases.length > 0) {
        const params = new URLSearchParams(window.location.search);
        const rmisUid = params.get('rmis_uid');
        const basePk = params.get('base_pk');
        const cardPk = params.get('card_pk');
        const ofname = params.get('ofname');
        const ofnameDep = params.get('ofname_dep');
        const q = params.get('q');

        if (rmisUid) {
          window.history.pushState('', '', window.location.href.split('?')[0]);
          for (const row of this.bases) {
            if (row.code === 'Р') {
              this.base = row.pk;
              this.query = rmisUid;
              this.search_after_loading = true;
              break;
            }
          }
          if (this.base === -1) {
            this.base = this.bases[0].pk;
          }
        } else if (basePk) {
          window.history.pushState('', '', window.location.href.split('?')[0]);
          if (ofname) {
            this.ofname_to_set = ofname;
          }
          if (ofnameDep) {
            this.ofname_to_set_dep = ofnameDep;
          }
          for (const row of this.bases) {
            if (row.pk === parseInt(basePk, 10)) {
              this.base = row.pk;
              break;
            }
          }
          if (this.base === -1) {
            this.base = this.bases[0].pk;
          }
          if (cardPk) {
            this.query = `card_pk:${cardPk}`;
            this.search_after_loading = true;
          }
        } else if (q) {
          window.history.pushState('', '', window.location.href.split('?')[0]);

          for (const b of this.bases) {
            if (b.internal_type) {
              this.base = b.pk;
              break;
            }
          }

          if (this.base === -1) {
            this.base = this.bases[0].pk;
          }
          this.query = q;
          this.search_after_loading = true;
        } else {
          this.base = this.bases[0].pk;
        }
        window.$(this.$refs.q).focus();
        this.emit_input();
      }
    },
    search() {
      this.search_after_loading = false;
      if (!this.query_valid || this.inLoading) return;
      this.check_base();
      window.$('input').each(function () {
        window.$(this).trigger('blur');
      });
      this.clear();
      this.$store.dispatch(actions.ENABLE_LOADING, { loadingLabel: 'Поиск карты' });
      patientsPoint.searchCard(this.base, this.query, true).then((result) => {
        if (result.results) {
          this.founded_cards = result.results;
          if (this.founded_cards.length > 1) {
            this.$refs.modal.$el.style.display = 'flex';
            this.showModal = true;
          } else if (this.founded_cards.length === 1) {
            this.select_card(0);
          } else {
            this.$root.$emit('msg', 'error', 'Не найдено\nКарт по такому запросу не найдено');
          }
        } else {
          this.$root.$emit('msg', 'error', 'Ошибка на сервере');
        }
      }).catch((error) => {
        this.$root.$emit('msg', 'error', `Ошибка на сервере\n${error.message}`);
      }).finally(() => {
        this.$store.dispatch(actions.DISABLE_LOADING);
      });
    },
  },
};
</script>

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

  .bob {
    border-left: none !important;
    border-top: none !important;
    border-right: none !important;
  }
</style>
