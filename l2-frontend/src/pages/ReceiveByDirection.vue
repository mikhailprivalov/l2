<template>
  <div>
    <div class="row top-panel">
      <div class="col-xs-4">
        <div class="card-no-hover card card-1 work-cards">
          <div class="input-group">
            <input
              ref="q"
              v-model="q"
              type="text"
              class="form-control"
              spellcheck="false"
              :placeholder="'Номер направления'"
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
              <div><strong>Направление {{ s.pk }} {{ s.new ? 'принято' : `было принято ранее — ${s.receivedate}` }}</strong></div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-xs-4">
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
    <table class="table table-bordered table-responsive table-condensed">
      <colgroup>
        <col width="200">
        <col width="200">
        <col>
      </colgroup>
      <thead>
        <tr>
          <th>Тип</th>
          <th>№ направления</th>
          <th>Исследования</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="r in receiveHistory"
          :key="r.pk"
        >
          <td>
            {{ r.type }}
          </td>
          <td>
            {{ r.pk }}
          </td>
          <td>{{ r.researches.join('; ') }}</td>
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
  },
  data() {
    return {
      workMode: 'direction',
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
})
export default class ReceiveOneByOne extends Vue {
  workMode: string;

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
    const { q } = this;
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
  font-size: 40px;
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

.btn-bc{
  padding: 2px;
  width: 100%;
}
</style>
