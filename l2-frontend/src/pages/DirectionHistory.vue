<template>
  <div>
    <div class="row print-hide">
      <div class="col-xs-12 col-sm-12 col-md-2 col-lg-3" />
      <div class="col-xs-12 col-sm-12 col-md-8 col-lg-6">
        <div class="input-group">
          <input
            v-model.trim="q"
            type="text"
            class="form-control"
            spellcheck="false"
            maxlength="15"
            autofocus
            placeholder="Введите номер направления"
            @keypress.enter="search"
          >
          <span class="input-group-btn">
            <button
              class="btn btn-blue-nb"
              type="button"
              :disabled="!q"
              @click="search"
            >Загрузить направление</button>
          </span>
        </div>
      </div>
      <div class="col-xs-12 col-sm-12 col-md-2 col-lg-3" />
    </div>
    <div class="row">
      <div class="col-xs-12 col-sm-12 col-md-1 col-lg-2" />
      <div class="col-xs-12 col-sm-12 col-md-10 col-lg-8">
        <div
          v-if="rows.length > 0"
          class="direction-history"
        >
          <div
            v-for="(r, i) in rows"
            :key="`hg-${i}`"
            class="history-group"
          >
            <div class="history-group-header">
              {{ r.type }}
            </div>
            <div
              v-if="r.events.length > 0"
              class="events"
            >
              <div
                v-for="(e, j) in r.events"
                :key="`e-${j}`"
                class="event"
              >
                <div
                  v-for="(d, k) in e"
                  v-if="/* eslint-disable-line vue/no-use-v-if-with-v-for */ d[0] === 'title' && d[1]"
                  :key="`d-${k}`"
                  class="event-title"
                >
                  <i class="fa fa-history" /> {{ d[1] }}
                </div>
                <div
                  v-if="e.length > 1"
                  class="event-data"
                >
                  <div
                    v-for="(d, k) in e"
                    v-if="/* eslint-disable-line vue/no-use-v-if-with-v-for */ d[0] !== 'title' && d[1]"
                    :key="`d-${k}`"
                    class="data-row"
                  >
                    <pre
                      v-if="d[0] === 'json_data'"
                      v-html="/* eslint-disable-line vue/no-v-html */ toJsonData(d[1])"
                    />
                    <template v-else>
                      <span class="data-title">{{ d[0] }}:</span> <span class="data-value">{{ d[1] }}</span>
                    </template>
                  </div>
                </div>
              </div>
            </div>
            <template v-else>
              Нет действий
            </template>
          </div>
        </div>
      </div>
      <div class="col-xs-12 col-sm-12 col-md-1 col-lg-2" />
    </div>
  </div>
</template>

<script lang="ts">
import * as actions from '@/store/action-types';

function syntaxHighlight(v) {
  const json = v.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  // eslint-disable-next-line max-len
  return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g, (match) => {
    let cls = 'number';
    if (/^"/.test(match)) {
      if (/:$/.test(match)) {
        cls = 'key';
      } else {
        cls = 'string';
      }
    } else if (/true|false/.test(match)) {
      cls = 'boolean';
    } else if (/null/.test(match)) {
      cls = 'null';
    }
    return `<span class="${cls}">${match}</span>`;
  });
}

export default {
  name: 'DirectionHistory',
  data() {
    return {
      q: '',
      rows: [],
    };
  },
  watch: {
    q() {
      this.q = this.q.replace(/[^0-9]/g, '');
    },
  },
  methods: {
    async search() {
      await this.$store.dispatch(actions.INC_LOADING);
      this.rows = await this.$api('/directions/direction-history', this, 'q');
      if (this.rows.length === 0) {
        this.$root.$emit('msg', 'error', 'Направление не найдено!');
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    toJsonData(t) {
      let v;
      try {
        const par = JSON.parse(t.replaceAll("{'", '{"').replaceAll("':", '":'));
        // eslint-disable-next-line max-len
        v = syntaxHighlight(JSON.stringify(((Object.prototype.toString.call(par) === '[object Array]') ? par.filter((n) => n !== undefined) : par), null, 2));
      } catch (e) {
        v = syntaxHighlight(t);
      }

      return v;
    },
  },
};
</script>

<style lang="scss" scoped>
.direction-history {
  margin-top: 10px;
  padding: 10px;
  border-radius: 5px;
  background-color: #434A54;
}

.history-group {
  padding: 10px;
  background-color: #ECF0F1;
  border-radius: 5px;

  &:not(:last-child) {
    margin-bottom: 10px;
  }

  &-header{
    font-weight: bold;
    font-size: 17px;
    margin-bottom: 5px;
  }
}

.event:not(:last-child) {
  margin-bottom: 10px;
}

.event {
  background-color: #fff;
  padding: 5px;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, .2);

  pre {
    margin-bottom: 0;
  }
}

.event-title {
  font-weight: bold;
}

@media print {
  .print-hide{
    display: none;
  }
}
</style>

<style lang="scss">
.string {
  color: green;
}

.number {
  color: darkorange;
}

.boolean {
  color: blue;
}

.null {
  color: magenta;
}

.key {
  color: red;
}
</style>
