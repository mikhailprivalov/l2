<template>
  <div class="root-agg">
    <button
      style="margin-bottom: 5px; position: sticky; left: 0;"
      class="btn btn-blue-nb"
      @click="print_form"
    >
      Печать
    </button>
    <table class="table table-responsive table-bordered table-condensed">
      <colgroup>
        <col style="width: 300px">
        <col
          v-for="d in dates"
          :key="d"
        >
      </colgroup>
      <thead>
        <tr>
          <th
            rowspan="2"
            class="first-cell"
          >
            Наименование ЛП
          </th>
          <th
            v-for="d in dates"
            :key="d"
          >
            {{ d }}
          </th>
        </tr>
        <tr>
          <th
            v-for="d in dates"
            :key="d"
            class="cl-td"
          >
            <div
              v-for="t in timesInDates[d]"
              :key="t"
              class="time"
              :data-datetime="`${d} ${t}`"
            >
              {{ t.split(':')[0] }}
            </div>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="r in rows"
          :key="r.pk"
        >
          <td>
            <div
              class="drug"
              :class="{ cancel: r.cancel }"
            >
              {{ r.drug }}
            </div>
            <span
              v-tippy
              class="badge badge-primary"
              title="Форма выпуска"
            >{{ r.form_release }}</span>
            <span
              v-tippy
              class="badge badge-primary"
              title="Способ применения"
            >{{ r.method }}</span>
            <span
              v-tippy
              class="badge badge-info"
              title="Дозировка"
            >{{ r.dosage }}</span>
            <span
              v-tippy
              class="badge badge-light"
              title="Дата создания"
            >{{ r.created_at }}</span>
            <span
              v-if="r.step > 1"
              v-tippy
              class="badge badge-warning"
              title="Шаг дней"
            >шаг {{ r.step }} дн</span>
            <template v-if="can_cancel">
              <a
                v-if="!r.cancel"
                class="badge badge-secondary"
                href="#"
                @click.prevent="cancelRow(r.pk, true)"
              >
                <i class="fa fa-circle" /> отменить ЛП
              </a>
              <a
                v-else
                class="badge badge-secondary"
                href="#"
                @click.prevent="cancelRow(r.pk, false)"
              >
                <i class="fa fa-circle" /> вернуть ЛП
              </a>
            </template>
            <div v-if="r.comment">
              <strong>Комментарий:</strong>&nbsp;{{ r.comment }}
            </div>
          </td>
          <td
            v-for="d in dates"
            :key="d"
            class="cl-td"
          >
            <PharmacotherapyTime
              v-for="t in timesInDates[d]"
              :key="t"
              :data="r.dates[d][t]"
            />
          </td>
        </tr>
        <tr v-if="rows.length === 0">
          <td>Нет данных</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script lang="ts">
import PharmacotherapyTime from '@/fields/PharmacotherapyTime.vue';
import * as actions from '@/store/action-types';

export default {
  components: { PharmacotherapyTime },
  props: {
    direction: {},
  },
  data() {
    return {
      rows: [],
      dates: [],
      times: [],
      timesInDates: {},
    };
  },
  computed: {
    can_cancel() {
      for (const g of this.$store.getters.user_data.groups || []) {
        if (g === 'Врач стационара' || g === 'Admin') {
          return true;
        }
      }
      return false;
    },
  },
  async mounted() {
    await this.load();
    this.$root.$on('pharmacotherapy-aggregation:reload', () => this.load());
    window.$('.root-agg').on('mouseover mouseout', '[data-datetime]', event => {
      const t$ = window.$(event.target);
      const all$ = window.$(`[data-datetime="${t$.data('datetime')}"]`);
      if (event.type === 'mouseover') {
        all$.addClass('datetime-hover');
      } else {
        all$.removeClass('datetime-hover');
      }
    });
  },
  beforeDestroy() {
    window.$('.root-agg [data-datetime]').off('mouseover mouseout');
  },
  methods: {
    async load() {
      await this.$store.dispatch(actions.INC_LOADING);
      const {
        result, dates, times, timesInDates,
      } = await this.$api('procedural-list/get-procedure', this, 'direction');
      this.rows = result;
      this.dates = dates;
      this.times = times;
      this.timesInDates = timesInDates;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async cancelRow(pk, cancel) {
      if (cancel) {
        try {
          await this.$dialog.confirm('Вы действительно хотите отменить назначение?');
        } catch (_) {
          return;
        }
      } else {
        try {
          await this.$dialog.confirm('Вы действительно хотите вернуть назначение?');
        } catch (_) {
          return;
        }
      }
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await this.$api('procedural-list/procedure-cancel', { pk, cancel });
      if (ok) {
        this.$root.$emit('msg', 'ok', message);
        this.$root.$emit('pharmacotherapy-aggregation:reload');
      } else {
        this.$root.$emit('msg', 'error', message);
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    print_form() {
      window.open(`/forms/pdf?type=107.02&&hosp_pk=${this.direction}`);
    },
  },
};
</script>

<style scoped lang="scss">
.time {
  display: inline-block;
  width: 30px;
  text-align: center;
  height: 24px;
  font-weight: normal;
  font-size: 12px;
  vertical-align: bottom;

  //&:nth-child(odd) {
  //  background-color: rgba(#000, .045);
  //}
}

.root-agg {
  overflow-x: auto;
}

a.badge:hover {
  background-color: #5f6267;
}

table {
  min-width: 100%;
  max-width: none;
  width: auto;

  .cl-td {
    white-space: nowrap;
  }
}

.drug {
  width: 296px;

  &.cancel:not(:hover) {
    text-decoration: line-through;
  }
}

.root-agg {
  position: relative;
}

.table tr > td:first-child,
.table .first-cell {
  background-color: white;
  position: sticky;
  left: -1px;
  z-index: 2;
  box-shadow: 2px 0 2px rgba(0, 0, 0, 0.1);
}
</style>
