<template>
  <div v-if="card_pk === -1" class="empty">
    <div>Пациент не выбран</div>
  </div>
  <div v-else class="root">
    <div class="col-form mid">
      <div class="form-row sm-header">
        Данные из картотеки<span v-if="!loaded" class="loading-text loading-sm">&nbsp;загрузка</span>
      </div>
      <div class="form-row sm-f">
        <div class="row-t">Телефон</div>
        <input class="form-control" v-model="card.phone" v-mask="'8 999 9999999'" />
      </div>
      <div class="form-row sm-header">
        {{ hasOnlyHosp ? 'Данные записи на госпитализацию' : 'Данные для листа ожидания' }}
      </div>
      <div class="form-row sm-f">
        <div class="row-t">Дата</div>
        <input class="form-control" type="date" v-model="date" :min="td" />
      </div>
      <div class="form-row sm-f" v-if="hasOnlyHosp">
        <div class="row-t">Отделение</div>
        <treeselect
          :multiple="false"
          :disable-branch-nodes="true"
          class="treeselect-noborder"
          :options="hospitalDepartments"
          :append-to-body="true"
          placeholder="Отделение госпитализации"
          :clearable="true"
          v-model="hospitalDepartment"
        />
      </div>
      <div class="form-row sm-f" v-if="hasOnlyHosp">
        <div class="row-t">Диагноз</div>
        <MKBField v-model="diagnosis" :short="false" />
      </div>
      <div class="form-row sm-f">
        <div class="row-t">Комментарий</div>
        <textarea class="form-control" v-model="comment"></textarea>
      </div>
      <template v-if="researches.length > 0">
        <div class="form-row sm-header">
          Услуги
        </div>
        <div class="researches">
          <research-display
            v-for="(res, idx) in disp_researches"
            :simple="true"
            :no_tooltip="true"
            :key="res.pk"
            :title="res.title"
            :pk="res.pk"
            :n="idx"
            :nof="disp_researches.length"
          />
        </div>
        <div class="controls">
          <button class="btn btn-primary-nb btn-blue-nb" type="button" @click="save" :disabled="!valid">
            {{
              hasOnlyHosp
                ? 'Записать на госпитализацию'
                : hasMixedHosp
                ? 'Госпитализация не может быть выбрана с не госпитализацией'
                : 'Создать записи в лист ожидания'
            }}
          </button>
        </div>
      </template>
      <div v-else style="padding: 10px;color: gray;text-align: center">
        Услуги не выбраны
      </div>

      <div class="rows" v-if="rows_count > 0">
        <table
          class="table table-bordered table-condensed table-sm-pd"
          style="table-layout: fixed; font-size: 12px; margin-top: 0;"
        >
          <colgroup>
            <col width="75" />
            <col />
            <col />
            <col width="100" />
            <col width="75" />
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
            <tr v-for="r in rows_mapped" :key="r.pk">
              <td>{{ r.date }}</td>
              <td>
                {{ r.service }}
                <template v-if="r.hospital">
                  <hr />
                  Отделение: {{ r.hospital }}
                </template>
              </td>
              <td style="white-space: pre-wrap">{{ (r.diagnosis ? 'Диагноз: ' + r.diagnosis + '\n\n' : '') + r.comment }}</td>
              <td>{{ r.phone }}</td>
              <td>{{ STATUSES[r.status] }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import moment from 'moment';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import * as actions from '@/store/action-types';
import ResearchDisplay from '@/ui-cards/ResearchDisplay.vue';
import patientsPoint from '@/api/patients-point';
import MKBField from '@/fields/MKBField.vue';

const STATUSES = { 0: 'ожидает', 1: 'выполнено', 2: 'отменено' };

export default {
  name: 'ListWaitCreator',
  components: {
    ResearchDisplay,
    Treeselect,
    MKBField,
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
      date: moment().format('YYYY-MM-DD'),
      td: moment().format('YYYY-MM-DD'),
      comment: '',
      rows: [],
      STATUSES,
      hospitalDepartments: [],
      hospitalDepartment: null,
      diagnosis: '',
    };
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
      },
      immediate: true,
    },
    visible: {
      handler() {
        this.load_data();
      },
    },
  },
  mounted() {
    this.$root.$on('update_card_data', () => this.load_data());
  },
  methods: {
    async load_stationar_deparments() {
      this.loadCnt++;
      const { data } = await this.$api('procedural-list/suitable-departments');
      this.hospitalDepartments = data;
      this.loadCnt--;
    },
    async save() {
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
        this.$root.$emit('msg', 'ok', 'Записи в лист ожидания созданы');
        this.date = moment().format('YYYY-MM-DD');
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
  computed: {
    disp_researches() {
      return this.researches.map(id => this.$store.getters.researches_obj[id]).filter(Boolean);
    },
    rows_count() {
      return this.rows.length;
    },
    rows_mapped() {
      return this.rows.map(r => ({
        pk: r.pk,
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
      return this.researchesObjects.length > 0 && this.researchesObjects.some(r => r.is_hospital);
    },
    hasNonHosp() {
      return this.researchesObjects.length > 0 && this.researchesObjects.some(r => !r.is_hospital);
    },
    hasMixedHosp() {
      return this.hasHosp && this.hasNonHosp;
    },
    hasOnlyHosp() {
      return this.hasHosp && !this.hasNonHosp;
    },
    valid() {
      return !this.hasHosp || (!this.hasNonHosp && !!this.hospitalDepartment && !!this.diagnosis.trim());
    },
    loaded() {
      return this.loadCnt === 0;
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
