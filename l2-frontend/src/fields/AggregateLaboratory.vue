<template>
  <div class="root-agg">
    <div
      v-for="(lab, title) in data"
      :key="`${lab}_${title}`"
    >
      <div>
        <strong>{{ title }}</strong>
      </div>
      <div
        v-if="excludedTitlesByGroup(title).length > 0"
        class="excluded"
      >
        <u><strong>Исключённые исследования:</strong></u>
        <span
          v-for="t in excludedTitlesByGroup(title)"
          :key="t"
          v-tippy="{ placement: 'top', arrow: true }"
          title="Вернуть"
          class="clickable-return"
          @click="cancelExcludeTitle(t)"
        >
          {{ getAfterGroup(t) }}
        </span>
      </div>
      <div
        v-if="excludedDateDirByGroup(title).length > 0"
        class="excluded"
      >
        <u><strong>Исключённые направления:</strong></u>
        <span
          v-for="t in excludedDateDirByGroup(title)"
          :key="t"
          v-tippy="{ placement: 'top', arrow: true }"
          title="Вернуть"
          class="clickable-return"
          @click="cancelExcludeDateDir(t)"
        >
          {{ getAfterGroup(t) }}
        </span>
      </div>
      <div
        v-for="(row, i) in lab.vertical"
        :key="i"
        class="scroll"
      >
        <div>
          <strong>{{ row.title_research }}</strong>
        </div>
        <div
          v-if="excludedTitlesByGroup(row.title_research).length > 0"
          class="excluded"
        >
          <u><strong>Исключённые фракции:</strong></u>
          <span
            v-for="t in excludedTitlesByGroup(row.title_research)"
            :key="t"
            v-tippy="{ placement: 'top', arrow: true }"
            title="Вернуть"
            class="clickable-return"
            @click="cancelExcludeTitle(t)"
          >
            {{ getAfterGroup(t) }}
          </span>
        </div>
        <div
          v-if="excludedDateDirByGroup(row.title_research).length > 0"
          class="excluded"
        >
          <u><strong>Исключённые направления:</strong></u>
          <span
            v-for="t in excludedDateDirByGroup(row.title_research)"
            :key="t"
            v-tippy="{ placement: 'top', arrow: true }"
            title="Вернуть"
            class="clickable-return"
            @click="cancelExcludeDateDir(t)"
          >
            {{ getAfterGroup(t) }}
          </span>
        </div>
        <table>
          <colgroup>
            <col width="64">
            <!-- eslint-disable-next-line vue/no-use-v-if-with-v-for -->
            <col
              v-for="t in row.title_fracions"
              v-if="!excludedTitle(t, row.title_research)"
              :key="t"
              width="52"
            >
          </colgroup>
          <thead>
            <tr>
              <th>Дата, напр.</th>
              <!-- eslint-disable-next-line vue/no-use-v-if-with-v-for -->
              <th
                v-for="t in row.title_fracions"
                v-if="!excludedTitle(t, row.title_research)"
                :key="t"
                v-tippy="{ placement: 'top', arrow: true }"
                class="clickable-td"
                title="Скрыть"
                @click="excludeTitle(t, row.title_research)"
              >
                {{ t }}
              </th>
            </tr>
          </thead>
          <tbody>
            <!-- eslint-disable-next-line vue/no-use-v-if-with-v-for -->
            <tr
              v-for="(r, dateDir) in row.result"
              v-if="!excludedDateDir(dateDir, row.title_research)"
              :key="dateDir"
            >
              <td
                v-tippy="{ placement: 'top', arrow: true }"
                class="clickable-td"
                title="Скрыть"
                @click="excludeDateDir(dateDir, row.title_research)"
              >
                {{ dateDir }}
              </td>
              <td
                v-for="(v, j) in r"
                v-if="!excludedTitleAtPos(row.title_fracions, j, row.title_research)"
                :key="j"
              >
                {{ v }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div
        v-for="(row, jj) in lab.horizontal"
        :key="jj"
        class="scroll"
      >
        <table>
          <colgroup>
            <col width="120">
            <col
              v-for="(_, dateDir) in row.result"
              v-if="/*eslint-disable-line vue/no-use-v-if-with-v-for*/ !excludedDateDir(dateDir, title)"
              :key="dateDir"
              width="64"
            >
          </colgroup>
          <thead>
            <tr>
              <th>Дата, напр.</th>
              <td
                v-for="(_, dateDir) in row.result"
                v-if="/*eslint-disable-line vue/no-use-v-if-with-v-for*/ !excludedDateDir(dateDir, title)"
                :key="dateDir"
                v-tippy="{ placement: 'top', arrow: true }"
                class="clickable-td"
                title="Скрыть"
                @click="excludeDateDir(dateDir, title)"
              >
                {{ dateDir }}
              </td>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(t, i) in row.title_fracions"
              v-if="/*eslint-disable-line vue/no-use-v-if-with-v-for*/ !excludedTitle(t, title)"
              :key="i"
            >
              <th
                v-tippy="{ placement: 'top', arrow: true }"
                class="th2 clickable-td"
                title="Скрыть"
                @click="excludeTitle(t, title)"
              >
                {{ t }}
              </th>
              <td
                v-for="(v, dateDir) in row.result"
                v-if="/*eslint-disable-line vue/no-use-v-if-with-v-for*/ !excludedDateDir(dateDir, title)"
                :key="dateDir"
              >
                {{ v[i] }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import stationarPoint from '@/api/stationar-point';

const delimiter = '#@#';

const makeKey = (t, group) => `${group}${delimiter}${t}`;

export default {
  props: {
    pk: {},
    caseDirection: {},
    extract: {
      type: Boolean,
      default: false,
    },
    value: {},
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      data: {},
      excluded: {
        dateDir: [],
        titles: [],
      },
      inited: false,
    };
  },
  computed: {
    directions() {
      const d = [];
      try {
        for (const title of Object.keys(this.data)) {
          const lab = this.data[title];
          if (Array.isArray(lab.vertical)) {
            for (const row of lab.vertical) {
              for (const dateDir of Object.keys(row.result)) {
                if (!this.excludedDateDir(dateDir, row.title_research)) {
                  d.push(parseInt(dateDir.split(' ')[1], 10));
                }
              }
            }
          }
          if (Array.isArray(lab.horizontal)) {
            for (const row of lab.horizontal) {
              for (const dateDir of Object.keys(row.result)) {
                if (!this.excludedDateDir(dateDir, title)) {
                  d.push(parseInt(dateDir.split(' ')[1], 10));
                }
              }
            }
          }
        }
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error(e);
      }
      return d;
    },
    val_data() {
      return {
        directions: this.directions,
        excluded: this.excluded,
      };
    },
  },
  watch: {
    val_data: {
      deep: true,
      handler() {
        if (this.inited) {
          this.$emit('input', JSON.stringify(this.val_data));
        }
      },
    },
    inited() {
      if (this.inited) {
        this.$emit('input', JSON.stringify(this.val_data));
      }
    },
  },
  async mounted() {
    await this.load();
    try {
      const valOrig = JSON.parse(this.value || '[]');
      if (Object.prototype.toString.call(valOrig) === '[object Object]' && valOrig.excluded) {
        this.excluded.dateDir = valOrig.excluded.dateDir || [];
        this.excluded.titles = valOrig.excluded.titles || [];
      }
    } catch (e) {
      // eslint-disable-next-line no-console
      console.log('Aggregate error:', e);
    }
    this.inited = true;
  },
  methods: {
    getAfterGroup(s) {
      return s.split(delimiter)[1];
    },
    async load() {
      this.excluded.dateDir = [];
      this.excluded.titles = [];
      if (this.caseDirection) {
        this.data = await this.$api('cases/aggregate', this, ['caseDirection'], { view: 'laboratory' });
      } else {
        this.data = await stationarPoint.aggregateLaboratory(this, ['pk', 'extract']);
      }
    },
    excludedTitle(t, group) {
      const title = makeKey(t, group);
      return this.excluded.titles.includes(title);
    },
    excludedTitleAtPos(titles, pos, group) {
      return this.excludedTitle(titles[pos], group);
    },
    excludedDateDir(t, group) {
      const title = makeKey(t, group);
      return this.excluded.dateDir.includes(title);
    },
    excludeTitle(t, group) {
      if (this.disabled) {
        return;
      }
      const title = makeKey(t, group);
      if (!this.excluded.titles.includes(title)) {
        this.excluded.titles.push(title);
      }
    },
    excludeDateDir(t, group) {
      if (this.disabled) {
        return;
      }
      const title = makeKey(t, group);
      if (!this.excluded.dateDir.includes(title)) {
        this.excluded.dateDir.push(title);
      }
    },
    cancelExcludeTitle(title) {
      if (this.disabled) {
        return;
      }
      const pos = this.excluded.titles.findIndex((v) => v === title);
      if (pos === -1) {
        return;
      }
      this.excluded.titles.splice(pos, 1);
    },
    cancelExcludeDateDir(title) {
      if (this.disabled) {
        return;
      }
      const pos = this.excluded.dateDir.findIndex((v) => v === title);
      if (pos === -1) {
        return;
      }
      this.excluded.dateDir.splice(pos, 1);
    },
    excludedTitlesByGroup(group) {
      const titleStart = makeKey('', group);
      return this.excluded.titles.filter((s) => s.startsWith(titleStart));
    },
    excludedDateDirByGroup(group) {
      const titleStart = makeKey('', group);
      return this.excluded.dateDir.filter((s) => s.startsWith(titleStart));
    },
  },
};
</script>

<style scoped lang="scss">
.root-agg {
  table {
    width: 100%;
    table-layout: fixed;
    border-collapse: collapse;
    margin-bottom: 5px;
  }

  table,
  th,
  td {
    border: 1px solid black;
  }

  th,
  td {
    word-break: break-word;
    white-space: normal;
    text-align: left;
  }

  table th:not(:first-child),
  .th2 {
    font-size: 12px;
  }

  td,
  th {
    padding: 2px;
  }
}

.clickable-td {
  cursor: pointer;

  &:hover {
    text-decoration: underline;
    background: rgba(#000, 0.05);
  }
}

.clickable-return {
  cursor: pointer;
  padding: 0 2px;
  border: 1px solid rgba(#049372, 0.4);
  border-radius: 3px;
  margin-left: 4px;
  margin-bottom: 5px;
  transition: 0.2s ease-in all;
  white-space: nowrap;
  display: inline-block;

  &:hover {
    color: #fff;
    background: #049372;
    border: 1px solid #049372;
    box-shadow: 0 7px 14px #04937254, 0 5px 5px #049372ba;
  }
}

.excluded {
  white-space: normal;
  word-break: break-word;
}

.scroll {
  overflow: auto;
}
</style>
