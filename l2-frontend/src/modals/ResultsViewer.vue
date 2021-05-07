<template>
  <modal ref="modal" @close="hide_modal" v-if="data.ok" show-footer="true" white-bg="true">
    <span slot="header">Результаты исследований</span>
    <div slot="body">
      <table style="width: 680px;">
        <tbody>
        <tr>
          <td style="text-align: left;" colspan="3">Направление №{{data.direction.pk}}</td>
        </tr>
        <tr>
          <td colspan="2" style="text-align: left;">ФИО: {{data.client.fio}}</td>
        </tr>
        <tr>
          <td style="text-align: left;">Номер карты: {{data.client.cardnum}}</td>
          <td style="text-align: center;">Пол: {{data.client.sex}}</td>
          <td style="text-align: right;">Дата рождения: {{data.client.dr}} ({{data.client.age}})</td>
        </tr>
        </tbody>
      </table>
      <div ref="rc">
        <table class="table ct" style="width: 620px; margin-bottom: 5px;">
          <thead v-if="!data.desc">
          <tr>
            <!-- eslint-disable-next-line max-len -->
            <th style="color: #000;padding: 2px; border: 1px solid rgb(0, 0, 0);line-height: 1.15; font-size: 12pt; font-weight: 600; font-family: 'Times New Roman', 'Liberation Serif', Times, serif;">
              Исследование
            </th>
            <!-- eslint-disable-next-line max-len -->
            <th style="color: #000;padding: 2px; border: 1px solid rgb(0, 0, 0);line-height: 1.15; font-size: 12pt; font-weight: 600; font-family: 'Times New Roman', 'Liberation Serif', Times, serif;">
              Значение
            </th>
            <!-- eslint-disable-next-line max-len -->
            <th style="white-space: normal;color: #000;padding: 2px; border: 1px solid rgb(0, 0, 0);line-height: 1.15; font-size: 12pt; font-weight: 600; font-family: 'Times New Roman', 'Liberation Serif', Times, serif;width: 70px;">
              Единицы измерения
            </th>
            <!-- eslint-disable-next-line max-len -->
            <th style="color: #000;padding: 2px; border: 1px solid rgb(0, 0, 0);line-height: 1.15; font-size: 12pt; font-weight: 600; font-family: 'Times New Roman', 'Liberation Serif', Times, serif;">
              Референсы
            </th>
          </tr>
          </thead>
          <tbody v-for="(row, kpk) of data.results" :key="kpk">
          <tr v-if="Object.keys(row.fractions).length > 1">
            <!-- eslint-disable-next-line max-len -->
            <th colspan="4" style="color: #000;padding: 2px; border: 1px solid rgb(0, 0, 0);line-height: 1.15; font-size: 12pt; font-family: 'Times New Roman', 'Liberation Serif', Times, serif;margin: 0;">
              {{row.title}}
              <template v-if="!data.desc && row.tube_time_get">(дата забора б/м: {{row.tube_time_get}})</template>
            </th>
          </tr>
          <tr v-for="(fraction, fpk) of row.fractions" :key="fpk">
            <!-- eslint-disable-next-line max-len -->
            <td style="color: #000;padding: 2px; border: 1px solid rgb(0, 0, 0);line-height: 1.15; font-size: 12pt; font-family: 'Times New Roman', 'Liberation Serif', Times, serif;margin: 0;">
                <template v-if="Object.keys(row.fractions).length > 1">
                  &nbsp;&nbsp;&nbsp;&nbsp;{{fraction.title}}
                </template>
                <template v-else>
                  {{row.title}}
                  <template v-if="!data.desc && row.tube_time_get">(дата забора б/м: {{row.tube_time_get}})</template>
                </template>
            </td>
            <!-- eslint-disable-next-line max-len -->
            <td :colspan="need_units_and_refs(fraction)? 1: 3" v-html="fraction.result" style="color: #000;padding: 2px; border: 1px solid rgb(0, 0, 0);line-height: 1.15; font-size: 12pt; font-family: 'Times New Roman', 'Liberation Serif', Times, serif;margin: 0;"></td>
            <!-- eslint-disable-next-line max-len -->
            <td v-if="need_units_and_refs(fraction)" style="color: #000;padding: 2px; border: 1px solid rgb(0, 0, 0);line-height: 1.15; font-size: 12pt;  font-family: 'Times New Roman', 'Liberation Serif', Times, serif;width: 70px;">
              {{fraction.units}}
            </td>
            <!-- eslint-disable-next-line max-len -->
            <td v-if="data.client.sex === 'м' && need_units_and_refs(fraction)" style="color: #000;padding: 2px; border: 1px solid rgb(0, 0, 0);line-height: 1.15; font-size: 12pt;  font-family: 'Times New Roman', 'Liberation Serif', Times, serif;margin: 0;">
              <!-- eslint-disable-next-line max-len -->
              <div v-for="(refer, k) of fraction.ref_m" :key="k" style="color: #000;line-height: 1.15; font-size: 12pt; font-family: 'Times New Roman', 'Liberation Serif', Times, serif;margin: 0;">
                <!-- eslint-disable-next-line max-len -->
                <span v-if="k !== 'Все'" style="line-height: 1.15; font-size: 12pt; font-family: 'Times New Roman', 'Liberation Serif', Times, serif;margin: 0;">{{k}}: </span>{{refer}}
              </div>
            </td>
            <!-- eslint-disable-next-line max-len -->
            <td v-else-if="need_units_and_refs(fraction)" style="color: #000;padding: 2px; border: 1px solid rgb(0, 0, 0);line-height: 1.15; font-size: 12pt; font-family: 'Times New Roman', 'Liberation Serif', Times, serif;margin: 0;">
              <!-- eslint-disable-next-line max-len -->
              <div v-for="(refer, k) of fraction.ref_f" :key="k" style="line-height: 1.15; font-size: 12pt; font-family: 'Times New Roman', 'Liberation Serif', Times, serif;margin: 0;">
                <!-- eslint-disable-next-line max-len -->
                <span v-if="k !== 'Все'" style="line-height: 1.15; font-size: 12pt; font-family: 'Times New Roman', 'Liberation Serif', Times, serif;margin: 0;">{{k}}: </span>{{refer}}
              </div>
            </td>
          </tr>
          </tbody>
        </table>
        <!-- eslint-disable-next-line max-len -->
        <div style="color: #000;line-height: 1.15; font-size: 12pt; font-family: 'Times New Roman', 'Liberation Serif', Times, serif;margin: 0;">
          Дата выполнения исследования: {{data.direction.date}}
        </div>
      </div>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-4">
          <button type="button" @click="copyResults" class="btn btn-primary-nb btn-blue-nb">
            Копировать результаты
          </button>
          <br><br>
          <button type="button" @click="selectResults" class="btn btn-primary-nb btn-blue-nb">
            Выделить результаты
          </button>
        </div>
        <div class="col-xs-4">
          <button type="button" @click="printResults" class="btn btn-primary-nb print-b">Печать результатов</button>
          <br><br>
          <button type="button" @click="printDirection" class="btn btn-primary-nb print-b">Печать направления</button>
        </div>
        <div class="col-xs-4">
          <a :href="data.pacs" target="_blank" class="btn btn-primary-nb btn-blue-nb" v-if="!!data.pacs">
            Снимок
          </a>
          <div style="height: 14px;" v-else />
          <br><br>
          <button type="button" @click="hide_modal" class="btn btn-primary-nb btn-blue-nb">Закрыть</button>
        </div>
      </div>
    </div>
  </modal>
</template>

<script>
import Modal from '../ui-cards/Modal.vue';
import directionsPoint from '../api/directions-point';
import * as actions from '../store/action-types';

export default {
  name: 'results-viewer',
  components: { Modal },
  props: {
    pk: {
      type: Number,
      required: true,
    },
    no_desc: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      data: {},
    };
  },
  created() {
    this.$store.dispatch(actions.INC_LOADING);
    directionsPoint.getResults(this, ['pk'], {
      force: this.no_desc,
    }).then((data) => {
      if (data.desc && !this.no_desc) {
        this.printResults();
        this.hide_modal();
        return;
      }
      if (!data.full) {
        // eslint-disable-next-line no-alert
        alert('Результаты подтверждены не полностью. Данные могут быть изменены');
      }
      this.data = data;
    }).finally(() => {
      this.$store.dispatch(actions.DEC_LOADING);
    });
  },
  methods: {
    hide_modal() {
      this.$root.$emit('hide_results');
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
    },
    selectResults() {
      window.selectTextEl(this.$refs.rc);
    },
    printResults() {
      this.$root.$emit('print:results', [this.pk]);
    },
    printDirection() {
      this.$root.$emit('print:directions', [this.pk]);
    },
    copyResults() {
      window.selectTextEl(this.$refs.rc);
      document.execCommand('copy');
      window.clearselection();
      window.okblink(this.$refs.rc);
      window.okmessage('Результаты скопированы', 'Ок');
    },
    need_units_and_refs(fraction) {
      return (fraction.units !== '' || JSON.stringify(fraction.ref_m) !== JSON.stringify({}))
        && (
          JSON.stringify(fraction.ref_m) !== JSON.stringify({ Все: '' })
          || JSON.stringify(fraction.ref_f) !== JSON.stringify({})
        )
        && JSON.stringify(fraction.ref_f) !== JSON.stringify({ Все: '' });
    },
  },
};
</script>

<style scoped lang="scss">
  th, td {
    padding: 2px !important;
    white-space: nowrap;
    word-wrap: normal;
  }

  .ct {
    border-collapse: collapse;
    margin-top: 5px
  }

  .ct td {
    border-collapse: collapse;
  }

</style>
