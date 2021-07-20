<template>
  <div class="report-root" :style="`--font-size-mon: ${fontSize}px;`">
    <div>
      <div class="float-right font-settings">
        <a href="#" @click.prevent="decFont()" class="a-under-reversed" title="Уменьшить шрифт таблицы" v-tippy>-A</a>
        &nbsp;
        <a href="#" @click.prevent="incFont()" class="a-under-reversed" title="Увеличить шрифт таблицы" v-tippy>+A</a>
      </div>
      <h3>{{ title }}</h3>
    </div>
    <div class="filters">
      <div class="row">
        <div class="hidden-xs hidden-sm col-md-1"></div>
        <div class="col-xs-3">
          <div class="input-group treeselect-noborder-left">
            <span class="input-group-addon">
              <span class="hidden-xs hidden-sm">Мониторинг</span>
              <i class="fas fa-search visible-xs visible-sm"></i>
            </span>
            <treeselect
              :multiple="false"
              :disable-branch-nodes="true"
              :options="monitorings"
              placeholder="Мониторинг не выбран"
              v-model="research"
            />
          </div>
        </div>
        <div class="col-xs-6 col-md-5">
          <div class="input-group">
            <span class="input-group-addon">Дата<span class="hidden-xs hidden-sm"> или начало периода</span></span>
            <input class="form-control" type="date" v-model="date" />
            <span class="input-group-addon">Час</span>
            <select class="form-control" v-model="hour">
              <option v-for="h in HOURS" :key="h.id" :value="h.id">{{ h.label }}</option>
            </select>
          </div>
        </div>
        <div class="col-xs-3">
          <button class="btn btn-blue-n" @click="load_data" :disabled="research === null" ref="loadButton">
            Загрузить<span class="hidden-sm hidden-xs"> данные</span>
          </button>

          <button
            class="btn btn-blue-n"
            @click="print_data"
            :disabled="!data"
            title="Сохранение отображённых данных в XLSX"
            v-tippy
          >
            <i class="fas fa-download"></i>
          </button>
        </div>
      </div>
    </div>
    <div class="scroll-container" v-if="data">
      <table class="table table-bordered table-condensed table-striped">
        <colgroup>
          <col style="width: 220px" />
          <col style="width: 85px" />
        </colgroup>
        <thead v-if="data.rows.length > 0">
          <tr>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
          </tr>
          <tr>
            <th>Организация</th>
            <th>№</th>
          </tr>
        </thead>
        <tbody v-if="data.rows.length > 0">
          <tr v-for="(r, i) in data.rows" :key="i">
            <td :title="`${r.hospTitle} – ${r.confirm}`" v-tippy>
              {{ r.hospTitle }}
            </td>
            <td>
              {{ r.direction }}
            </td>
          </tr>
          <tr v-if="data.total && data.total.length > 0">
            <th colspan="2" class="text-right">Итого</th>
          </tr>
        </tbody>
        <thead v-if="data.rows.length > 0">
          <tr>
            <th>Организация</th>
            <th>№</th>
          </tr>
          <tr>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
          </tr>
        </thead>
        <tbody v-if="data.empty_hospital.length > 0">
          <tr v-for="(h, i) in data.empty_hospital" :key="`empty_${i}`">
            <th :title="h" v-tippy>{{ h }}</th>
            <th>пусто</th>
          </tr>
        </tbody>
      </table>
      <table
        class="table table-bordered table-condensed table-striped"
        :style="`width: ${140 * data.titles.reduce((a, b) => a + b.fields.length, 0)}px;`"
      >
        <colgroup>
          <template v-for="(t, i) in data.titles">
            <col v-for="(f, j) in t.fields" :key="`${i}_${j}`" width="140" />
          </template>
        </colgroup>
        <thead v-if="data.rows.length > 0">
          <tr>
            <th
              v-for="(t, i) in data.titles"
              :key="i"
              :colspan="t.fields.length"
              class="param-title group-start group-end"
              :title="t.groupTitle"
              v-tippy
            >
              {{ t.groupTitle }}
            </th>
          </tr>
          <tr>
            <template v-for="(t, i) in data.titles">
              <th
                v-for="(f, j) in t.fields"
                :key="`${i}_${j}`"
                class="param-title"
                :class="[j === 0 && 'group-start', j + 1 === t.fields.length && 'group-end']"
                :title="`${t.groupTitle} — ${f}`"
                v-tippy
              >
                {{ f }}
              </th>
            </template>
          </tr>
        </thead>
        <tbody v-if="data.rows.length > 0">
          <tr v-for="(r, i) in data.rows" :key="i">
            <template v-for="(v, j) in r.values">
              <td
                v-for="(rv, k) in v"
                :key="`${i}_${j}_${k}`"
                :class="[k === 0 && 'group-start', k + 1 === v.length && 'group-end']"
                :title="`${data.titles[j].groupTitle} — ${data.titles[j].fields[k]}: ${rv}`"
                v-tippy
              >
                {{ rv }}
              </td>
            </template>
          </tr>
          <tr v-if="data.total && data.total.length > 0">
            <template v-for="(v, j) in data.total">
              <td
                v-for="(rv, k) in v"
                :key="`total_${j}_${k}`"
                :class="[k === 0 && 'group-start', k + 1 === v.length && 'group-end']"
                :title="`Итого — ${data.titles[j].groupTitle} — ${data.titles[j].fields[k]}: ${rv}`"
                v-tippy
              >
                {{ rv }}
              </td>
            </template>
          </tr>
        </tbody>
        <thead v-if="data.rows.length > 0">
          <tr>
            <template v-for="(t, i) in data.titles">
              <th
                v-for="(f, j) in t.fields"
                :key="`${i}_${j}`"
                class="param-title"
                :class="[j === 0 && 'group-start', j + 1 === t.fields.length && 'group-end']"
                :title="`${t.groupTitle} — ${f}`"
                v-tippy
              >
                {{ f }}
              </th>
            </template>
          </tr>
          <tr>
            <th
              v-for="(t, i) in data.titles"
              :key="i"
              :colspan="t.fields.length"
              class="param-title group-start group-end"
              :title="t.groupTitle"
              v-tippy
            >
              {{ t.groupTitle }}
            </th>
          </tr>
        </thead>
        <tbody v-if="data.titles.reduce((a, b) => a + b.fields.length, 0) > 0 && data.empty_hospital.length > 0">
          <tr v-for="(h, i) in data.empty_hospital" :key="`empty_${i}`">
            <td :colspan="data.titles.reduce((a, b) => a + b.fields.length, 0)">&nbsp;</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script lang="ts">
import { mapGetters } from 'vuex';
import moment from 'moment';
import axios from 'axios';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import api from '@/api';
import * as actions from '@/store/action-types';
import * as Cookies from 'es-cookie';

const HOURS = [{ id: '-', label: 'нет' }];

for (let i = 0; i < 24; i++) {
  const id = i < 10 ? `0${i}` : String(i);
  const label = `${id}:00`;
  HOURS.push({ id, label });
}

const MIN_FONT = 9;
const MAX_FONT = 14;

export default {
  components: {
    Treeselect,
  },
  data() {
    return {
      title: 'Просмотр мониторингов',
      research: null,
      loadedResearch: null,
      date: moment().format('YYYY-MM-DD'),
      loadedDate: '',
      hour: '-',
      HOURS,
      data: null,
      fontSize: 11,
    };
  },
  async mounted() {
    await this.$store.dispatch(actions.INC_LOADING);
    await this.$store.dispatch(actions.GET_RESEARCHES);
    await this.$store.dispatch(actions.DEC_LOADING);
  },
  computed: {
    ...mapGetters(['researches']),
    monitorings() {
      return (this.researches['-12'] || []).map(r => ({ id: r.pk, label: r.title }));
    },
    canIncFont() {
      return this.fontSize < MAX_FONT;
    },
    canDecFont() {
      return this.fontSize > MIN_FONT;
    },
  },
  methods: {
    async load_data() {
      await this.$store.dispatch(actions.INC_LOADING);
      this.loadedResearch = this.research;
      this.loadedDate = this.date;
      const { rows } = await api('/monitorings/search', this, ['research', 'date', 'hour']);
      this.data = rows;
      await this.$store.dispatch(actions.DEC_LOADING);
      if (this.$refs.loadButton) {
        window.$(this.$refs.loadButton).blur();
      }
    },
    incFont() {
      this.fontSize = Math.min(MAX_FONT, this.fontSize + 1);
    },
    decFont() {
      this.fontSize = Math.max(MIN_FONT, this.fontSize - 1);
    },
    print_data() {
      axios({
        method: 'post',
        url: '/api/monitorings/filexlsx',
        data: {
          research: this.loadedResearch,
          date: this.loadedDate,
          data: this.data,
        },
        responseType: 'blob',
        headers: {
          'X-CSRFToken': Cookies.get('csrftoken'),
        },
      })
        .then(response => {
          const blob = new Blob([response.data], { type: 'application/ms-excel' });
          const downloadUrl = window.URL.createObjectURL(blob);
          let filename = '';
          const disposition = response.headers['content-disposition'];
          if (disposition && disposition.indexOf('attachment') !== -1) {
            const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
            const matches = filenameRegex.exec(disposition);
            if (matches != null && matches[1]) {
              filename = matches[1].replace(/['"]/g, '');
            }
          }
          const a = document.createElement('a');
          if (typeof a.download === 'undefined') {
            window.location.href = downloadUrl;
          } else {
            a.href = downloadUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
          }
        })
        .catch(error => {
          console.error(error);
          this.$root.$emit('msg', 'error', 'Сохранить данные в виде XLSX не удалось');
        });
    },
  },
};
</script>

<style scoped lang="scss">
.report-root {
  position: absolute;
  top: 36px;
  left: 10px;
  right: 10px;
  bottom: 0;
}

.filters {
  margin-bottom: 10px;

  .row {
    margin-left: 0;
    margin-right: 0;
  }
}

.scroll-container {
  white-space: nowrap;
  overflow-x: auto;
  overflow-y: auto;
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: start;
  justify-content: start;
  margin-left: -10px;
  margin-right: -10px;
  position: absolute;
  top: 125px;
  left: 0;
  right: 0;
  bottom: 0;

  table {
    table-layout: fixed;
    background: #fff;

    thead {
      font-size: 12px;
    }

    &:first-child {
      width: 305px;
      position: sticky;
      margin-left: 10px;
      z-index: 102;
      left: 0;

      thead {
        th {
          z-index: 102 !important;
        }
      }
    }

    &:last-child {
      border-left: none;

      tr {
        td:first-child,
        th:first-child {
          border-left: none;
        }
      }
    }

    &,
    td,
    th {
      font-size: var(--font-size-mon, 12px);
      word-break: keep-all;
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow-x: hidden;
    }

    td,
    th {
      transition: 0.15 all linear;
      &:hover {
        background-color: rgba(#049372, 0.1);
      }
    }
  }
}

.group-start {
  border-left-width: 3px;
}

.group-end {
  border-right-width: 3px;
}

.font-settings {
  font-weight: bold;
}
</style>
