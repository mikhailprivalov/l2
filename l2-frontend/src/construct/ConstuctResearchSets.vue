<template>
  <div class="main">
    <div
      class="box card-no-hover card-1"
    >
      <h4 class="text-center">
        Исследования в {{ setIsSelected ? currentSet.label : '' }}
      </h4>
      <div v-if="setIsSelected">
        <table class="table">
          <colgroup>
            <col>
            <col width="50">
          </colgroup>
          <tr>
            <td class="not-bottom-border">
              <input
                v-model.trim="currentSet.label"
                class="form-control padding-left"
              >
            </td>
            <td class="not-bottom-border">
              <div class="button">
                <button
                  v-tippy
                  class="btn last btn-blue-nb nbr"
                  title="Сохранить"
                  :disabled="!currentSet.label"
                  @click="updateSet"
                >
                  <i class="fa fa-save" />
                </button>
              </div>
            </td>
          </tr>
        </table>
      </div>
      <div
        v-if="setIsSelected"
        class="scroll"
      >
        <table class="table">
          <colgroup>
            <col width="85">
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
            <td class="border">
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
      <div v-if="setIsSelected">
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
    <div class="box card-no-hover card-1">
      <h4 class="text-center">
        Наборы
      </h4>
      <div class="scroll">
        <table class="table">
          <colgroup>
            <col>
            <col width="100">
          </colgroup>
          <tr
            v-if="sets.length === 0"
            class="text-center"
          >
            <td
              colspan="2"
            >
              Нет данных
            </td>
          </tr>
          <tr
            v-for="(i) in sets.data"
            :key="i.id"
            class="border"
          >
            <VueTippyTd
              class="research border padding-left"
              :text="i.label"
            />
            <td>
              <div class="button">
                <button
                  v-tippy
                  class="btn last btn-blue-nb nbr"
                  title="Редактировать"
                  @click="getResearchesInSet(i)"
                >
                  <i class="fa fa-pencil" />
                </button>
                <button
                  v-tippy
                  class="btn last btn-blue-nb nbr"
                  title="Скрыть"
                  @click="hideSet(i.id)"
                >
                  <i class="fa fa-times" />
                </button>
              </div>
            </td>
          </tr>
        </table>
      </div>
      <div>
        <table class="table">
          <colgroup>
            <col>
            <col width="100">
          </colgroup>
          <tr>
            <td class="add-border">
              <input
                v-model.trim="newSet"
                class="form-control padding-left"
              >
            </td>
            <td class="add-border">
              <div class="button">
                <button
                  v-tippy
                  class="btn last btn-blue-nb nbr"
                  title="Добавить"
                  :disabled="!newSet"
                  @click="addSet"
                >
                  Добавить
                </button>
              </div>
            </td>
          </tr>
        </table>
      </div>
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
      newSet: '',
      setTitle: '',
      researchesInSet: [],
      researches: [],
    };
  },
  computed: {
    setIsSelected() {
      return !!this.currentSet;
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
  mounted() {
    this.getSets();
    this.getResearches();
  },
  methods: {
    async updateOrder(research, action) {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await this.$api('/update-order-in-set', {
        id: research.id, set: this.currentSet.id, order: research.order, action,
      });
      await this.$store.dispatch(actions.DEC_LOADING);
      if (ok) {
        this.$root.$emit('msg', 'ok', 'Порядок изменён');
        await this.getResearchesInSet(this.currentSet);
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
    async getResearchesInSet(currentSet) {
      const researches = await this.$api('/get-researches-in-set', currentSet.id);
      this.researchesInSet = researches.data;
      this.currentSet = currentSet;
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
          await this.getResearchesInSet(this.currentSet);
          this.currentResearch = null;
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      }
    },
    async addSet() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await this.$api('/add-research-set', { newSet: this.newSet });
      await this.$store.dispatch(actions.DEC_LOADING);
      if (ok) {
        this.$root.$emit('msg', 'ok', 'Набор добавлен');
        await this.getSets();
        this.newSet = '';
      } else {
        this.$root.$emit('msg', 'error', message);
      }
    },
    async updateSet() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await this.$api('/update-research-set', this.currentSet);
      await this.$store.dispatch(actions.DEC_LOADING);
      if (ok) {
        this.$root.$emit('msg', 'ok', 'Набор изменён');
        await this.getSets();
      } else {
        this.$root.$emit('msg', 'error', message);
      }
    },
    async hideSet(id) {
      try {
        await this.$dialog.confirm('Подтвердите скрытие набора');
      } catch (_) {
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await this.$api('/hide-research-set', id);
      await this.$store.dispatch(actions.DEC_LOADING);
      if (ok) {
        this.$root.$emit('msg', 'ok', 'Набор скрыт');
        if (id === this.currentSet.id) {
          this.currentSet = null;
          this.researchesInSet = [];
        }
        await this.getSets();
      } else {
        this.$root.$emit('msg', 'error', message);
      }
    },
  },
};
</script>

<style scoped>
.box {
  background-color: #FFF;
  margin: 10px;
  flex-basis: 350px;
  flex-grow: 1;
  border-radius: 4px;
  height: calc(100vh - 200px);
  min-height: 250px;
}
.main {
  display: flex;
  flex-wrap: wrap;
}
::v-deep .form-control {
  border: none;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
.scroll {
  min-height: 112px;
  max-height: calc(100vh - 300px);
  overflow-y: auto;
}
.border {
  border: 1px solid #ddd;
  border-radius: 0;
}
.add-border {
  border-left: 1px solid #ddd;
  border-right: 1px solid #ddd;
  border-bottom: 1px solid #ddd;
  border-radius: 0;
}
.not-bottom-border {
  border-left: 1px solid #ddd;
  border-right: 1px solid #ddd;
  border-top: 1px solid #ddd;
  border-radius: 0;
}
.table > thead > tr > th {
  border-bottom: 0;
}
.research {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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
