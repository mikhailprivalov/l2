<template>
  <div class="d-root">
    <div class="top-pane">
      <div style="float: right;">
        <button
          type="button"
          class="btn btn-primary-nb btn-ell"
          @click="showJournal = true"
        >
          Отчёт
        </button>
      </div>
      <div
        class="btn-group btn-group-justified"
        style="margin-bottom: 10px; width: 50%"
      >
        <div
          v-if="!showManualSelectGetTime"
          class="btn-group"
        >
          <a
            type="button"
            class="btn btn-primary-nb btn-ell"
            target="_blank"
            :href="historyUrl"
          >Печать</a>
        </div>
        <div
          v-if="showManualSelectGetTime"
          class="btn-group"
        >
          <a
            type="button"
            class="btn btn-primary-nb btn-ell"
            target="_blank"
            :href="actUrl"
          >Акт</a>
        </div>
        <div class="btn-group">
          <button
            type="button"
            class="btn btn-blue-nb btn-ell"
            @click="load()"
          >
            Обновить
          </button>
        </div>
      </div>
    </div>
    <div
      v-if="loading"
      class="preloader"
    >
      <i class="fa fa-spinner" /> загрузка
    </div>
    <table
      v-else
      class="table table-bordered table-hover table-condensed"
    >
      <colgroup>
        <col style="width: 70px">
        <col style="width: 80px">
        <col style="width: 80px">
        <col style="width: 200px">
        <col>
        <col style="width: 25px">
      </colgroup>
      <thead>
        <tr>
          <th>Время</th>
          <th>Напр.</th>
          <th>Ёмкость</th>
          <th>Тип</th>
          <th>Исследования</th>
          <td
            :key="`check_confirm_${globalCheckConfirm}`"
            class="x-cell"
          >
            <label @click.prevent="toggleGlobalCheckConfirm">
              <input
                type="checkbox"
                :checked="globalCheckConfirm"
              >
            </label>
          </td>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="t in tubes"
          :key="`${t.pk}_${t.checked}`"
          :class="highlightedPks && highlightedPks.includes(t.pk) && 'row-active'"
        >
          <td>{{ t.time }}</td>
          <td>{{ t.direction }}</td>
          <td>{{ t.pk }}</td>
          <td>
            <ColorTitled
              :color="t.color"
              :title="t.title"
            />
          </td>
          <td>{{ t.researches }}</td>
          <td class="x-cell">
            <label>
              <input
                v-model="t.checked"
                type="checkbox"
              >
            </label>
          </td>
        </tr>
      </tbody>
    </table>

    <transition name="fade">
      <JournalGetMaterial
        v-if="showJournal"
        :users="currentUser"
        @close="showJournal = false"
      />
    </transition>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import moment from 'moment/moment';

import ColorTitled from '@/ui-cards/ColorTitled.vue';
import JournalGetMaterial from '@/modals/JournalGetMaterial.vue';

@Component({
  components: {
    ColorTitled,
    JournalGetMaterial,
  },
  data() {
    return {
      tubes: [],
      highlightedPks: null,
      loading: false,
      showJournal: false,
    };
  },
  mounted() {
    this.load();
    this.$root.$on('load-tubes', pks => this.load(pks));
  },
})
export default class BiomaterialHistory extends Vue {
  loading: boolean;

  tubes: any[];

  highlightedPks: any[] | null;

  showJournal: boolean;

  get showManualSelectGetTime() {
    return !!this.$store.getters.modules.show_manual_select_get_time;
  }

  get historyUrl() {
    const checked = this.tubes.filter(t => t.checked).map(t => t.pk);

    if (checked.length === 0) {
      return '/direction/researches/update/history/print';
    }

    return `/direction/researches/update/history/print?filter=${JSON.stringify(checked)}`;
  }

  get actUrl() {
    const checked = this.tubes.filter(t => t.checked).map(t => t.pk);
    if (checked.length === 0) {
      return '/direction/researches/update/history/print';
    }

    return `/forms/pdf?type=114.01&filter=${JSON.stringify(checked)}`;
  }

  async load(pks = null) {
    this.loading = !pks;
    const { rows } = await this.$api('/directions/tubes-get-history', { pks });
    if (pks) {
      this.tubes = [...rows, ...this.tubes];
    } else {
      this.tubes = rows;
    }
    this.loading = false;
    this.highlightedPks = pks;
  }

  get globalCheckConfirm() {
    return this.tubes.every(t => t.checked);
  }

  toggleGlobalCheckConfirm() {
    const newChecked = !this.globalCheckConfirm;

    this.tubes = this.tubes.map(t => ({ ...t, checked: newChecked }));
  }

  get currentUser() {
    const { doc_pk: pk, fio } = this.$store.getters.user_data;
    return [{ pk, fio }];
  }
}
</script>

<style lang="scss" scoped>
.d-root {
  padding: 5px;
}

.top-pane {
  margin-bottom: 10px;
}

.row-active {
  background-color: rgba(#049372, 0.14);
}
</style>
