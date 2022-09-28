<template>
  <div v-frag>
    <ul class="nav navbar-nav">
      <li>
        <a
          href="#"
          @click.prevent="open"
        > Расширенный поиск пациента </a>

        <transition name="fade">
          <modal
            v-if="opened"
            show-footer="true"
            white-bg="true"
            max-width="710px"
            width="100%"
            margin-left-right="auto"
            class="an"
            @close="close"
          >
            <span slot="header">Расширенный поиск пациента</span>
            <div
              slot="body"
              class="an-body search-body"
            >
              <div class="d-root">
                <form
                  autocomplete="off"
                  @submit.prevent="search"
                >
                  <PatientSearchForm v-model="form" />
                  <div class="row mt15">
                    <div
                      class="col-xs-5"
                      style="padding-right: 10px"
                    >
                      <div class="input-group">
                        <SelectFieldTitled
                          v-model="base"
                          :variants="basesFiltered"
                        />
                        <span class="input-group-btn">
                          <button
                            class="btn btn-primary-nb btn-blue-nb search-btn"
                            type="submit"
                            :disabled="!isValidForm"
                          >
                            {{ loading ? 'Загрузка' : 'Поиск' }}
                          </button>
                        </span>
                      </div>
                    </div>
                    <div
                      class="col-xs-2"
                      style="padding-left: 0"
                    >
                      <button
                        v-if="formFromSaved"
                        v-tippy
                        class="btn btn-blue-nb"
                        type="button"
                        :disabled="loading"
                        title="Вернуться к предыдущему поиску"
                        @click="restoreForm"
                      >
                        <i class="fas fa-history" />
                      </button>
                    </div>
                    <div class="col-xs-5 text-right">
                      <button
                        v-tippy
                        class="btn btn-blue-nb"
                        type="button"
                        :disabled="loading"
                        title="Очистить форму"
                        @click="clearForm"
                      >
                        <i class="fas fa-times" />
                      </button>
                    </div>
                  </div>
                </form>

                <div
                  v-if="searched && results.length === 0"
                  class="empty-results"
                >
                  НИЧЕГО НЕ НАЙДЕНО
                </div>
                <div
                  v-else-if="searched"
                  class="results"
                >
                  <div
                    v-for="(row, i) in results"
                    :key="row.pk"
                    class="founded"
                    @click="select_card(i)"
                  >
                    <div
                      v-if="row.isArchive"
                      class="founded-row is-archive"
                    >
                      Карта в архиве
                    </div>
                    <div class="founded-row">
                      Карта <span class="b">{{ row.type_title }} {{ row.num }}</span>
                    </div>
                    <div class="founded-row">
                      <span class="b">ФИО, пол:</span> {{ row.family }} {{ row.name }} {{ row.twoname }}, {{ row.sex }}
                    </div>
                    <div class="founded-row">
                      <span class="b">Дата рождения:</span> {{ row.birthday }} ({{ row.age }})
                    </div>
                    <div
                      v-for="d in row.docs"
                      :key="d.pk"
                      class="founded-row"
                    >
                      <span class="b">{{ d.type_title }}:</span> {{ d.serial }} {{ d.number }}
                    </div>
                    <div
                      v-for="(p, j) in row.phones"
                      :key="`phone-${j}-${p}`"
                      class="founded-row"
                    >
                      <span class="b">Телефон:</span> {{ p }}
                    </div>
                  </div>
                  <div class="results-msg">
                    <small>Показано не более 20 карт</small>
                  </div>
                </div>
              </div>
            </div>
            <div slot="footer">
              <div class="row">
                <div class="col-xs-6">
                  <button
                    class="btn btn-blue-nb"
                    type="button"
                    :disabled="loading"
                    @click="close"
                  >
                    Закрыть
                  </button>
                </div>
              </div>
            </div>
          </modal>
        </transition>
      </li>
    </ul>
  </div>
</template>

<script lang="ts">
import _ from 'lodash';
import Vue from 'vue';
import { mapGetters } from 'vuex';
import Component from 'vue-class-component';

import Modal from '@/ui-cards/Modal.vue';
import PatientSearchForm from '@/ui-cards/ExtendedPatientSearch/PatientSearchForm.vue';
import { PatientForm } from '@/ui-cards/ExtendedPatientSearch/types';
import patientsPoint from '@/api/patients-point';
import { Base } from '@/types/cards';
import SelectFieldTitled from '@/fields/SelectFieldTitled.vue';
import { SimplePatient } from '@/types/patient';

@Component({
  components: { SelectFieldTitled, PatientSearchForm, Modal },
  data() {
    return {
      opened: false,
      loading: false,
      base: -1,
      form: null,
      formFromSaved: null,
      baseFromSaved: null,
      baseGlobal: null,
      searched: false,
      results: [],
    };
  },
  computed: {
    isValidForm() {
      if (!this.form) {
        return false;
      }

      return Object.keys(this.form).some((k) => typeof this.form[k] !== 'boolean' && Boolean(this.form[k]));
    },
    ...mapGetters(['bases', 'user_data']),
    formSavedKey() {
      const { username } = this.user_data || {};
      if (username) {
        return `extended-search:last-form:${username}`;
      }
      return null;
    },
    baseSavedKey() {
      const { username } = this.user_data || {};
      if (username) {
        return `extended-search:last-base:${username}`;
      }
      return null;
    },
    basesFiltered() {
      return this.bases.filter((b) => !b.hide);
    },
  },
  watch: {
    bases: {
      immediate: true,
      handler() {
        if (this.basesFiltered.length > 0 && !this.basesFiltered.find((b) => b.pk === this.base)) {
          this.base = this.basesFiltered[0].pk;
        }
      },
    },
  },
})
export default class ExtendedPatientSearch extends Vue {
  opened: boolean;

  loading: boolean;

  searched: boolean;

  bases: Base[];

  user_data: any;

  basesFiltered: Base[];

  base: number;

  form: PatientForm | null;

  formSavedKey: string | null;

  formFromSaved: PatientForm | null;

  baseSavedKey: string | null;

  baseFromSaved: number | null;

  baseGlobal: number | null;

  results: SimplePatient[];

  isValidForm: boolean;

  mounted() {
    this.$root.$on('global:select-base', (pk) => {
      this.baseGlobal = pk;
    });
  }

  open() {
    let baseGlobal = Number(window.localStorage.getItem('selected-base'));

    if (Number.isNaN(baseGlobal)) {
      baseGlobal = this.baseGlobal;
    }

    if (baseGlobal !== null) {
      this.base = baseGlobal;
    }
    this.results = [];
    this.searched = false;
    this.loading = false;

    const savedFormKey = this.formSavedKey;
    const savedBaseKey = this.baseSavedKey;

    try {
      if (savedFormKey && window.localStorage.getItem(savedFormKey)) {
        const data = JSON.parse(window.localStorage.getItem(savedFormKey));

        if (_.isObject(data)) {
          this.formFromSaved = data as PatientForm;
        }
      }

      if (savedBaseKey && window.localStorage.getItem(savedBaseKey)) {
        const data = JSON.parse(window.localStorage.getItem(savedBaseKey));

        if (_.isNumber(data)) {
          this.baseFromSaved = data;
        }
      }
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error(e);
    }

    this.opened = true;
  }

  close() {
    this.opened = false;
  }

  clearForm() {
    this.$root.$emit('extended-patient-search:reset-patient-form');
  }

  async search() {
    if (!this.isValidForm) {
      return;
    }
    this.loading = true;
    const { results } = await patientsPoint.searchCard({
      type: this.base,
      extendedSearch: true,
      form: this.form,
      limit: 20,
    });
    this.results = results;
    if (results.length > 0) {
      this.$root.$emit('msg', 'ok', `Найдено карт: ${results.length}`);
    } else {
      this.$root.$emit('msg', 'warning', 'Не удалось ничего найти по такому запросу');
    }
    this.loading = false;
    this.searched = true;
    this.formFromSaved = { ...this.form };

    try {
      const savedFormKey = this.formSavedKey;
      const savedBaseKey = this.baseSavedKey;

      if (savedFormKey) {
        const data = JSON.stringify(this.form);
        window.localStorage.setItem(savedFormKey, data);
      }

      if (savedBaseKey) {
        window.localStorage.setItem(savedBaseKey, JSON.stringify(this.base));
      }
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error(e);
    }
  }

  restoreForm() {
    this.form = { ...this.form, ...(this.formFromSaved || {}) };
    this.base = this.baseFromSaved === null ? this.base : this.baseFromSaved;
    this.search();
  }

  select_card(i: number) {
    const card = this.results[i];
    this.$root.$emit('select_card', {
      base_pk: card.base_pk,
      card_pk: card.pk,
      hide: true,
      inc_archive: card.isArchive,
    });
    this.close();
  }
}
</script>

<style lang="scss" scoped>
.d-root {
  height: 100%;
  flex: 1;
  padding: 10px;
  overflow: auto;
}

.mt15 {
  margin-top: 15px;
}

.search-btn {
  width: 90px !important;
}

.empty-results {
  padding: 20px;
  text-align: center;
}

.results {
  margin-top: 10px;

  &-msg {
    padding: 10px;
    text-align: center;
  }
}

.founded {
  background: #fff;
  margin-bottom: 10px;
  cursor: pointer;
  padding: 5px;
  border-radius: 5px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;

  &:hover {
    transform: scale(1.01);
    box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
    z-index: 1;
  }
}

.search-body {
  overflow-x: hidden;
}
</style>
