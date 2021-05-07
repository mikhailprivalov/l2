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
        <input class="form-control" v-model="card.phone" v-mask="'8 999 9999999'">
      </div>
      <div class="form-row sm-header">
        Данные для листа ожидания
      </div>
      <div class="form-row sm-f">
        <div class="row-t">Дата</div>
        <input class="form-control" type="date" v-model="date" :min="td">
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
          <research-display v-for="(res, idx) in disp_researches" :simple="true"
                            :no_tooltip="true"
                            :key="res.pk"
                            :title="res.title" :pk="res.pk" :n="idx"
                            :nof="disp_researches.length"/>
        </div>
        <div class="controls">
          <button class="btn btn-primary-nb btn-blue-nb" type="button" @click="save">Создать записи в лист ожидания</button>
        </div>
      </template>
      <div v-else style="padding: 10px;color: gray;text-align: center">
        Услуги не выбраны
      </div>

      <div class="rows" v-if="rows_count > 0">
        <table class="table table-bordered table-condensed table-sm-pd"
               style="table-layout: fixed; font-size: 12px; margin-top: 0;">
          <colgroup>
            <col width="75">
            <col/>
            <col/>
            <col width="100"/>
            <col width="75"/>
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
              <td>{{r.date}}</td>
              <td>{{r.service}}</td>
              <td style="white-space: pre-wrap">{{r.comment}}</td>
              <td>{{r.phone}}</td>
              <td>{{STATUSES[r.status]}}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import * as actions from '@/store/action-types';
import api from '@/api';
import moment from 'moment';
import ResearchDisplay from '@/ui-cards/ResearchDisplay.vue';
import patientsPoint from '@/api/patients-point';

const STATUSES = { 0: 'ожидает', 1: 'выполнено', 2: 'отменено' };

export default {
  name: 'ListWaitCreator',
  components: {
    ResearchDisplay,
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
      loaded: true,
      date: moment().format('YYYY-MM-DD'),
      td: moment().format('YYYY-MM-DD'),
      comment: '',
      rows: [],
      STATUSES,
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
    async save() {
      await this.$store.dispatch(actions.INC_LOADING);
      const result = await api(
        'list-wait/create', this,
        ['card_pk', 'researches', 'date', 'comment'],
        {
          phone: this.card.phone,
        },
      );
      await this.load_data();
      await this.$store.dispatch(actions.DEC_LOADING);
      if (result.ok) {
        window.okmessage('Записи в лист ожидания созданы');
        this.date = moment().format('YYYY-MM-DD');
        this.td = this.date;
        this.comment = '';
        this.$root.$emit('researches-picker:clear_all');
      }
    },
    async load_data() {
      if (this.card_pk === -1) {
        return;
      }
      if (!this.visible) {
        this.rows = await api('list-wait/actual-rows', this, 'card_pk');
        return;
      }
      this.loaded = false;
      await this.$store.dispatch(actions.INC_LOADING);
      this.card = await patientsPoint.getCard(this, 'card_pk');
      this.loaded = true;
      this.rows = await api('list-wait/actual-rows', this, 'card_pk');
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
  computed: {
    disp_researches() {
      return this.researches.map((id) => this.$store.getters.researches_obj[id]);
    },
    rows_count() {
      return this.rows.length;
    },
    rows_mapped() {
      return this.rows.map((r) => ({
        pk: r.pk,
        date: moment(r.exec_at).format('DD.MM.YYYY'),
        service: r.research__title,
        comment: r.comment,
        status: r.work_status,
        phone: r.phone,
      }));
    },
  },
};
</script>

<style scoped lang="scss">
  .root, .empty {
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

  .researches, .controls {
    padding: 5px;
  }

  .controls {
    padding-top: 0;
  }

  .rows {
    margin-top: 5px;
  }
</style>
