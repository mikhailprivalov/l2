<template>
  <div>
    <h4 class="f-h text-center">
      Журнал принятых ёмкостей
    </h4>

    <div
      class="row"
      style="display: flex"
    >
      <div class="col-xs-1" />
      <div class="col-xs-7">
        <div class="row">
          <div class="col-xs-5">
            <label for="select-group">Группа исследований</label>
          </div>
          <div class="col-xs-7">
            <Treeselect
              v-model="researchGroup"
              :multiple="false"
              :disable-branch-nodes="true"
              class="treeselect-wide"
              :options="researchGroups"
              :append-to-body="true"
              :clearable="false"
              :z-index="5001"
            />
          </div>
        </div>
        <div
          class="row"
          style="margin-top: 5px"
        >
          <div class="col-xs-5">
            <label for="start-from">Начать с </label>
          </div>
          <div class="col-xs-7">
            <input
              id="start-from"
              v-model="startFrom"
              type="number"
              name="start-from"
              class="form-control"
              min="1"
            >
          </div>
        </div>
      </div>
      <div
        class="col-xs-3"
        style="display: flex"
      >
        <button
          class="btn btn-blue-nb4"
          style="width: 100%;align-items: stretch"
          :disabled="podrazdeleniyaSelected.length === 0"
          @click="printJournal"
        >
          Печать журнала
        </button>
      </div>
    </div>
    <div
      class="row"
      style="display: flex"
    >
      <div class="col-xs-1" />
      <div class="col-xs-7">
        <div
          class="row"
          style="margin-top: 5px"
        >
          <div class="col-xs-5">
            <label for="select-otd">Отделение</label>
          </div>
          <div class="col-xs-7">
            <Treeselect
              v-model="podrazdeleniyaSelected"
              :multiple="true"
              :disable-branch-nodes="true"
              class="treeselect-wide"
              :options="podrazdeleniya"
              :append-to-body="true"
              :clearable="true"
              :z-index="5001"
              clear-all-text="Очистить"
              placeholder="Выберите отделение"
              show-count
            />
            <a
              href="#"
              class="a-under-reversedn"
              @click.prevent="selectAll"
            >выбрать все</a>
          </div>
        </div>
      </div>
      <div
        class="col-xs-3"
        style="display: flex"
      >
        <button
          class="btn btn-blue-nb4"
          style="width: 100%;align-items: stretch; margin-top: 5px; max-height: 100px;"
          :disabled="podrazdeleniyaSelected.length === 0"
          @click="printDirections"
        >
          Печать направлений
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import axios from 'axios';
import * as Cookies from 'es-cookie';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import * as actions from '@/store/action-types';

export default {
  name: 'ReceiveJournal',
  components: {
    Treeselect,
  },
  data() {
    return {
      currentLaboratory: null,
      researchGroups: [],
      researchGroup: null,
      startFrom: 1,
      podrazdeleniya: [],
      podrazdeleniyaSelected: [],
      labInited: false,
    };
  },
  watch: {
    currentLaboratory: {
      async handler() {
        if (this.currentLaboratory === null) {
          return;
        }
        await this.$store.dispatch(actions.INC_LOADING);
        const { groups } = await this.$api('researches/research-groups-by-laboratory', {
          laboratoryId: this.currentLaboratory,
        });
        this.researchGroups = groups;
        if (this.researchGroups.every((x) => x.id !== this.researchGroup)) {
          this.researchGroup = this.researchGroups[0].id;
        }
        await this.$store.dispatch(actions.DEC_LOADING);
      },
      immediate: true,
    },
  },
  async mounted() {
    await this.$store.dispatch(actions.INC_LOADING);
    this.$root.$on('change-laboratory', async (pk) => {
      this.currentLaboratory = pk;
      if (!this.labInited) {
        this.labInited = true;
        await this.$store.dispatch(actions.DEC_LOADING);
      }
    });
    this.$root.$emit('emit-laboratory');
    await this.$store.dispatch(actions.INC_LOADING);
    this.podrazdeleniya = (await this.$api('otds', { withoutDefault: true })).rows || [];
    await this.$store.dispatch(actions.DEC_LOADING);
  },
  methods: {
    selectAll() {
      this.podrazdeleniyaSelected = this.podrazdeleniya.map((x) => x.id);
    },
    getJournalUrl(withDirections = false) {
      const url = new URL('/mainmenu/receive/journal', window.location.origin);
      const params = {
        group: this.researchGroup,
        start: this.startFrom,
        otd: JSON.stringify(this.podrazdeleniyaSelected),
        lab_pk: this.currentLaboratory,
      };
      Object.keys(params).forEach((key) => {
        if (params[key]) {
          url.searchParams.append(key, params[key]);
        }
      });
      if (withDirections) {
        url.searchParams.append('return', 'directions');
      }
      return url.toString();
    },
    printJournal() {
      window.open(this.getJournalUrl(), '_blank');
    },
    async printDirections() {
      await this.$store.dispatch(actions.INC_LOADING);
      try {
        const url = this.getJournalUrl(true);
        const { data } = await axios.get(url, {
          headers: {
            'X-CSRFToken': Cookies.get('csrftoken'),
          },
        });

        this.$root.$emit('print:directions', data);
      } catch (e) {
        this.$root.$emit('msg', 'error', 'Ошибка при получении направлений');
        console.error(e);
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style lang="scss" scoped>
.btn-blue-nb4, .btn-blue-nb4:active, .btn-blue-nb4:visited, .btn-blue-nb4:focus {
  background: transparent;
  border: #049372 solid 2px;
  color: #049372
}

.btn-blue-nb4:hover {
  background: #049372;
  border: #049372 solid 2px;
  color: #fff
}
</style>
