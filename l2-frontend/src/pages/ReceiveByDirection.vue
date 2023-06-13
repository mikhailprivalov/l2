<template>
  <div>
    <div class="row top-panel">
      <div class="col-xs-6">
        <div class="card-no-hover card card-1 work-cards">
          <div class="input-group">
            <input
              ref="q"
              v-model="q"
              type="text"
              class="form-control"
              spellcheck="false"
              placeholder="Номер направления"
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
      <div class="col-xs-6">
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
      Принятые за сегодня <i
        v-if="historyLoading"
        class="fa fa-spinner"
      />
    </h5>
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
  data() {
    return {
      workMode: 'direction',
      lastResearches: [],
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
export default class ReceiveByDirection extends Vue {
  workMode: string;

  lastResearches: string[];

  q: string;

  currentLaboratory: number;

  receiveStatuses: ReceiveStatus[];

  receiveHistory: ReceiveHistory[];

  historyLoading: boolean;

  focus() {
    window.$(this.$refs.q).focus();
  }

  async receive() {
    if (!this.q) {
      return;
    }
    await this.$store.dispatch(actions.INC_LOADING);
    const { q } = this;
    const {
      ok, researches, invalid, message,
    } = await this.$api(
      '/laboratory/receive-one-by-one',
      this,
      ['currentLaboratory', 'nextN', 'workMode'],
      { q },
    );
    for (const msg of invalid) {
      this.$error(msg);
    }
    if (message) {
      this.$error(message);
    }
    this.lastResearches = researches;
    this.receiveStatuses = ok;
    await this.$store.dispatch(actions.DEC_LOADING);
    await this.loadHistory();
    this.q = '';
  }

  async loadHistory() {
    this.historyLoading = true;
    const { rows } = await this.$api('/laboratory/receive-history', this, 'currentLaboratory', { onlyDirections: true });
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
  .col-xs-6:last-child {
    border-left: 1px solid lightgray;
    h5 {
      padding: 0;
      margin: 0;
      font-weight: normal
    }
  }
}

.last-researches {
  height: 140px;
  overflow-x: hidden;
  overflow-y: auto;
}

.work-cards {
  margin-top: 0;
  padding: 5px;
}

.receive-messages {
  height: 90px;
  overflow-y: auto;
  overflow-x: hidden;
}

.btn-bc {
  padding: 2px;
  width: 100%;
}
</style>
