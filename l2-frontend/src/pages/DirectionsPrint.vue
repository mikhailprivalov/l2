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
            @keypress.enter="add"
          >
          <span class="input-group-btn">
            <button
              class="btn btn-blue-nb"
              type="button"
              :disabled="!q"
              @click="add"
            >Добавить</button>
          </span>
        </div>
      </div>
      <div class="col-xs-12 col-sm-12 col-md-2 col-lg-3" />
    </div>
    <div class="dir-cont">
      <span
        v-for="d in directionsPks"
        :key="d"
        class="badge badge-default"
        @click="removeDirection(d)"
      >{{ d }}</span>
      <template v-if="!hasDirections">
        Ничего не выбрано
      </template>
    </div>
    <div
      v-if="hasDirections"
      class="row"
    >
      <div class="col-xs-1 col-md-4" />
      <div
        id="print_container"
        class="col-xs-10 col-md-4"
      >
        <button
          class="btn btn-primary-nb mw btn-block"
          type="button"
          @click="printDirections"
        >
          Печать выбранных
        </button>
        <button
          class="btn btn-primary-nb mw btn-block"
          type="button"
          @click="printResults"
        >
          Печать результатов (если доступны)
        </button>
        <button
          class="btn btn-primary-nb mw btn-block"
          type="button"
          @click="printBarcodes"
        >
          Печать штрих-кодов
        </button>
        <button
          class="btn btn-primary-nb btn-primary-rm mw btn-block"
          style="margin-top: 15px"
          type="button"
          @click="clearAll"
        >
          Очистить
        </button>
      </div>
      <div class="col-xs-1 col-md-4" />
    </div>
  </div>
</template>

<script lang="ts">
import * as actions from '@/store/action-types';

const MAX_PER_ONE_ADD = 16;
const MAX_ALL = 16;

export default {
  name: 'DirectionsPrint',
  data() {
    return {
      q: '',
      directions: {},
    };
  },
  computed: {
    directionsPks() {
      return Object.keys(this.directions).filter(d => !!this.directions[d]).map(Number);
    },
    hasDirections() {
      return this.directionsPks.length > 0;
    },
  },
  watch: {
    q() {
      this.q = this.q.replace(/[^0-9-]/g, '');
    },
  },
  methods: {
    async add() {
      const pks = [];

      let [f, t] = this.q.split('-');

      f = Number(f);
      t = Number(t);

      if (f && t) {
        if (t - f + 1 > MAX_PER_ONE_ADD) {
          this.$root.$emit('msg', 'error', `Невозможно добавить более, чем ${MAX_PER_ONE_ADD} направлений одновременно`);
          return;
        }
      }

      t = t || f;

      if ((t - f) + 1 + this.directionsPks.length > MAX_ALL) {
        this.$root.$emit('msg', 'error', `Невозможно добавить более ${MAX_PER_ONE_ADD} направлений`);
        return;
      }

      for (let i = f; i <= t; i++) {
        pks.push(i);
      }

      if (pks.length === 0) {
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      for (const pk of pks) {
        const { ok } = await this.$api('/directions/check-direction', { q: pk });
        if (ok) {
          this.directions = { ...this.directions, [pk]: true };
        } else {
          this.$root.$emit('msg', 'error', `Направление ${pk} не найдено`);
        }
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    removeDirection(d) {
      this.directions = { ...this.directions, [d]: false };
    },
    clearAll() {
      this.directions = {};
    },
    printDirections() {
      this.$root.$emit('print:directions', this.directionsPks);
    },
    printBarcodes() {
      this.$root.$emit('print:barcodes', this.directionsPks);
    },
    printResults() {
      this.$root.$emit('print:results', this.directionsPks);
    },
  },
};
</script>

<style lang="scss" scoped>
.dir-cont {
  margin-top: 15px;
  text-align: center;
  margin-bottom: 15px;
}

.badge {
  cursor: pointer;

  & + & {
    margin-left: 5px;
  }
}

.btn-block.mw {
  margin-bottom: 5px;
}
</style>
