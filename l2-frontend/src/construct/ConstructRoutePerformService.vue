<template>
  <div>
    <table
      class="table table-bordered table-condensed table-sm-pd"
      style="table-layout: fixed; font-size: 12px; margin-bottom: 0"
    >
      <colgroup>
        <col width="500">
        <col>
        <col width="37">
      </colgroup>
      <thead>
        <tr>
          <th>Услуга</th>
          <th>Исполнитель</th>
          <th />
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(val, index) in tbData"
          :key="index"
        >
          <td class="cl-td">
            <Treeselect
              v-model="val.researchId"
              class="treeselect-noborder treeselect-32px"
              :multiple="false"
              :options="researches"
              :disable-branch-nodes="true"
              :append-to-body="true"
              placeholder="Не выбрана"
              @input="checkUniqueResearch"
            />
          </td>
          <td class="cl-td">
            <Treeselect
              v-model="val.planExternalPerformerId"
              class="treeselect-noborder treeselect-32px"
              :multiple="false"
              :options="performerHospitals"
              :disable-branch-nodes="true"
              :append-to-body="true"
              placeholder="Не выбран"
            />
          </td>
          <td class="text-center cl-td">
            <button
              v-tippy="{ placement: 'bottom' }"
              class="btn btn-blue-nb"
              title="Удалить строку"
              @click="delete_row(index)"
            >
              <i class="fa fa-times" />
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <div
      class="flex add-row-div"
    >
      <button
        v-tippy="{ placement: 'bottom' }"
        class="btn btn-blue-nb add-row margin-button"
        title="Добавить строку"
        type="button"
        @click="add_new_row"
      >
        Добавить
      </button>
      <button
        class="btn btn-blue-nb add-row margin-button"
        :disabled="disabledButtons"
        @click="saveResearchPerformer(tbData)"
      >
        Сохранить
      </button>
    </div>
  </div>
</template>

<script lang="ts">
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import Treeselect from '@riophae/vue-treeselect';

import * as actions from '@/store/action-types';

const makeDefaultRow = (researchId = null) => ({ researchId });
export default {
  name: 'ConstructRoutePerformservice',
  components: { Treeselect },
  data() {
    return {
      rows: [],
      tbData: [makeDefaultRow()],
      researches: [],
      performerHospitals: [],
    };
  },
  mounted() {
    this.getResearchList();
    this.getperformerHospitals();
    this.load_data();
  },
  methods: {
    add_new_row() {
      this.tbData.push(makeDefaultRow(null));
    },
    delete_row(index) {
      this.tbData.splice(index, 1);
    },
    async getResearchList() {
      const result = await this.$api('/get-research-list');
      this.researches = result.data;
    },
    async getperformerHospitals() {
      const result = await this.$api('hospitals/external-performer');
      this.performerHospitals = result.data;
    },
    checkUniqueResearch() {
      const currentResearch = this.tbData.map((v) => v.researchId);
      const setcurrentResearch = new Set(currentResearch);
      this.disabledButtons = currentResearch.length !== setcurrentResearch.size;
    },
    async saveResearchPerformer(tbData) {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await this.$api('researches/research-performer-save', {
        tb_data: tbData,
      });
      if (ok) {
        this.$root.$emit('msg', 'ok', message);
      } else {
        this.$root.$emit('msg', 'error', message);
      }
      await this.load_data();
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async load_data() {
      await this.$store.dispatch(actions.INC_LOADING);
      this.tbData = await this.$api('researches/get-research-performer');
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style scoped>

.add-row-div {
  justify-content: flex-end;
  padding-top: 10px;
}

.flex {
  display: flex;
}
.margin-button {
  margin-left: 10px;
}
</style>
