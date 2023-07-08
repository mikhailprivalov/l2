<template>
  <div>
    <div class="row top-panel">
      <div class="col-xs-4">
        <div class="card-no-hover card card-1 work-cards">
          <RadioFieldById
            v-model="workMode"
            :variants="WORK_MODES"
            rounded
          />
          <div class="input-group">
            <input
              ref="q"
              v-model="q"
              type="text"
              class="form-control"
              spellcheck="false"
              :placeholder="workMode === 'direction' ? 'Номер направления' : 'Номер штрих-кода'"
              maxlength="20"
              @keypress.enter="receive"
            >
            <span class="input-group-btn">
              <button
                class="btn btn-blue-nb"
                type="button"
                @click="receive"
              >
                Принять
              </button>
            </span>
          </div>
          <div class="receive-messages">
            <div
              v-for="s in receiveStatuses"
              :key="s.pk"
            >
              <div>Емк. <strong>{{ s.pk }} {{ s.new ? 'принята' : `была принята ранее — ${s.receivedate}` }}</strong></div>
              <div>
                Лаборатории: <strong v-html="/* eslint-disable-line vue/no-v-html */ s.labs.join('<br/>')" />
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-xs-4">
        <div class="big-number">
          <span class="big-number-prefix">№</span> {{ lastN || '--' }}
        </div>
        <br>
        <br>
        <label>
          Следующий номер: <input
            v-model.number="nextN"
            class="form-control next-n-input"
            type="number"
          >
        </label>
        <small><a
          href="#"
          class="a-under"
          @click="loadNextN"
        >сброс</a></small>
      </div>
      <div class="col-xs-4">
        <h5>Исследования:</h5>
        <div class="last-researches">
          <div
            v-for="(r, i) in lastResearchesWithEmpty"
            :key="i"
          >
            {{ r }}
          </div>
        </div>
      </div>
    </div>
    <h5>
      <small
        class="fastlinks"
        style="display: inline-block;float: right"
      ><a
        :href="`/ui/receive/journal?lab_pk=${ currentLaboratory }`"
        target="_blank"
      >Журнал приёма</a>&nbsp;<ExecutionList /></small> Принятые за сегодня <i
        v-if="historyLoading"
        class="fa fa-spinner"
      />
    </h5>
    <table class="table table-bordered table-responsive table-condensed">
      <colgroup>
        <col width="110">
        <col width="200">
        <col width="150">
        <col width="180">
        <col>
        <col width="50">
      </colgroup>
      <thead>
        <tr>
          <th>№ принятия</th>
          <th>Тип емкости</th>
          <th>№ емкости</th>
          <th>Лаборатория</th>
          <th>Исследования</th>
          <th>Ш/к</th>
          <th>Брак</th>
          <th>Описание брак</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="r in receiveHistory"
          :key="r.pk"
        >
          <td>{{ r.n }}</td>
          <td>
            <ColorTitled
              :color="r.color"
              :title="r.type"
            />
          </td>
          <td>
            {{ r.pk }}
          </td>
          <td>{{ r.labs.join('; ') }}</td>
          <td>{{ r.researches.join('; ') }}</td>
          <td>
            <a
              v-if="!r.isDirection"
              class="btn btn-sm btn-blue-nb btn-bc"
              :href="`/barcodes/tubes?tubes_id=[${r.pk}]`"
              target="_blank"
            ><i
              class="fa fa-barcode"
            /></a>
          </td>
          <td class="text-center cl-td">
            <label>
              <input
                v-model="r.is_defect"
                type="checkbox"
                @change="changeRow(r)"
                @keypress="changeRow(r)"
                @input="changeRow(r)"
              >
            </label>
          </td>
          <td class="text-center cl-td">
            <div class="input-group">
              <input
                ref="q"
                v-model="r.defect_text"
                type="text"
                class="form-control"
                spellcheck="false"
                maxlength="12"
                :readonly="!r.is_defect"
                @keypress.enter="saveDefect"
              >
              <span class="input-group-btn">
                <button
                  class="btn btn-blue-nb"
                  type="button"
                  @click="saveDefect(r)"
                >
                  Сохранить
                </button>
              </span>
            </div>
          </td>
        </tr>
        <tr v-if="receiveHistory.length === 0">
          <td colspan="6">
            нет данных
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import { debounce } from 'lodash/function';

import * as actions from '@/store/action-types';
import RadioFieldById from '@/fields/RadioFieldById.vue';
import ExecutionList from '@/ui-cards/ExecutionList.vue';
import ColorTitled from '@/ui-cards/ColorTitled.vue';

const WORK_MODES = [
  { id: 'tube', label: 'Штрих-код' },
  { id: 'direction', label: 'Номер направления' },
];

interface ReceiveStatus {
  pk: number,
  new: boolean,
  labs: string[],
  receivedate: string,
}

interface ReceiveHistory {
  pk: number,
  n: number,
  type: string,
  color: string,
  labs: string[],
  researches: string[],
}

@Component({
  components: {
    RadioFieldById,
    ExecutionList,
    ColorTitled,
  },
  data() {
    return {
      workMode: WORK_MODES[0].id,
      WORK_MODES,
      lastResearches: [],
      lastN: '--',
      nextN: 1,
      q: '',
      currentLaboratory: -1,
      receiveStatuses: [],
      receiveHistory: [],
      historyLoading: false,
    };
  },
  mounted() {
    this.focus();
    this.$root.$on('change-laboratory', (pk) => {
      this.currentLaboratory = pk;
      this.loadNextN();
      this.receiveHistory = [];
      this.debouncedLoadHistory();
    });
    this.$root.$emit('emit-laboratory');
  },
  computed: {
    lastResearchesWithEmpty() {
      if (this.lastResearches.length === 0) {
        return ['--'];
      }
      return this.lastResearches;
    },
  },
  watch: {
    workMode() {
      this.focus();
    },
  },
})
export default class ReceiveOneByOne extends Vue {
  workMode: string;

  WORK_MODES: typeof WORK_MODES;

  lastResearches: string[];

  lastN: string | number;

  q: string;

  nextN: number;

  currentLaboratory: number;

  receiveStatuses: ReceiveStatus[];

  receiveHistory: ReceiveHistory[];

  historyLoading: boolean;

  focus() {
    window.$(this.$refs.q).focus();
  }

  async loadNextN() {
    const { lastDaynum } = await this.$api('/laboratory/last-received-daynum', { pk: this.currentLaboratory });

    this.nextN = lastDaynum + 1;
  }

  async receive() {
    if (!this.q) {
      return;
    }
    await this.$store.dispatch(actions.INC_LOADING);
    let { q } = this;
    if (q.substr(0, 3) === '460' && q.length === 13) {
      q = String(Number(q.substr(0, 12)) - 460000000000);
      this.workMode = 'direction';
    }
    const {
      ok, researches, invalid, lastN,
    } = await this.$api(
      '/laboratory/receive-one-by-one',
      this,
      ['currentLaboratory', 'nextN', 'workMode'],
      { q },
    );
    for (const msg of invalid) {
      this.$root.$emit('msg', 'error', msg);
    }
    this.lastN = lastN;
    this.lastResearches = researches;
    this.receiveStatuses = ok;
    await this.loadNextN();
    await this.$store.dispatch(actions.DEC_LOADING);
    await this.loadHistory();
    this.q = '';
  }

  async saveDefect(row) {
    await this.$store.dispatch(actions.INC_LOADING);
    const { rows } = await this.$api('/laboratory/save-defect-tube', { row });
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  // eslint-disable-next-line class-methods-use-this
  changeRow(row) {
    if (!row.is_defect) {
      // eslint-disable-next-line no-param-reassign
      row.defect_text = '';
      this.saveDefect(row);
      this.loadHistory();
    }
  }

  async loadHistory() {
    this.historyLoading = true;
    const { rows } = await this.$api('/laboratory/receive-history', this, 'currentLaboratory');
    this.receiveHistory = rows;
    this.historyLoading = false;
  }

  debouncedLoadHistory = debounce(function () {
    this.loadHistory();
  }, 100);
}
</script>

<style lang="scss" scoped>
.top-panel {
  .col-xs-4:nth-child(2) {
    text-align: center;
    padding-top: 5px;
    border-right: 1px solid lightgray;
    border-left: 1px solid lightgray;
    min-height: 160px;
  }

  .col-xs-4:last-child h5 {
    padding: 0;
    margin: 0;
    font-weight: normal
  }
}

.last-researches {
  height: 140px;
  overflow-x: hidden;
  overflow-y: auto;
}

.big-number {
  font-size: 60px;
  display: inline-block;
  vertical-align: middle
}

.big-number-prefix {
  color: lightgray;
}

.next-n-input {
  width: 60px;
  display: inline-block;
}

.work-cards {
  padding: 5px;

  .input-group {
    margin-top: 10px;
  }
}

.receive-messages {
  height: 60px;
  overflow-y: auto;
  overflow-x: hidden;
}

.btn-bc {
  padding: 2px;
  width: 100%;
}
</style>
