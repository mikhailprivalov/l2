<template>
  <div
    v-if="card_pk === -1"
    class="empty"
  >
    <div>Пациент не выбран</div>
  </div>
  <div
    v-else
    class="root"
  >
    <div class="col-form mid">
      <div class="form-row sm-header">
        Данные из картотеки<span
          v-if="!loaded"
          class="loading-text loading-sm"
        >&nbsp;загрузка</span>
      </div>
      <div class="form-row sm-f">
        <div class="row-t">
          Телефон
        </div>
        <input
          v-model="card.phone"
          v-mask="'8 999 9999999'"
          class="form-control"
        >
      </div>
      <div class="form-row sm-header">
        {{ hasOnlyHosp ? 'Данные записи на госпитализацию' : 'Данные для листа ожидания' }}
      </div>
      <div
        v-if="!hasOnlyHosp"
        class="form-row sm-f"
      >
        <div class="row-t">
          Дата
        </div>
        <input
          v-model="date"
          class="form-control"
          type="date"
          :min="td"
        >
      </div>
      <div
        v-else
        class="form-row sm-f"
      >
        <div class="row-t">
          Дата госпитализации
        </div>
        <DatePicker
          v-model="date"
          mode="date"
          :available-dates="availableDates"
          :attributes="attributes"
          :masks="masks"
          :model-config="modelConfig"
          trim-weeks
          color="teal"
        />
      </div>
      <div
        v-if="hasOnlyHosp"
        class="form-row sm-f"
      >
        <div class="row-t">
          Отделение
        </div>
        <Treeselect
          v-model="hospitalDepartment"
          :multiple="false"
          :disable-branch-nodes="true"
          class="treeselect-noborder"
          :options="hospitalDepartments"
          :append-to-body="true"
          placeholder="Отделение госпитализации"
          :clearable="true"
        />
      </div>
      <div
        v-if="hasOnlyHosp"
        class="form-row sm-f"
      >
        <div class="row-t">
          Диагноз
        </div>
        <MKBField
          v-model="diagnosis"
          :short="false"
        />
      </div>
      <div class="form-row sm-f">
        <div class="row-t">
          Комментарий
        </div>
        <textarea
          v-model="comment"
          class="form-control"
        />
      </div>
      <template v-if="researches.length > 0">
        <div class="form-row sm-header">
          Услуги
        </div>
        <div class="researches">
          <ResearchDisplay
            v-for="(res, idx) in disp_researches"
            :key="res.pk"
            :simple="true"
            :no_tooltip="true"
            :title="res.title"
            :pk="res.pk"
            :n="idx"
            :nof="disp_researches.length"
          />
        </div>
        <div v-if="!date" />
        <div
          v-else-if="!validDate && cito"
          class="alert alert-warning"
        >
          Запись будет произведена как CITO сверх лимита
        </div>
        <div
          v-else-if="!validDate"
          class="alert alert-warning"
        >
          Выбранная дата недоступна для записи на госпитализацию
        </div>
        <div class="controls">
          <button
            class="btn btn-primary-nb btn-blue-nb"
            type="button"
            :disabled="!valid"
            @click="save"
          >
            {{
              hasOnlyHosp
                ? 'Записать на госпитализацию'
                : hasMixedHosp
                  ? 'Госпитализация не может быть выбрана с не госпитализацией'
                  : hasManyHosp
                    ? 'Нужно выбрать только одну стационарную услугу'
                    : 'Создать записи в лист ожидания'
            }}
          </button>
        </div>
      </template>
      <div
        v-else
        style="padding: 10px; color: gray; text-align: center"
      >
        Услуги не выбраны
      </div>

      <div
        v-if="rows_count > 0"
        class="rows"
      >
        <table
          class="table table-bordered table-condensed table-sm-pd"
          style="table-layout: fixed; font-size: 12px; margin-top: 0"
        >
          <colgroup>
            <col width="75">
            <col>
            <col>
            <col width="100">
            <col width="80">
          </colgroup>
          <thead>
            <tr>
              <th>Дата</th>
              <th>Услуга</th>
              <th>Комментарий</th>
              <th>Телефон</th>
              <th>Статус</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in rows_mapped"
              :key="r.pk"
            >
              <td>{{ r.date }}</td>
              <td>
                {{ r.service }}
                <template v-if="r.hospital">
                  <hr>
                  Отделение: {{ r.hospital }}
                </template>
              </td>
              <td style="white-space: pre-wrap">
                {{ (r.diagnosis ? 'Диагноз: ' + r.diagnosis + '\n\n' : '') + r.comment }}
              </td>
              <td>{{ r.phone }}</td>
              <td>
                <template v-if="!r.hospital">
                  {{ STATUSES[r.status] }}
                </template>
                <template v-else-if="!r.canceled && r.status !== 3">
                  <HospPlanScheduleButton :data="r" />
                  <div class="spacer" />
                  <HospPlanCancelButton :data="r" />
                </template>
                <template v-else-if="r.slot">
                  {{ r.slot }}
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import moment from 'moment';
import DatePicker from 'v-calendar/src/components/DatePicker.vue';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import * as actions from '@/store/action-types';
import ResearchDisplay from '@/ui-cards/ResearchDisplay.vue';
import patientsPoint from '@/api/patients-point';
import MKBField from '@/fields/MKBField.vue';
import HospPlanScheduleButton from '@/ui-cards/HospPlanScheduleButton.vue';
import HospPlanCancelButton from '@/ui-cards/HospPlanCancelButton.vue';

const STATUSES = { 0: 'ожидает', 1: 'выполнено', 2: 'отменено' };

export default {
  name: 'ListWaitCreator',
  components: {
    ResearchDisplay,
    HospPlanScheduleButton,
    HospPlanCancelButton,
    Treeselect,
    MKBField,
    DatePicker,
  },
  props: {
    card_pk: {
      required: true,
    },
    researches: {
      type: Array,
    },
    visible: {
      type: Boolean,
    },
  },
  data() {
    return {
      card: {
        phone: '',
      },
      loadCnt: 0,
      date: '',
      td: moment().format('YYYY-MM-DD'),
      comment: '',
      rows: [],
      STATUSES,
      hospitalDepartments: [],
      hospitalDepartment: null,
      diagnosis: '',
      availableHospDates: {},
      masks: {
        iso: 'DD.MM.YYYY',
        data: ['DD.MM.YYYY'],
        input: ['DD.MM.YYYY'],
      },
      modelConfig: {
        type: 'string',
        mask: 'YYYY-MM-DD',
      },
      cito: false,
      counts: {},
    };
  },
  computed: {
    disp_researches() {
      return this.researches.map((id) => this.$store.getters.researches_obj[id]).filter(Boolean);
    },
    rows_count() {
      return this.rows.length;
    },
    rows_mapped() {
      return this.rows.map((r) => ({
        ...r,
        date: moment(r.exec_at).format('DD.MM.YYYY'),
        service: r.research__title,
        comment: r.comment,
        status: r.work_status,
        phone: r.phone,
        hospital: r.hospital_department__title || null,
        diagnosis: r.diagnos || null,
      }));
    },
    researchesObjects() {
      const r = [];
      for (const pk of this.researches) {
        const res = this.$store.getters.researches_obj[pk];
        if (res) {
          r.push(res);
        }
      }
      return r;
    },
    hasHosp() {
      return this.researchesObjects.length > 0 && this.researchesObjects.some((r) => r.is_hospital);
    },
    hasNonHosp() {
      return this.researchesObjects.length > 0 && this.researchesObjects.some((r) => !r.is_hospital);
    },
    hasMixedHosp() {
      return this.hasHosp && this.hasNonHosp;
    },
    hasManyHosp() {
      return this.researchesObjects.filter((r) => r.is_hospital).length > 1;
    },
    hasOnlyHosp() {
      return this.hasHosp && !this.hasNonHosp && !this.hasManyHosp;
    },
    validDate() {
      return !this.hasOnlyHosp || (!!this.date && !!this.availableHospDates[this.date]);
    },
    valid() {
      return (
        !this.hasHosp
        || (!this.hasNonHosp
          && !!this.hospitalDepartment
          && !!this.diagnosis.trim()
          && (this.validDate
            || (!!this.date && this.cito && Object.prototype.hasOwnProperty.call(this.availableHospDates, this.date))))
      );
    },
    loaded() {
      return this.loadCnt === 0;
    },
    availableDates() {
      return Object.keys(this.availableHospDates)
        .filter(
          (d) => (this.cito && Object.prototype.hasOwnProperty.call(this.availableHospDates, d)) || !!this.availableHospDates[d],
        )
        .map((d) => {
          const md = moment(d, 'YYYY-MM-DD').toDate();

          return {
            start: md,
            end: md,
          };
        });
    },
    attributes() {
      return Object.keys(this.availableHospDates).map((k) => {
        const c = this.counts[k];

        return {
          dates: moment(k, 'YYYY-MM-DD').toDate(),
          popover: {
            label: c ? `Занято ${c.used} / ${c.available}` : 'на этот день нет запланированных слотов',
          },
          dot: this.availableHospDates[k] ? 'green' : 'red',
        };
      });
    },
  },
  watch: {
    rows_count: {
      handler() {
        this.$root.$emit('list-wait-creator:rows-count', this.rows_count);
      },
      immediate: true,
    },
    card_pk: {
      handler() {
        this.rows = [];
        this.load_data();
      },
      immediate: true,
    },
    researches: {
      handler() {
        if (this.hospitalDepartments.length === 0 && this.hasHosp) {
          this.load_stationar_deparments();
        }
        this.actualizeHospDates();
      },
      immediate: true,
    },
    visible: {
      handler() {
        this.load_data();
        this.actualizeHospDates();
      },
    },
    date() {
      this.actualizeHospDates();
    },
  },
  mounted() {
    this.$root.$on('update_card_data', () => this.load_data());
    this.$root.$on('reload-list-wait-data', () => this.load_data());
  },
  methods: {
    async actualizeHospDates() {
      if (!this.visible) {
        return true;
      }
      if (!this.hasOnlyHosp) {
        this.availableHospDates = {};
        return true;
      }
      this.loadCnt++;
      const { data, counts, cito } = await this.$api('schedule/available-hospitalization-plan', {
        research_pk: this.researches[0],
      });
      this.counts = counts || {};
      this.cito = !!cito;
      this.loadCnt--;
      this.availableHospDates = data;
      if (!this.availableHospDates[this.date] && this.date) {
        if (!cito) {
          this.$root.$emit('msg', 'error', `Дата ${moment(this.date, 'YYYY-MM-DD').format('DD.MM.YYYY')} недоступна`, 2500);
          this.date = '';
        }
      }
      return !!this.date;
    },
    async load_stationar_deparments() {
      this.loadCnt++;
      const { data } = await this.$api('procedural-list/suitable-departments');
      this.hospitalDepartments = data;
      this.loadCnt--;
    },
    async save() {
      const isValidDate = await this.actualizeHospDates();
      if (!isValidDate) {
        return;
      }
      const hasHosp = this.hasOnlyHosp;
      this.loadCnt++;
      await this.$store.dispatch(actions.INC_LOADING);
      const result = await this.$api(
        'list-wait/create',
        this,
        ['card_pk', 'researches', 'date', 'comment', 'hospitalDepartment', 'diagnosis'],
        {
          phone: this.card.phone,
        },
      );
      await this.load_data();
      await this.$store.dispatch(actions.DEC_LOADING);
      if (result.ok) {
        this.$root.$emit('msg', 'ok', hasHosp ? 'Запись на госпитализацию успешно создана' : 'Записи в лист ожидания созданы');
        this.date = '';
        this.availableHospDates = {};
        this.td = this.date;
        this.comment = '';
        this.hospitalDepartment = null;
        this.diagnosis = '';
        this.$root.$emit('researches-picker:clear_all');
      }
      this.loadCnt--;
    },
    async load_data() {
      if (this.card_pk === -1) {
        return;
      }
      if (!this.visible) {
        this.rows = await this.$api('list-wait/actual-rows', this, 'card_pk');
        return;
      }
      this.loadCnt++;
      await this.$store.dispatch(actions.INC_LOADING);
      this.card = await patientsPoint.getCard(this, 'card_pk');
      this.rows = await this.$api('list-wait/actual-rows', this, 'card_pk');
      await this.$store.dispatch(actions.DEC_LOADING);
      this.loadCnt--;
    },
  },
};
</script>

<style scoped lang="scss">
.root,
.empty {
  position: absolute;
  top: 0 !important;
  left: 0;
  right: 0;
  bottom: 0;
}

.empty {
  color: gray;
  display: flex;
  justify-content: center;

  div {
    align-self: center;
  }
}

.root {
  overflow: auto;
}

.col-form {
  padding-bottom: 10px;
}

.researches,
.controls {
  padding: 5px;
}

.controls {
  padding-top: 0;
}

.rows {
  margin-top: 5px;
}

td hr {
  margin: 5px 0;
}
</style>
