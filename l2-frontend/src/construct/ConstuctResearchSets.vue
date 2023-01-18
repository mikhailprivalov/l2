<template>
  <div>
    <h4>
      Наборы
    </h4>
    <Treeselect
      v-model="currentSet"
      :options="sets.data"
      placeholder="Выберите набор"
      value-format="object"
    />
    <div class="title-set">
      <table class="table">
        <colgroup>
          <col>
          <col
            v-if="setIsSelected"
            width="40"
          >
          <col
            v-if="!setIsHidden"
            width="100"
          >
        </colgroup>
        <tr>
          <td class="border">
            <input
              v-model.trim="titleSet"
              class="form-control b"
            >
          </td>
          <td
            v-if="setIsSelected"
            class="border"
          >
            <div class="button">
              <button
                v-tippy
                class="btn last btn-blue-nb nbr"
                :title="setIsHidden ? 'Отменить скрытие' : 'Скрыть набор'"
                @click="updateSetHiding"
              >
                <i :class="setIsHidden ?'fa fa-eye' : 'fa fa-times'" />
              </button>
            </div>
          </td>
          <td
            v-if="!setIsHidden"
            class="border"
          >
            <div class="button">
              <button
                v-tippy
                class="btn last btn-blue-nb nbr"
                :title="setIsSelected ? 'Сохранить набор' : 'Добавить набор'"
                :disabled="!titleSet"
                @click="updateSet"
              >
                {{ setIsSelected ? 'Сохранить' : 'Добавить' }}
              </button>
            </div>
          </td>
        </tr>
      </table>
    </div>
    <h4 v-if="setIsSelected">
      Исследования
    </h4>
    <div
      v-if="setIsSelected"
      class="card-no-hover card card-1"
    >
      <div class="scroll">
        <table class="table">
          <colgroup>
            <col
              v-if="!setIsHidden"
              width="85"
            >
            <col>
          </colgroup>
          <tr
            v-if="researchesInSet.length === 0"
            class="text-center"
          >
            <td
              colspan="2"
            >
              Нет данных
            </td>
          </tr>
          <tr
            v-for="(i) in researchesInSet"
            :key="i.id"
          >
            <td
              v-if="!setIsHidden"
              class="border"
            >
              <div class="button">
                <button
                  class="btn last btn-blue-nb nbr"
                  :disabled="isFirstRow(i.order)"
                  @click="updateOrder(i, 'inc_order')"
                >
                  <i class="glyphicon glyphicon-arrow-up" />
                </button>
                <button
                  class="btn last btn-blue-nb nbr"
                  :disabled="isLastRow(i.order)"
                  @click="updateOrder(i, 'dec_order')"
                >
                  <i class="glyphicon glyphicon-arrow-down" />
                </button>
              </div>
            </td>
            <VueTippyTd
              class="research border padding-left"
              :text="i.research.label"
            />
          </tr>
        </table>
      </div>
    </div>
    <h4 v-if="setIsSelected && !setIsHidden">
      Добавить исследование в набор
    </h4>
    <div v-if="setIsSelected && !setIsHidden">
      <table>
        <colgroup>
          <col>
          <col width="100">
        </colgroup>
        <tr>
          <td>
            <Treeselect
              v-model="currentResearch"
              :options="researches.data"
              :disable-branch-nodes="true"
              :append-to-body="true"
              placeholder="Исследование"
              class="nba"
            />
          </td>
          <td>
            <div class="button">
              <button
                v-tippy
                class="btn last btn-blue-nb nbr"
                title="Добавить исследование"
                :disabled="!currentResearch"
                @click="addResearchInSet"
              >
                Добавить
              </button>
            </div>
          </td>
        </tr>
      </table>
    </div>
  </div>
</template>

<script lang="ts">

import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import VueTippyTd from '@/construct/VueTippyTd.vue';
import * as actions from '@/store/action-types';

export default {
  name: 'ConstuctResearchSets',
  components: { Treeselect, VueTippyTd },
  data() {
    return {
      currentSet: null,
      currentResearch: null,
      sets: [],
      titleSet: '',
      hideStatus: false,
      researchesInSet: [],
      researches: [],
    };
  },
  computed: {
    setIsSelected() {
      return !!this.currentSet;
    },
    setIsHidden() {
      return this.hideStatus.ok;
    },
    min_max_order() {
      let min = 0;
      let max = 0;
      for (const row of this.researchesInSet) {
        if (min === 0) {
          min = row.order;
        } else {
          min = Math.min(min, row.order);
        }
        max = Math.max(max, row.order);
      }
      return { min, max };
    },
  },
  watch: {
    currentSet() {
      if (!this.currentSet) {
        this.titleSet = '';
      } else {
        this.checkSetHidden();
        this.getResearchesInSet();
        this.titleSet = this.currentSet.label;
      }
    },
  },
  mounted() {
    this.getSets();
    this.getResearches();
  },
  methods: {
    async checkSetHidden() {
      if (this.setIsSelected) {
        this.hideStatus = await this.$api('/check-set-hidden', this.currentSet.id);
      }
    },
    async updateOrder(research, action) {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await this.$api('/update-order-in-set', {
        id: research.id, set: this.currentSet.id, order: research.order, action,
      });
      await this.$store.dispatch(actions.DEC_LOADING);
      if (ok) {
        this.$root.$emit('msg', 'ok', 'Порядок изменён');
        await this.getResearchesInSet();
      } else {
        this.$root.$emit('msg', 'error', message);
      }
    },
    isFirstRow(order) {
      return order === this.min_max_order.max;
    },
    isLastRow(order) {
      return order === this.min_max_order.min;
    },
    async getSets() {
      this.sets = await this.$api('/get-research-sets');
    },
    async getResearches() {
      this.researches = await this.$api('/get-research-list');
    },
    async getResearchesInSet() {
      const researches = await this.$api('/get-researches-in-set', this.currentSet.id);
      this.researchesInSet = researches.data;
    },
    async addResearchInSet() {
      if (this.researchesInSet.find((i) => i.research.id === this.currentResearch)) {
        this.$root.$emit('msg', 'error', 'Такое исследование уже есть');
      } else {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('/add-research-in-set', {
          set: this.currentSet.id,
          research: this.currentResearch,
          minOrder: this.min_max_order.min,
        });
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Исследование добавлено');
          await this.getResearchesInSet();
          this.currentResearch = null;
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      }
    },
    async updateSet() {
      if (this.setIsSelected) {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('/update-research-set', {
          id: this.currentSet.id,
          label: this.titleSet,
        });
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Набор изменён');
          await this.getSets();
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      } else {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('/update-research-set', {
          id: -1,
          label: this.titleSet,
        });
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Набор добавлен');
          await this.getSets();
          this.titleSet = '';
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      }
    },
    async updateSetHiding() {
      if (!this.setIsHidden) {
        try {
          await this.$dialog.confirm('Подтвердите скрытие набора');
        } catch (_) {
          return;
        }
      }
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await this.$api('/update-set-hiding', this.currentSet.id);
      await this.$store.dispatch(actions.DEC_LOADING);
      if (ok) {
        if (!this.setIsHidden) {
          this.$root.$emit('msg', 'ok', 'Набор скрыт');
        } else {
          this.$root.$emit('msg', 'ok', 'Скрытие отменено');
        }
        await this.checkSetHidden();
      } else {
        this.$root.$emit('msg', 'error', message);
      }
    },
  },
};
</script>

<style scoped>
::v-deep .form-control {
  border: 0;
}
::v-deep .card {
  margin: 0;
}
.title-set {
  margin: 10px 0;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
.scroll {
  min-height: 112px;
  max-height: calc(100vh - 400px);
  overflow-y: auto;
}
.border {
  border: 1px solid #ddd;
  border-radius: 0;
}
.table > thead > tr > th {
  border-bottom: 0;
}
.research {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  height: 37px;
}
.padding-left {
  padding-left: 6px;
}
.button {
  width: 100%;
  display: flex;
  flex-wrap: nowrap;
  flex-direction: row;
  justify-content: stretch;
}
  .btn {
    align-self: stretch;
    flex: 1;
    padding: 7px 0;
  }
</style>
