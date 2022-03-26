<template>
  <div
    ref="root"
    class="results-root"
    :class="embedded && 'embedded'"
  >
    <div
      v-if="!embedded"
      :class="{ has_loc, opened: sidebarIsOpened || !data.ok }"
      class="results-sidebar"
    >
      <div class="sidebar-top">
        <div class="input-group">
          <input
            v-model="pk"
            type="text"
            class="form-control"
            autofocus
            :placeholder="'Название участка'"
            @keyup.enter="load()"
          >
          <span class="input-group-btn">
            <button
              class="btn last btn-blue-nb nbr"
              type="button"
              style="margin-right: -1px"
              @click="load()"
            >Добавить</button>
          </span>
        </div>
      </div>
      <div
        class="directions"
        :class="{ noStat: !stat_btn_d, has_loc, stat_btn: stat_btn_d }"
      >
        <div class="inner">
          <div
            v-for="direction in directions_history"
            :key="direction.pk"
            class="direction"
          >
            <div>{{ direction.patient }}, {{ direction.card }}</div>
          </div>
          <div
            v-if="directions_history.length === 0"
            class="text-center"
            style="margin: 5px"
          >
            Нет участков
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import moment from 'moment';
import { mapGetters } from 'vuex';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import { vField, vGroup } from '@/components/visibility-triggers';
import { cleanCaches } from '@/utils';
import { enterField, leaveField } from '@/forms/utils';
import patientsPoint from '../api/patients-point';
import * as actions from '../store/action-types';
import directionsPoint from '../api/directions-point';
import researchesPoint from '../api/researches-point';
import usersPoint from '../api/user-point';
import UrlData from '../UrlData';

export default {
  name: 'ConstructDistrict',
  async beforeRouteLeave(to, from, next) {
    const msg = this.unload();

    if (msg) {
      try {
        await this.$dialog.confirm(msg);
      } catch (_) {
        next(false);
        return;
      }
    }

    next();
  },
  data() {
    return {
      pk: '',
      iss_search: false,
      data: { ok: false, direction: {} },
      date: moment().format('DD.MM.YYYY'),
      td: moment().format('YYYY-MM-DD'),
      tnd: moment().add(1, 'day').format('YYYY-MM-DD'),
      td_m_year: moment().subtract(1, 'year').format('YYYY-MM-DD'),
      directions_history: [],
      prev_scroll: 0,
      prev_scrollHeightTop: 0,
      changed: false,
      inserted: false,
      anamnesis_edit: false,
      anamnesis_data: {
        text: '',
      },
      anamnesis_loading: false,
      new_anamnesis: null,
      research_open_history: null,
      research_history: [],
      templates: {},
      benefit: false,
      benefit_rows_loading: false,
      benefit_rows: [],
      dreg: false,
      dreg_rows_loading: false,
      dreg_rows: [],
      location: {
        loading: false,
        init: false,
        data: [],
      },
      slot: {
        id: null,
        data: {},
      },
      create_directions_for: -1,
      create_directions_data: [],
      create_directions_diagnosis: '',
      show_results_pk: -1,
      loc_timer: null,
      inited: false,
      medical_certificatesicates_rows: [],
      sidebarIsOpened: false,
      hasEDSigns: false,
      statusTitles: {
        1: 'Направление зарегистрировано',
        2: 'Результат подтверждён',
      },
      embedded: false,
      embeddedFull: false,
      tableFieldsErrors: {},
      workFromUsers: [],
      workFromHistory: [],
      moreServices: [],
    };
  },
  computed: {
    requiredStattalonFields() {
      return this.$store.getters.requiredStattalonFields;
    },
    researchesPkRequiredStattalonFields() {
      return this.$store.getters.researchesPkRequiredStattalonFields;
    },
    userServicesFiltered() {
      return this.user_services.filter((s) => !this.slot.data.direction || s.pk === this.slot.data.direction_service);
    },
    date_to_form() {
      return `"${this.date}"`;
    },
    ca() {
      if (this.new_anamnesis !== null) {
        return this.new_anamnesis;
      }
      return this.data.anamnesis;
    },
    fte() {
      return this.$store.getters.modules.l2_fast_templates;
    },
    stat_btn() {
      return this.$store.getters.modules.l2_stat_btn;
    },
    stat_btn_d() {
      return this.stat_btn && this.directions_history.length;
    },
    rmis_queue() {
      return this.$store.getters.modules.l2_rmis_queue;
    },
    amd() {
      return this.$store.getters.modules.l2_amd;
    },
    l2_morfology_additional() {
      return this.$store.getters.modules.l2_morfology_additional;
    },
    show_additional() {
      if (!this.data || !this.data.ok) {
        return false;
      }
      return (
        this.l2_morfology_additional
        && (this.data.has_microbiology || this.data.has_citology || this.data.has_gistology)
        && !this.data.direction.all_confirmed
      );
    },
    additionalTypes() {
      if (!this.show_additional) {
        return [];
      }
      if (this.data.has_microbiology) {
        return [10001];
      }
      if (this.data.has_citology) {
        return [10002];
      }
      if (this.data.has_gistology) {
        return [10003];
      }
      return [1000000];
    },
    pk_c() {
      const lpk = this.pk.trim();
      if (lpk === '') return -1;
      try {
        return parseInt(lpk, 10);
      } catch (e) {
        // pass
      }
      return -1;
    },
    has_changed() {
      return this.changed && this.data && this.data.ok && this.inserted;
    },
    ...mapGetters({
      user_data: 'user_data',
      researches_obj: 'researches',
      bases: 'bases',
    }),
    internal_base() {
      for (const b of this.bases) {
        if (b.internal_type) {
          return b.pk;
        }
      }
      return -1;
    },
    bases_obj() {
      return this.bases.reduce(
        (a, b) => ({
          ...a,
          [b.pk]: b,
        }),
        {},
      );
    },
    has_loc() {
      if (!this.user_data || !this.rmis_queue) {
        return false;
      }
      return !!this.user_data.rmis_location;
    },
    user_services() {
      if (!this.user_data || !this.user_data.user_services) {
        return [];
      }
      const r = [{ pk: -1, title: 'Не выбрано', full_title: 'Не выбрано' }];
      for (const d of Object.keys(this.researches_obj)) {
        for (const row of this.$store.getters.researches[d] || []) {
          if (this.user_data.user_services.includes(row.pk)) {
            r.push(row);
          }
        }
      }
      return r;
    },
    can_confirm() {
      for (const g of this.$store.getters.user_data.groups || []) {
        if (g === 'Без подтверждений') {
          return false;
        }
      }
      return true;
    },
    can_reset_amd() {
      for (const g of this.$store.getters.user_data.groups || []) {
        if (g === 'Управление отправкой в АМД') {
          return true;
        }
      }
      return false;
    },
    can_confirm_by_other_user() {
      for (const g of this.$store.getters.user_data.groups || []) {
        if (g === 'Работа от имени в описательных протоколах') {
          return true;
        }
      }
      return false;
    },
    navState() {
      if (!this.data.ok) {
        return null;
      }
      return {
        pk: this.data.direction.pk,
      };
    },
    workFromHistoryList() {
      return this.workFromHistory
        .map((p) => {
          for (const podr of this.workFromUsers) {
            const profile = podr.children.find((x) => x.id === p);

            if (profile) {
              return profile;
            }
          }

          return null;
        })
        .filter(Boolean);
    },
  },
  watch: {
    date() {
      this.load_history();
    },
    user_data: {
      async handler({ rmis_location: rmisLocation }) {
        if (!this.location.init && rmisLocation) {
          await this.load_location();
          this.location.init = true;
        }
      },
      immediate: true,
    },
    can_confirm_by_other_user: {
      async handler() {
        if (this.can_confirm_by_other_user && this.workFromUsers.length === 0) {
          const { users } = await usersPoint.loadUsersByGroup({
            group: ['Врач параклиники', 'Врач консультаций', 'Заполнение мониторингов', 'Свидетельство о смерти-доступ'],
          });
          this.workFromUsers = users;
        }
      },
      immediate: true,
    },
    has_loc: {
      async handler(h) {
        if (h) {
          await this.$store.dispatch(actions.INC_LOADING);
          await this.$store.dispatch(actions.GET_RESEARCHES);
          await this.$store.dispatch(actions.DEC_LOADING);
        }
      },
      immediate: true,
    },
    td: {
      handler() {
        this.load_location();
      },
    },
    navState() {
      if (this.inited) {
        UrlData.set(this.navState);
      }

      UrlData.title(this.data.ok ? this.data.direction.pk : null);
    },
  },
  mounted() {
    this.load_history();
    this.$root.$on('hide_dreg', () => {
      this.load_dreg_rows();
      this.dreg = false;
    });
    this.$root.$on('hide_benefit', () => {
      this.load_benefit_rows();
      this.benefit = false;
    });

    this.$root.$on('show_results', (pk) => {
      this.show_results_pk = pk;
    });

    this.$root.$on('hide_results', () => {
      this.show_results_pk = -1;
    });

    this.$root.$on('EDS:has-signs', (has) => {
      this.hasEDSigns = has;
    });

    const storedData = UrlData.get();
    if (storedData && typeof storedData === 'object' && storedData.pk) {
      this.load_pk(storedData.pk).then(() => {
        this.inited = true;
      });
    } else {
      this.inited = true;
    }

    this.$root.$on('open-direction-form', (pk) => this.load_pk(pk));

    this.$root.$on('preselect-args-ok', () => {
      this.hasPreselectOk = true;
    });

    this.$root.$on('table-field:errors:set', (fieldPk, hasInvalid) => {
      this.tableFieldsErrors = {
        ...this.tableFieldsErrors,
        [fieldPk]: hasInvalid,
      };
    });

    const urlParams = new URLSearchParams(window.location.search);
    this.embedded = urlParams.get('embedded') === '1';
    this.embeddedFull = urlParams.get('embeddedFull') === '1';
    window.$(window).on('beforeunload', this.unload);

    try {
      if (localStorage.getItem('results-paraclinic:work-from-history')) {
        const savedWorkedFrom = JSON.parse(localStorage.getItem('results-paraclinic:work-from-history'));

        if (Array.isArray(savedWorkedFrom)) {
          this.workFromHistory = savedWorkedFrom;
        }
      }
    } catch (e) {
      console.log(e);
    }

    this.$store.dispatch(actions.LOAD_REQUIRED_STATTALON_FIELDS);
    this.$store.dispatch(actions.LOAD_RESEARCHES_PK_REQUIRED_STATTALON_FIELDS);
  },
  beforeDestroy() {
    window.$(window).off('beforeunload', this.unload);
  },
  methods: {
    async add_services() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { pks, ok, message } = await this.$api('directions/add-additional-issledovaniye', {
        direction_pk: this.data.direction.pk,
        researches: this.moreServices,
      });
      await this.$store.dispatch(actions.DEC_LOADING);
      this.moreServices = [];
      if (ok) {
        this.load_pk(
          this.data.direction.pk,
          this.data.researches.map((r) => r.pk),
        );
        this.$root.$emit('msg', 'ok', `Добавлено услуг: ${pks.length}`);
      } else {
        this.$root.$emit('msg', 'error', message);
      }
    },
    unload() {
      if (!this.has_changed) {
        return undefined;
      }

      return 'Возможно имеются несохраненные изменения! Вы уверены, что хотите покинуть страницу?';
    },
    async load_location() {
      if (!this.has_loc) {
        return;
      }
      if (!this.loc_timer) {
        this.loc_timer = setInterval(() => this.load_location(), 120000);
      }
      this.location.loading = true;
      try {
        this.location.data = (
          await usersPoint.loadLocation({ date: this.td }).catch((e) => {
            console.error(e);
            return { data: [] };
          })
        ).data;
      } catch (e) {
        console.error(e);
        this.location.data = [];
      }
      this.location.loading = false;
    },
    tdm() {
      return moment().add(1, 'day').format('YYYY-MM-DD');
    },
    print_tube_iss(pk) {
      this.$root.$emit('print:barcodes:iss', [pk]);
    },
    async load_dreg_rows() {
      this.dreg_rows_loading = true;
      this.dreg_rows = (await this.$api('patients/individuals/load-dreg', this.data.patient, 'card_pk')).rows.filter(
        (r) => !r.date_end,
      );
      this.data.patient.has_dreg = this.dreg_rows.length > 0;
      this.dreg_rows_loading = false;
    },
    async load_benefit_rows() {
      this.benefit_rows_loading = true;
      this.benefit_rows = (await patientsPoint.loadBenefit(this.data.patient, 'card_pk')).rows.filter((r) => !r.date_end);
      this.data.patient.has_benefit = this.benefit_rows.length > 0;
      this.benefit_rows_loading = false;
    },
    async load_anamnesis() {
      this.anamnesis_loading = true;
      this.anamnesis_data = await patientsPoint.loadAnamnesis(this.data.patient, 'card_pk');
      this.anamnesis_loading = false;
    },
    change_mkb(row) {
      return (field) => {
        if (field.value && !row.confirmed && row.research.is_doc_refferal && this.stat_btn) {
          const ndiagnos = field.value.split(' ')[0] || '';
          if (ndiagnos !== row.diagnos && ndiagnos.match(/^[A-Z]\d{1,2}(\.\d{1,2})?$/gm)) {
            this.$root.$emit('msg', 'ok', `Диагноз в данных статталона обновлён\n${ndiagnos}`, 3000);
            // eslint-disable-next-line no-param-reassign
            row.diagnos = ndiagnos;
          }
        }
      };
    },
    open_results(pk) {
      if (this.research_open_history) {
        this.hide_results();
        return;
      }
      this.$store.dispatch(actions.INC_LOADING);
      this.research_history = [];
      directionsPoint
        .paraclinicResultPatientHistory({ pk })
        .then(({ data }) => {
          this.research_history = data;
        })
        .finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
          this.research_open_history = pk;
        });
    },
    hide_results() {
      this.research_history = [];
      this.research_open_history = null;
    },
    r(research) {
      return this.r_list(research).length === 0;
    },
    r_list(research) {
      const l = [];
      if (research.confirmed) {
        return [];
      }

      for (const g of research.research.groups) {
        if (!vGroup(g, research.research.groups, this.data.patient)) {
          continue;
        }
        let n = 0;
        for (const f of g.fields) {
          n++;
          if (
            (((f.required
                  && (f.value === ''
                    || f.value === '- Не выбрано'
                    || !f.value
                    || (f.field_type === 29 && (f.value.includes('"address": ""') || f.value.includes('"address":""')))))
                || this.tableFieldsErrors[f.pk])
              && vField(g, research.research.groups, f.visibility, this.data.patient))
            || (f.controlParam && !vField(g, research.research.groups, f.controlParam, this.data.patient))
          ) {
            l.push((g.title !== '' ? `${g.title} ` : '') + (f.title === '' ? `поле ${n}` : f.title));
          }
        }
      }

      if (research.research.is_doc_refferal) {
        for (const [key, value] of Object.entries(this.requiredStattalonFields)) {
          if (!research[key] || research[key] === -1) {
            l.push(value);
          }
        }
      }

      const keysData = Object.keys(this.researchesPkRequiredStattalonFields).map(key => Number(key));
      if (keysData.includes(research.research.pk)) {
        for (const [key, value] of Object.entries(this.researchesPkRequiredStattalonFields[research.research.pk])) {
          if (!research[key] || research[key] === -1) {
            l.push(value);
          }
        }
      }

      return l.slice(0, 2);
    },
    hide_modal_anamnesis_edit() {
      if (this.$refs.modalAnamnesisEdit) {
        this.$refs.modalAnamnesisEdit.$el.style.display = 'none';
      }
      this.anamnesis_edit = false;
    },
    save_anamnesis() {
      this.$store.dispatch(actions.INC_LOADING);
      patientsPoint.saveAnamnesis(this.data.patient, 'card_pk', { text: this.anamnesis_data.text }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
        this.new_anamnesis = this.anamnesis_data.text;
        this.hide_modal_anamnesis_edit();
      });
    },
    edit_anamnesis() {
      this.$store.dispatch(actions.INC_LOADING);
      patientsPoint
        .loadAnamnesis(this.data.patient, 'card_pk')
        .then((data) => {
          this.anamnesis_data = data;
        })
        .finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
          this.anamnesis_edit = true;
        });
    },
    load_history() {
      this.directions_history = [];
      this.$store.dispatch(actions.INC_LOADING);
      directionsPoint
        .paraclinicResultUserHistory(this, 'date')
        .then((data) => {
          this.directions_history = data.directions;
        })
        .finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
        });
    },
    reload_if_need() {
      if (this.date === moment().format('DD.MM.YYYY')) {
        this.load_history();
      }
    },
    load_pk(pk, withoutIssledovaniye = null) {
      this.pk = `${pk}`;
      return this.load(withoutIssledovaniye);
    },
    async load(withoutIssledovaniye = null) {
      if (!withoutIssledovaniye) {
        if (
          this.has_changed
          // eslint-disable-next-line no-alert,no-restricted-globals
          && !confirm('Возможно имеются несохраненные изменения! Вы действительно хотите закрыть текущий протокол?')
        ) {
          return;
        }
        this.clear(true);
      }
      this.$store.dispatch(actions.INC_LOADING);
      await directionsPoint
        .getParaclinicForm({ pk: this.pk_c, byIssledovaniye: this.iss_search, withoutIssledovaniye })
        .then((data) => {
          if (withoutIssledovaniye) {
            this.data.researches = [...this.data.researches, ...data.researches];
            return;
          }
          if (data.ok) {
            this.tnd = moment().add(1, 'day').format('YYYY-MM-DD');
            this.td_m_year = moment().subtract(1, 'year').format('YYYY-MM-DD');
            this.dreg_rows_loading = false;
            this.benefit_rows_loading = false;
            this.dreg_rows = [];
            this.benefit_rows = [];
            this.pk = '';
            this.data = data;
            if (!data.patient?.has_snils) {
              this.$root.$emit('msg', 'error', 'У пациента не заполнен СНИЛС!');
            }
            this.sidebarIsOpened = false;
            this.hasEDSigns = false;
            this.hasPreselectOk = false;
            setTimeout(async () => {
              this.$root.$emit('open-pk', data.direction.pk);
              for (let i = 0; i < 10; i++) {
                await new Promise((r) => {
                  setTimeout(() => r, 100);
                });
                if (this.hasPreselectOk) {
                  break;
                }
              }
              this.$root.$emit('preselect-args', { card_pk: data.patient.card_pk, base_pk: data.patient.base });
            }, 100);
            if (data.card_internal && data.status_disp === 'need' && data.has_doc_referral) {
              this.$root.$emit('msg', 'error', 'Диспансеризация не пройдена');
            }
            this.changed = false;
          } else {
            this.$root.$emit('msg', 'error', data.message);
          }
        })
        .finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
        });
    },
    hide_modal_create_directions() {
      if (this.$refs.modalCD) {
        this.$refs.modalCD.$el.style.display = 'none';
      }
      this.create_directions_for = -1;
      this.create_directions_data = [];
      this.create_directions_diagnosis = '';
    },
    create_directions(iss) {
      this.create_directions_diagnosis = iss.diagnos;
      this.create_directions_for = iss.pk;
    },
    visibility_state(iss) {
      const groups = {};
      const fields = {};
      const { groups: igroups } = iss.research;
      for (const group of iss.research.groups) {
        if (!vGroup(group, igroups, this.data.patient)) {
          groups[group.pk] = false;
        } else {
          groups[group.pk] = true;
          for (const field of group.fields) {
            fields[field.pk] = vField(group, igroups, field.visibility, this.data.patient);
          }
        }
      }

      return {
        groups,
        fields,
      };
    },
    save(iss) {
      this.hide_results();
      this.inserted = false;
      this.$store.dispatch(actions.INC_LOADING);
      directionsPoint
        .paraclinicResultSave({
          data: {
            ...iss,
            direction: this.data.direction,
          },
          with_confirm: false,
          visibility_state: this.visibility_state(iss),
        })
        .then((data) => {
          if (data.ok) {
            this.$root.$emit('msg', 'ok', 'Сохранено');
            // eslint-disable-next-line no-param-reassign
            iss.saved = true;
            if (data.execData) {
              // eslint-disable-next-line no-param-reassign
              iss.whoSaved = data.execData.whoSaved;
              // eslint-disable-next-line no-param-reassign
              iss.whoConfirmed = data.execData.whoConfirmed;
              // eslint-disable-next-line no-param-reassign
              iss.whoExecuted = data.execData.whoExecuted;
            }
            this.data.direction.amd = data.amd;
            this.data.direction.amd_number = data.amd_number;
            this.reload_if_need();
            this.changed = false;
          } else {
            this.$root.$emit('msg', 'error', data.message);
          }
        })
        .finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
          this.inserted = true;
          this.load_location();
        });
    },
    save_and_confirm(iss) {
      this.hide_results();
      this.inserted = false;
      this.$store.dispatch(actions.INC_LOADING);
      directionsPoint
        .paraclinicResultSave({
          data: {
            ...iss,
            direction: this.data.direction,
          },
          with_confirm: true,
          visibility_state: this.visibility_state(iss),
        })
        .then((data) => {
          if (data.ok) {
            this.$root.$emit('msg', 'ok', 'Сохранено');
            this.$root.$emit('msg', 'ok', 'Подтверждено');

            if (iss.work_by) {
              this.workFromHistory = [iss.work_by, ...this.workFromHistory.filter((x) => x !== iss.work_by).slice(0, 5)];
            }
            localStorage.setItem('results-paraclinic:work-from-history', JSON.stringify(this.workFromHistory));

            // eslint-disable-next-line no-param-reassign
            iss.saved = true;
            // eslint-disable-next-line no-param-reassign
            iss.allow_reset_confirm = true;
            // eslint-disable-next-line no-param-reassign
            iss.confirmed = true;
            if (data.execData) {
              // eslint-disable-next-line no-param-reassign
              iss.whoSaved = data.execData.whoSaved;
              // eslint-disable-next-line no-param-reassign
              iss.whoConfirmed = data.execData.whoConfirmed;
              // eslint-disable-next-line no-param-reassign
              iss.whoExecuted = data.execData.whoExecuted;
            }
            this.data.direction.amd = data.amd;
            this.data.direction.amd_number = data.amd_number;
            this.data.direction.all_confirmed = this.data.researches.every((r) => Boolean(r.confirmed));
            for (const r of this.data.researches) {
              r.confirmed_at = data.confirmed_at;
            }
            this.reload_if_need();
            this.changed = false;
          } else {
            this.$root.$emit('msg', 'error', data.message);
          }
        })
        .finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
          this.inserted = true;
          this.load_location();
          this.$root.$emit('open-pk', this.data.direction.pk);
        });
    },
    confirm(iss) {
      this.hide_results();
      this.inserted = false;
      this.$store.dispatch(actions.INC_LOADING);
      directionsPoint
        .paraclinicResultConfirm({ iss_pk: iss.pk })
        .then((data) => {
          if (data.ok) {
            this.$root.$emit('msg', 'ok', 'Подтверждено');
            // eslint-disable-next-line no-param-reassign
            iss.confirmed = true;
            // eslint-disable-next-line no-param-reassign
            iss.allow_reset_confirm = true;
            this.data.direction.amd = data.amd;
            this.data.direction.amd_number = data.amd_number;
            this.data.direction.all_confirmed = this.data.researches.every((r) => Boolean(r.confirmed));
            for (const r of this.data.researches) {
              r.confirmed_at = data.confirmed_at;
            }
            this.reload_if_need();
            this.changed = false;
          } else {
            this.$root.$emit('msg', 'error', data.message);
          }
        })
        .finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
          this.inserted = true;
          this.load_location();
          this.$root.$emit('open-pk', this.data.direction.pk);
        });
    },
    async reset_confirm(iss) {
      this.hide_results();

      try {
        const moreMessage = this.hasEDSigns ? 'ИМЕЮТСЯ ЭЛЕКТРОННЫЕ ПОДПИСИ! ' : '';
        await this.$dialog.confirm(`${moreMessage}Подтвердите сброс подтверждения услуги «${iss.research.title}»`);
      } catch (_) {
        return;
      }

      this.inserted = false;
      await this.$store.dispatch(actions.INC_LOADING);
      const data = await directionsPoint.paraclinicResultConfirmReset({ iss_pk: iss.pk });
      if (data.ok) {
        this.$root.$emit('msg', 'ok', 'Подтверждение сброшено');
        // eslint-disable-next-line no-param-reassign
        iss.confirmed = false;
        // eslint-disable-next-line no-param-reassign
        iss.whoConfirmed = null;
        // eslint-disable-next-line no-param-reassign
        iss.work_by = null;
        // eslint-disable-next-line no-param-reassign
        iss.whoExecuted = null;
        this.data.direction.amd = 'not_need';
        this.data.direction.all_confirmed = this.data.researches.every((r) => Boolean(r.confirmed));
        if (this.hasEDSigns) {
          this.$root.$emit('EDS:archive-document');
        }
        for (const r of this.data.researches) {
          r.confirmed_at = null;
        }
        this.reload_if_need();
        this.changed = false;
      } else {
        this.$root.$emit('msg', 'error', data.message);
      }
      this.$root.$emit('open-pk', this.data.direction.pk);
      await this.$store.dispatch(actions.DEC_LOADING);
      this.inserted = true;
      this.load_location();
    },
    clear(ignoreOrig) {
      const ignore = ignoreOrig || false;
      if (
        !ignore
        && this.has_changed
        // eslint-disable-next-line no-alert,no-restricted-globals
        && !confirm('Возможно имеются несохраненные изменения! Вы действительно хотите закрыть текущий протокол?')
      ) {
        return;
      }

      this.inserted = false;
      this.changed = false;
      this.anamnesis_edit = false;
      this.new_anamnesis = null;
      this.data = { ok: false };
      this.research_open_history = null;
      this.dreg_rows_loading = false;
      this.dreg_rows = [];
      this.benefit_rows_loading = false;
      this.benefit_rows = [];
      this.tableFieldsErrors = {};
      this.moreServices = [];
      cleanCaches();
      this.$root.$emit('preselect-card', null);
      this.$root.$emit('open-pk', -1);
    },
    print_direction(pk) {
      this.$root.$emit('print:directions', [pk]);
    },
    print_results(pk) {
      this.$root.$emit('print:results', [pk]);
    },
    print_example(pk) {
      this.$root.$emit('print:example', [pk]);
    },
    copy_results(row, pk) {
      this.$store.dispatch(actions.INC_LOADING);
      directionsPoint
        .paraclinicDataByFields({ pk, pk_dest: row.pk })
        .then(({ data }) => {
          this.hide_results();
          this.replace_fields_values(row, data);
        })
        .finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
        });
    },
    load_template(row, pk) {
      this.$store.dispatch(actions.INC_LOADING);
      researchesPoint
        .getTemplateData({ pk: parseInt(pk, 10) })
        .then(({ data: { fields: data, title } }) => {
          this.template_fields_values(row, data, title);
        })
        .finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
        });
    },
    async open_slot(row) {
      await this.$store.dispatch(actions.INC_LOADING);
      this.slot.id = row.slot;
      this.slot.data = await usersPoint.getReserve({ pk: row.slot, patient: row.uid });
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async close_slot() {
      if (!this.$refs.modalSlot) {
        return;
      }
      this.$refs.modalSlot.$el.style.display = 'none';
      this.slot.id = null;
      this.slot.data = {};
    },
    async fill_slot() {
      let s = '';
      for (const r of this.user_services) {
        if (r.pk === this.slot.data.direction_service) {
          s = r.title;
          break;
        }
      }
      try {
        await this.$dialog.confirm(`Подтвердите назначение услуги ${s}`);
        await this.$store.dispatch(actions.INC_LOADING);
        const cards = await patientsPoint.searchCard({
          type: this.internal_base,
          query: this.slot.data.patient_uid,
          list_all_cards: false,
          inc_rmis: true,
        });
        const cardPk = (cards.results || [{}])[0].pk;
        const { direction } = await usersPoint.fillSlot({ slot: { ...this.slot, card_pk: cardPk } });
        await this.$store.dispatch(actions.DEC_LOADING);
        this.load_location();
        this.open_fill_slot(direction);
      } catch (_) {
        await this.$store.dispatch(actions.DEC_LOADING);
      }
    },
    open_fill_slot(direction) {
      this.close_slot();
      this.load_pk(direction);
    },
    template_fields_values(row, dataTemplate, title) {
      this.$dialog
        .alert(title, {
          view: 'replace-append-modal',
        })
        .then(({ data }) => {
          if (data === 'append') {
            this.append_fields_values(row, dataTemplate);
          } else {
            this.replace_fields_values(row, dataTemplate);
          }
        });
    },
    replace_fields_values(row, data) {
      for (const g of row.research.groups) {
        for (const f of g.fields) {
          if (![1, 3, 16, 17, 20, 13, 14, 11].includes(f.field_type)) {
            f.value = data[f.pk] || '';
          }
        }
      }
      this.$root.$emit('checkTables');
    },
    append_fields_values(row, data) {
      for (const g of row.research.groups) {
        for (const f of g.fields) {
          if (![1, 3, 16, 17, 20, 13, 14, 11, 2, 32, 33, 36, 27, 28, 29, 30, 37, 35].includes(f.field_type) && data[f.pk]) {
            this.append_value(f, data[f.pk]);
          }
        }
      }
      this.$root.$emit('checkTables');
    },
    clear_vals(row) {
      this.$dialog.confirm('Вы действительно хотите очистить результаты?').then(() => {
        this.$root.$emit('msg', 'ok', 'Очищено');
        for (const g of row.research.groups) {
          for (const f of g.fields) {
            if (![1, 3, 16, 17, 20, 13, 14, 11, 23].includes(f.field_type)) {
              this.clear_val(f);
            }
          }
        }
      });
    },
    clear_val(field) {
      // eslint-disable-next-line no-param-reassign
      field.value = '';
    },
    append_value(field, value) {
      let addVal = value;
      if (addVal !== ',' && addVal !== '.') {
        if (
          field.value.length > 0
          && field.value[field.value.length - 1] !== ' '
          && field.value[field.value.length - 1] !== '\n'
        ) {
          if (field.value[field.value.length - 1] === '.') {
            addVal = addVal.replace(/./, addVal.charAt(0).toUpperCase());
          }
          addVal = ` ${addVal}`;
        } else if (
          (field.value.length === 0
            || (field.value.length >= 2
              && field.value[field.value.length - 2] === '.'
              && field.value[field.value.length - 1] === '\n'))
          && field.title === ''
        ) {
          addVal = addVal.replace(/./, addVal.charAt(0).toUpperCase());
        }
      }
      // eslint-disable-next-line no-param-reassign
      field.value += addVal;
    },
    select_research(pk) {
      if (this.slot.data.direction) {
        return;
      }
      this.slot.data.direction_service = pk;
    },
    add_researches(row, pks) {
      this.create_directions(row);
      setTimeout(() => {
        for (const pk of pks) {
          this.$root.$emit('researches-picker:add_researchcd', pk);
        }
      }, 300);
    },
    show_results(pk) {
      this.$root.$emit('print:results', pk);
    },
    async send_amd() {
      await this.$store.dispatch(actions.INC_LOADING);
      const toSend = this.directions_history.filter((d) => ['error', 'need'].includes(d.amd)).map((d) => d.pk);
      if (toSend.length > 0) {
        await directionsPoint.sendAMD({ pks: toSend });
        this.$root.$emit('msg', 'ok', 'Отправка запланирована');
        this.reload_if_need();
      } else {
        this.$root.$emit('msg', 'error', 'Не найдены подходящие направления');
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async reset_amd(pks) {
      try {
        await this.$dialog.confirm('Подтвердите сброс статуса отправки в АМД');
        await this.$store.dispatch(actions.INC_LOADING);
        await directionsPoint.resetAMD({ pks });
        this.load_pk(this.data.direction.pk);
        this.reload_if_need();
        await this.$store.dispatch(actions.DEC_LOADING);
      } catch (e) {
        // pass
      }
    },
    async send_to_amd(pks) {
      await this.$store.dispatch(actions.INC_LOADING);
      await directionsPoint.sendAMD({ pks });
      this.load_pk(this.data.direction.pk);
      this.reload_if_need();
      this.$root.$emit('msg', 'ok', 'Отправка запланирована');
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    updateValue(field, prop) {
      return (newValue) => {
        // eslint-disable-next-line no-param-reassign
        field[prop] = newValue;
      };
    },
    enter_field(...args) {
      return enterField.apply(this, args);
    },
    leave_field(...args) {
      return leaveField.apply(this, args);
    },
    needFillWorkBy(row) {
      if (!this.can_confirm_by_other_user || row.confirmed) {
        return false;
      }
      return !row.work_by;
    },
  },
};
</script>

<style scoped lang="scss">
.results-root {
  position: absolute;
  top: 36px;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  align-items: stretch;
  flex-direction: row;
  flex-wrap: nowrap;
  align-content: stretch;
  overflow-x: hidden;

  &.embedded {
    top: 0;
  }

  & > div {
    align-self: stretch;
  }
}

@media (max-width: 1366px) {
  .burger {
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 11;
    background-color: #323639;
    width: 36px;
    transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
    cursor: pointer;

    &:hover {
      background-color: #4a5054;
    }

    &.active {
      background-color: #03614b;
      &:hover {
        background-color: #059271;
      }

      .burger-inner i {
        transform: rotate(90deg);
      }
    }

    .burger-inner {
      writing-mode: vertical-lr;
      text-orientation: mixed;
      color: #fff;
      padding: 20px 0 0 7px;
      font-size: 16px;
      i {
        transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
      }
    }

    .burger-lines {
      top: 290px;
      bottom: 10px;
      left: 17px;

      &,
      &::before,
      &::after {
        position: absolute;
        width: 1px;
        background-color: rgba(#fff, 0.1);
      }

      &::before,
      &::after {
        top: 0;
        bottom: 0;
        content: '';
      }

      &::before {
        left: -9px;
      }

      &::after {
        left: 9px;
      }
    }
  }
}

@media (max-width: 1366px) {
  .backdrop {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(#000, 0.6);
    backdrop-filter: blur(3px);
    z-index: 9;
    display: flex;
    align-items: center;
    justify-content: center;
    padding-left: 341px;

    &-inner {
      color: #fff;
      text-shadow: 0 0 4px rgba(#000, 0.6);
    }
  }
}

@media (min-width: 1367px) {
  .burger,
  .backdrop {
    display: none;
  }
}

.results-sidebar {
  width: 304px;
  border-right: 1px solid #b1b1b1;
  display: flex;
  flex-direction: column;

  @media (max-width: 1366px) {
    position: absolute;
    top: 0;
    left: -304px;
    bottom: 0;
    z-index: 10;
    background-color: #fff;
    transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);

    &.opened {
      left: 36px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
    }
  }
}

.results-content {
  display: flex;
  flex-direction: column;
  width: calc(100% - 304px);

  @media (max-width: 1366px) {
    padding-left: 36px;
    width: 100%;
  }

  &.embedded {
    padding-left: 0 !important;
    width: 100% !important;
  }
}

.results-top {
  border-bottom: 1px solid #b1b1b1;
  height: 68px;
  padding: 5px;
}

.results-top > div {
  font-family: 'Courier New', Courier, monospace !important;
}

.research-title {
  position: sticky;
  top: 0;
  background-color: #ddd;
  text-align: center;
  padding: 5px;
  font-weight: bold;
  z-index: 4;
  display: flex;

  &.withFiles {
    .research-left {
      width: calc(100% - 540px);
    }
    .research-right {
      width: 540px;
    }
  }
}

.research-left {
  position: relative;
  text-align: left;
  width: calc(100% - 430px);
}

.research-right {
  text-align: right;
  width: 430px;
  margin-top: -5px;
  margin-right: -5px;
  margin-bottom: -5px;
  white-space: nowrap;

  .btn,
  ::v-deep .file-btn {
    border-radius: 0;
    padding: 5px 4px;
  }
}

.right-f {
  width: 140px;
  display: inline-block;

  ::v-deep .btn {
    border-radius: 0;
    padding-top: 5px;
    padding-bottom: 5px;
  }
}

.results-history {
  margin-top: -95px;
  margin-left: -295px;
  margin-right: -130px;
  padding: 8px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);

  &-embedded {
    margin-top: -65px;
    margin-left: -130px;
  }

  ul {
    padding-left: 20px;
    margin: 0;

    li {
      font-weight: normal;

      a {
        font-weight: bold;
        display: inline-block;
        padding: 2px 4px;
        background: rgba(#000, 0.03);
        border-radius: 4px;
        margin-left: 3px;

        &:hover {
          background: rgba(#000, 0.1);
        }
      }
    }
  }
}

.results-editor {
  height: calc(100% - 68px);
  overflow-y: auto;
  overflow-x: hidden;
}

.embeddedFull {
  .results-editor {
    height: 100%;
  }
}

.sidebar-bottom-top {
  background-color: #eaeaea;
  flex: 0 0 34px;
  display: flex;
  justify-content: flex-start;
  align-items: center;

  ::v-deep .form-control {
    border-radius: 0;
    border-top: none;
    border-left: none;
    border-right: none;
  }

  span {
    display: inline-block;
    white-space: nowrap;
    padding-left: 5px;
    width: 130px;
  }
}

.control-row {
  height: 34px;
  background-color: #f3f3f3;
  display: flex;
  flex-direction: row;
  margin-bottom: 10px;

  button {
    align-self: stretch;
    border-radius: 0;
  }

  div {
    align-self: stretch;
  }
}

.res-title {
  padding: 5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.direction,
.sd {
  padding: 5px;
  margin: 5px;
  border-radius: 5px;
  border: 1px solid rgba(0, 0, 0, 0.14);
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);

  hr {
    margin: 3px;
  }
}

.research-row {
  margin-top: 3px;
  margin-bottom: 3px;
  padding: 3px;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);
}

.anamnesis {
  padding: 10px;
}

.status-list {
  display: flex;
  overflow: hidden;
  text-overflow: ellipsis;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.directions {
  position: relative;
  height: calc(100% - 68px);
  padding-bottom: 34px;

  &.noStat {
    padding-bottom: 0;
  }

  .inner {
    height: 100%;
    overflow-y: auto;
    overflow-x: hidden;
  }

  &.has_loc {
    .inner {
      height: calc(50% + 17px);
    }
  }

  .rmis_loc {
    position: absolute;
    height: 50%;
    bottom: 0;
    left: 0;
    right: 0;
    border-top: 1px solid #b1b1b1;

    .title {
      height: 20px;
      background: #eaeaea;
      text-align: center;
      position: relative;

      .loader {
        position: absolute;
        right: 2px;
        top: 1px;
        animation: rotating 1.5s linear infinite;
      }
    }

    .inner {
      height: calc(100% - 20px);
      overflow-y: auto;
      overflow-x: hidden;

      &.stat_btn {
        height: calc(100% - 54px);
      }

      table {
        margin-bottom: 0;
      }

      th,
      td {
        font-size: 12px;
        padding: 2px;
      }

      tr {
        cursor: pointer;

        &.current {
          td {
            background-color: #687282;
            color: #fff;
          }
        }
      }
    }
  }

  .side-bottom {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    border-radius: 0;
    display: flex;
    flex-direction: row;

    .btn {
      height: 34px;
      border-radius: 0;
    }

    &_all {
      .btn:first-child {
        width: 163px;
      }

      .btn:last-child {
        width: 140px;
      }
    }

    &_amd,
    &_stat {
      .btn {
        width: 100%;
      }
    }
  }
}

.dreg_nex {
  color: #687282;
}

.dreg_ex {
  color: #da3b6c;
  text-shadow: 0 0 4px rgba(#da3b6c, 0.6);
}

.slot {
  &-0 {
    color: #e1f2fe;
  }

  &-1 {
    color: #f7581c;
  }

  &-2 {
    color: #049372;
  }
}

.content-picker {
  display: flex;
  flex-wrap: wrap;
  justify-content: stretch;
  align-items: stretch;
  align-content: flex-start;
}

.research-select {
  align-self: stretch;
  display: flex;
  align-items: center;
  padding: 1px 2px 1px;
  color: #000;
  background-color: #fff;
  text-decoration: none;
  transition: 0.15s linear all;
  margin: 0;
  font-size: 12px;
  min-width: 0;
  flex: 0 1 auto;
  width: 25%;
  height: 34px;
  border: 1px solid #6c7a89 !important;
  cursor: pointer;
  text-align: left;
  outline: transparent;

  &.active {
    background: #049372 !important;
    color: #fff;
  }

  &:hover {
    box-shadow: inset 0 0 8px rgba(0, 0, 0, 0.8) !important;
  }
}

.inline-form {
  background: none;
  border: none;
  padding: 0;
  display: inline-block;
  width: 140px;
  margin-right: -50px;

  &:focus {
    outline: none;
  }
}

.lastresults {
  table-layout: fixed;
  padding: 0;
  margin: 0;
  color: #000;
  background-color: #ffdb4d;
  border-color: #000;

  ::v-deep th,
  ::v-deep td {
    border-color: #000;
  }

  ::v-deep a {
    color: #000;
    text-decoration: dotted underline;
  }

  ::v-deep a:hover {
    text-decoration: none;
  }
}

.comment {
  margin-left: 3px;
  color: #049372;
  font-weight: 600;
}

.disp {
  a:not(.btn):not(.not-black) {
    color: #0d0d0d !important;
    text-decoration: dotted underline;

    &:hover {
      text-decoration: none;
    }
  }

  &_need,
  &_need:focus,
  &_need:active,
  &_need:hover {
    color: #f7581c !important;
    text-shadow: 0 0 4px rgba(#f7581c, 0.6);
    font-weight: bold;
  }

  &_finished,
  &_finished:focus,
  &_finished:active,
  &_finished:hover {
    color: #049372 !important;
    text-shadow: 0 0 4px rgba(#049372, 0.6);
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

  &_need,
  &_need a {
    color: #ff0000 !important;
  }

  &_finished,
  &_finished a {
    color: #049372 !important;
  }

  a {
    text-decoration: dotted underline;

    &:hover {
      text-decoration: none;
    }
  }
}

.status,
.control-row .amd {
  padding: 5px;
}

.status {
  font-weight: bold;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-none {
  color: #cf3a24;
}

.amd {
  font-weight: bold;

  &-need,
  &-error {
    color: #cf3a24;
  }

  &-planned {
    color: #d9be00;
  }

  &-ok {
    color: #049372;
  }
}

label.field-title {
  font-weight: normal;
}

textarea {
  resize: vertical;
}

.simple-value {
  padding: 5px;

  ul {
    margin: 0;
    padding-left: 20px;
  }
}
</style>
