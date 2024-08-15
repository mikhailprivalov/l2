<template>
  <div class="b-root">
    <div class="top-search">
      <div class="confirm-list-wrapper">
        <button
          class="btn btn-primary-nb btn-ell"
          type="button"
          @click="openConfirmationList()"
        >
          Лист подтверждений
        </button>
      </div>
      <div class="input-group">
        <input
          ref="q"
          v-model="query"
          type="text"
          class="form-control"
          placeholder="Номер направления"
          autofocus
          maxlength="20"
          :readonly="loading"
          @keyup.enter="search"
        >
        <span class="input-group-btn">
          <button
            class="btn btn-blue-nb"
            type="button"
            @click="search"
          >Поиск</button>
        </span>
      </div>
    </div>

    <table class="table table-bordered table-condensed main-table">
      <colgroup>
        <col style="width: 170px">
        <col>
      </colgroup>
      <tbody>
        <tr>
          <th>Номер направления</th>
          <td class="cl-td">
            <h2 class="direction">
              <template v-if="direction">
                {{ direction.pk }}
                <template v-if="direction.full_confirm || !direction.has_not_completed || !needGlobalCheck">
                  (исполнено)
                </template>
                <template v-else-if="direction.cancel">
                  (отменено)
                </template>
              </template>
              <template v-else>
&nbsp;
              </template>
            </h2>
          </td>
        </tr>
        <tr>
          <th>Дата назначения</th>
          <td>
            {{ direction && direction.date }}
          </td>
        </tr>
        <tr>
          <th>Пациент</th>
          <td>{{ client && client.fio }}</td>
        </tr>
        <tr>
          <th>Дата рождения</th>
          <td>
            {{ client && `${client.birthday}, ${client.age}` }}
          </td>
        </tr>
        <tr>
          <th>Карта</th>
          <td>{{ client && client.card }}</td>
        </tr>
        <tr v-if="!direction || (!direction.imported_from_rmis && !direction.isExternal)">
          <th>Л/врач</th>
          <td>
            {{ direction && direction.doc.fio }}
            {{ direction && direction.doc.otd }}
          </td>
        </tr>
        <tr v-if="direction && (direction.imported_from_rmis || direction.isExternal)">
          <th>Организация</th>
          <td>{{ direction.imported_org }}</td>
        </tr>
      </tbody>
    </table>

    <div class="btn-group btn-group-justified control-buttons">
      <div
        class="btn-group"
      >
        <button
          v-if="!showManualSelectGetTime"
          v-tippy
          type="button"
          :disabled="!tubes || direction.full_confirm || !needGlobalCheck"
          class="btn btn-blue-nb3 btn-ell"
          title="Отмена направления"
          @click="cancel"
        >
          Отмена направления
        </button>
        <input
          v-if="showManualSelectGetTime"
          v-model="manualSelectGetTime"
          type="datetime-local"
          :readonly="!tubes || !hasAnyChecked"
          step="1"
          class="form-control"
        >
      </div>
      <div class="btn-group">
        <button
          v-tippy
          type="button"
          :disabled="!direction"
          class="btn btn-blue-nb3 btn-ell"
          title="Печать всех штрих-кодов направления"
          @click="printBarcodes()"
        >
          Печать штрих-кодов
        </button>
      </div>
      <div class="btn-group">
        <button
          v-tippy
          type="button"
          :disabled="!tubes || !hasAnyChecked"
          class="btn btn-blue-nb3 btn-ell"
          title="Сохранить статус забора материала"
          @click="save(false)"
        >
          Сохранить
        </button>
      </div>
      <div class="btn-group">
        <button
          v-tippy
          type="button"
          :disabled="!tubes || !hasAnyChecked"
          class="btn btn-blue-nb3 btn-ell"
          title="Печать выбранных штрих-кодов и сохранить статус забора материала"
          @click="save(true)"
        >
          Печать ш/к и сохранить
        </button>
      </div>
    </div>

    <table class="table table-bordered table-condensed tubes-table">
      <colgroup>
        <col>
        <col style="width: 225px">
        <col style="width: 112px">
        <col style="width: 25px">
      </colgroup>
      <thead>
        <tr>
          <th>Исследования</th>
          <th>Тип ёмкости</th>
          <th>Номер</th>
          <td
            :key="`check_${globalCheckStatus}`"
            class="x-cell"
          >
            <label
              v-if="!needGlobalCheck"
              class="disabled"
            >
              <i
                v-if="tubes"
                class="fas fa-check"
              />
            </label>
            <label
              v-else
              v-tippy
              title="Переключить статус забора всех неисполненных ёмкостей"
              @click.prevent="toggleGlobalCheck"
            >
              <input
                type="checkbox"
                :checked="globalCheckStatus"
              >
            </label>
          </td>
        </tr>
      </thead>
      <tbody>
        <template v-for="(tubes, lab) in tubes">
          <tr :key="lab">
            <th colspan="4">
              Лаборатория: {{ lab }}
            </th>
          </tr>
          <template v-for="t in tubes">
            <tr
              :key="t.id"
              :class="t.checked && !t.status && 'row-checked'"
            >
              <td>
                {{ t.researches.join('; ') }}
              </td>
              <td>
                <ColorTitled
                  :color="t.color"
                  :title="t.title"
                />
              </td>
              <td
                class="x-cell"
                :rowspan="!!details[t.id] ? 2 : 1"
              >
                <div class="tube_id">
                  <span>{{ t.barcode || t.id }} </span>
                  <a
                    v-tippy
                    href="#"
                    title="Печать штрих-кода этой ёмкости"
                    @click.prevent="printBarcodes(t.id)"
                  >
                    <i class="fas fa-barcode" />
                  </a>
                </div>
              </td>
              <td
                class="x-cell"
                :rowspan="!!details[t.id] ? 2 : 1"
              >
                <label :class="t.status && 'disabled'">
                  <i
                    v-if="t.status"
                    class="fas fa-check"
                  />
                  <input
                    v-else
                    v-model="t.checked"
                    type="checkbox"
                  >
                </label>
              </td>
            </tr>
            <tr
              v-if="details[t.id]"
              :key="`details-${t.id}`"
            >
              <td colspan="2">
                <div><strong>Исполнитель:</strong> {{ details[t.id].executor }}</div>
                <div><strong>Дата и время:</strong> {{ details[t.id].datetime }}</div>
              </td>
            </tr>
          </template>
        </template>
      </tbody>
    </table>

    <table
      v-if="tubes && needGlobalCheck"
      class="table table-bordered table-condensed tubes-table"
    >
      <colgroup>
        <col style="width: 70%">
        <col>
      </colgroup>
      <thead>
        <tr>
          <th>Тип</th>
          <th>Количество, отмечено</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(t, title) in typesChecked"
          :key="title"
        >
          <td>
            <ColorTitled
              :color="t.color"
              :title="title"
            />
          </td>
          <td>
            {{ t.count | pluralCount }}
          </td>
        </tr>
        <tr v-if="Object.keys(typesChecked).length === 0">
          <td
            class="text-center"
            colspan="2"
          >
            Нет
          </td>
        </tr>
        <tr v-else>
          <th class="text-right">
            Итого
          </th>
          <td>{{ typesCheckedTotal | pluralCount }}</td>
        </tr>
      </tbody>
    </table>
    <MountingPortal
      mount-to="#portal-place-modal"
      name="ConfirmListPopup"
      append
    >
      <transition name="fade">
        <modal
          v-if="showConfirmList"
          show-footer="true"
          white-bg="true"
          max-width="710px"
          width="100%"
          margin-left-right="auto"
          @close="showConfirmList = false"
        >
          <span slot="header">Лист подтверждений</span>
          <div
            slot="body"
            class="popup-body"
          >
            <div
              v-if="loading"
              class="preloader"
            >
              <i class="fa fa-spinner" /> загрузка
            </div>
            <div v-else>
              <table class="table table-bordered table-condensed table-hover">
                <colgroup>
                  <col>
                  <col style="width: 85px">
                  <col style="width: 85px">
                  <col style="width: 210px">
                  <col style="width: 25px">
                </colgroup>
                <thead>
                  <tr>
                    <th>ФИО</th>
                    <th>№ напр.</th>
                    <th>№ ёмкости</th>
                    <th>Тип</th>
                    <th
                      :key="`check_confirm_${globalCheckConfirm}`"
                      class="x-cell"
                    >
                      <label @click.prevent="toggleGlobalCheckConfirm">
                        <input
                          type="checkbox"
                          :checked="globalCheckConfirm"
                        >
                      </label>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="t in tubesForConfirm"
                    :key="`${t.pk}_${t.checked}`"
                  >
                    <td
                      class="cursor-pointer"
                      @click="t.checked = !t.checked"
                    >
                      {{ t.patient }}
                    </td>
                    <td>
                      {{ t.direction }}
                      <br><small><a
                        href="#"
                        @click.stop.prevent="cancel(t.direction)"
                      >отменить</a></small>
                    </td>
                    <td>
                      {{ t.pk }}
                      <br><small><a
                        href="#"
                        @click.stop.prevent="printBarcodes(t.pk)"
                      >печать ш/к</a></small>
                    </td>
                    <td @click="t.checked = !t.checked">
                      <ColorTitled
                        :color="t.color"
                        :title="t.title"
                      />
                    </td>
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
            </div>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-6">
                <button
                  class="btn btn-blue-nb"
                  type="button"
                  @click="showConfirmList = false"
                >
                  Закрыть
                </button>
              </div>
              <div class="col-xs-6 text-right">
                <button
                  class="btn btn-blue-nb"
                  type="button"
                  @click="saveList"
                >
                  Подтвердить выбранные
                </button>
              </div>
            </div>
          </div>
        </modal>
      </transition>
    </MountingPortal>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import { debounce } from 'lodash/function';

import * as actions from '@/store/action-types';
import ColorTitled from '@/ui-cards/ColorTitled.vue';
import Modal from '@/ui-cards/Modal.vue';
import UrlData from '@/UrlData';

@Component({
  components: {
    ColorTitled,
    Modal,
  },
  data() {
    return {
      query: '',
      hasFocus: false,
      loaded: null,
      scannerBuffer: '',
      clearTimer: null,
      client: null,
      direction: null,
      tubes: null,
      details: {},
      tubesForConfirm: [],
      loading: false,
      showConfirmList: false,
      manualSelectGetTime: null,
    };
  },
  created() {
    this.keypressHandler = e => {
      this.onKeyPress(e);
    };

    window.addEventListener('keypress', this.keypressHandler);
  },
  async mounted() {
    const storedData = UrlData.get();
    if (storedData && typeof storedData === 'object') {
      if (storedData.pk) {
        this.query = (storedData.pk).toString();
        await this.doSearch();
      }
    }
    this.inited = true;
  },
  beforeDestroy() {
    window.removeEventListener('keypress', this.keypressHandler);
  },
  watch: {
    query() {
      this.barScanner(this.query);
    },
    navState() {
      if (this.inited) {
        UrlData.set(this.navState);
      }
      UrlData.title(this.direction);
    },
  },
})
export default class BiomaterialSearch extends Vue {
  query: string;

  loaded: null | number;

  scannerBuffer: string;

  clearTimer: null | any;

  direction: any;

  client: any;

  tubes: any;

  details: any;

  loading: boolean;

  showConfirmList: boolean;

  tubesForConfirm: any[];

  manualSelectGetTime: null | any;

  onKeyPress(event) {
    if (window.$('input').is(':focus') || this.loading) {
      return;
    }

    const sym = String.fromCharCode(event.which);
    if (Number.isNaN(Number(sym))) {
      return;
    }

    clearTimeout(this.clearTimer);
    this.clearTimer = null;

    this.scannerBuffer += sym;
    this.scannerBuffer = this.scannerBuffer.replace(/\n/g, '').trim();

    if ((this.scannerBuffer.length >= 3 && this.scannerBuffer.substr(0, 3) !== '460') || this.scannerBuffer.length > 13) {
      this.scannerBuffer = '';
    } else {
      this.barScanner(this.scannerBuffer);
    }

    this.clearTimer = setTimeout(() => {
      this.scannerBuffer = '';
    }, 300);
  }

  barScanner(v) {
    if (v.substr(0, 3) === '460' && v.length === 13) {
      const parsedNumber = Number(v.substr(0, 12)) - 460000000000;
      if (this.loaded !== parsedNumber) {
        this.query = v;
        this.search();
      } else {
        this.scannerBuffer = '';
        this.clearTimer = null;
      }
    }
  }

  search = debounce(this.doSearch, 100);

  async doSearch() {
    const q = this.query.replace(/\D/g, '');
    if (q.length === 0) {
      return;
    }
    this.loading = true;
    this.scannerBuffer = '';
    this.clearTimer = null;
    await this.$store.dispatch(actions.INC_LOADING);
    const data = await this.$api('/directions/tubes-for-get', { pk: q });
    if (data.ok) {
      this.direction = data.direction;
      this.client = data.client;
      this.tubes = data.tubes;
      this.details = data.details;
    } else {
      const msg = data.message || 'Не найдено';
      this.$root.$emit('msg', 'error', `${msg}\nЗапрос: "${this.query}"`);
    }
    this.query = '';
    await this.$store.dispatch(actions.DEC_LOADING);
    this.loading = false;
  }

  get showManualSelectGetTime() {
    return !!this.$store.getters.modules.show_manual_select_get_time;
  }

  get navState() {
    if (!this.direction) {
      return null;
    }
    return {
      pk: this.direction,
    };
  }

  get needGlobalCheck() {
    for (const tubes of Object.values<any>(this.tubes || {})) {
      for (const t of Object.values<any>(tubes || {})) {
        if (!t.status) {
          return true;
        }
      }
    }

    return false;
  }

  get hasAnyChecked() {
    for (const tubes of Object.values<any>(this.tubes || {})) {
      for (const t of Object.values<any>(tubes || {})) {
        if (t.checked && !t.status) {
          return true;
        }
      }
    }

    return false;
  }

  get globalCheckStatus() {
    if (!this.needGlobalCheck) {
      return false;
    }

    for (const tubes of Object.values<any>(this.tubes || {})) {
      for (const t of Object.values<any>(tubes || {})) {
        if (!t.checked && !t.status) {
          return false;
        }
      }
    }

    return true;
  }

  get typesChecked() {
    if (!this.needGlobalCheck) {
      return {};
    }

    const r = {};

    for (const tubes of Object.values<any>(this.tubes || {})) {
      for (const t of Object.values<any>(tubes || {})) {
        if (t.checked && !t.status) {
          if (!r[t.title]) {
            r[t.title] = {
              count: 0,
              color: t.color,
            };
          }
          r[t.title].count++;
        }
      }
    }

    return r;
  }

  get typesCheckedTotal() {
    return Object.values<any>(this.typesChecked).reduce((a, b) => a + b.count, 0);
  }

  toggleGlobalCheck() {
    const newStatus = !this.globalCheckStatus;
    this.tubes = Object.entries<any>(this.tubes).reduce(
      (a, [lab, tubes]) => ({
        ...a,
        [lab]: Object.entries<any>(tubes).reduce((x, [k, v]) => ({ ...x, [k]: { ...v, checked: newStatus || v.status } }), {}),
      }),
      {},
    );
  }

  printBarcodes(tubeId = null) {
    if (tubeId) {
      window.open(`/barcodes/tubes?tubes_id=${JSON.stringify(Array.isArray(tubeId) ? tubeId : [tubeId])}`, '_blank');
    } else {
      window.open(`/barcodes/tubes?napr_id=${JSON.stringify([this.direction.pk])}`, '_blank');
    }
  }

  async cancel(pk = null) {
    try {
      await this.$dialog.confirm('Подтвердите смену статуса отмены');
    } catch (_) {
      return;
    }
    await this.$store.dispatch(actions.INC_LOADING);
    const { cancel } = await this.$api('/directions/cancel', { pk: pk || this.direction.pk });
    if (this.direction && (!pk || this.direction.pk === pk)) {
      this.direction.cancel = cancel;
    }
    await this.$store.dispatch(actions.DEC_LOADING);

    if (pk) {
      await this.openConfirmationList(true);
    }
  }

  saveList() {
    const pks = this.tubesForConfirm.filter(t => t.checked).map(t => t.pk);

    this.save(false, pks);
  }

  async save(needPrintBarcodes, toConfirmPks = null) {
    await this.$store.dispatch(actions.INC_LOADING);
    const selectGetTime = this.manualSelectGetTime;
    const pks = toConfirmPks
      || Object.values<any>(this.tubes).reduce(
        (a, tubes) => [
          ...a,
          ...Object.values<any>(tubes)
            .filter(v => v.checked && !v.status)
            .reduce((x, v) => [...x, v.id], []),
        ],
        [],
      );
    // eslint-disable-next-line max-len
    const { ok, details } = await this.$api('/directions/tubes-register-get', { pks, selectGetTime });
    await this.$store.dispatch(actions.DEC_LOADING);
    if (needPrintBarcodes && ok) {
      this.printBarcodes(pks);
    }

    if (this.details) {
      this.details = { ...this.details, ...(details || {}) };
    }

    if (!ok) {
      this.$root.$emit('msg', 'error', 'Ошибка');
    } else {
      if (this.tubes) {
        this.tubes = Object.entries<any>(this.tubes).reduce(
          (a, [lab, tubes]) => ({
            ...a,
            [lab]: Object.entries<any>(tubes).reduce(
              (x, [k, v]) => ({ ...x, [k]: { ...v, status: v.status || pks.includes(v.id) } }),
              {},
            ),
          }),
          {},
        );
      }

      this.$root.$emit('load-tubes', pks);

      this.$root.$emit('msg', 'ok', 'Забор материала зарегистрирован');

      if (toConfirmPks) {
        await this.openConfirmationList(true);
      } else {
        window.$(this.$refs.q).focus();
      }
    }
  }

  async openConfirmationList(hidden = false) {
    this.showConfirmList = true;
    this.loading = !hidden;
    await this.$store.dispatch(actions.INC_LOADING);
    const { rows } = await this.$api('/directions/tubes-for-confirm');
    this.tubesForConfirm = rows;
    await this.$store.dispatch(actions.DEC_LOADING);
    this.loading = false;
  }

  get globalCheckConfirm() {
    return this.tubesForConfirm.every(t => t.checked);
  }

  toggleGlobalCheckConfirm() {
    const newChecked = !this.globalCheckConfirm;

    this.tubesForConfirm = this.tubesForConfirm.map(t => ({ ...t, checked: newChecked }));
  }
}
</script>

<style lang="scss" scoped>
.b-root {
  padding: 5px;
}

.control-buttons {
  margin-bottom: 10px;
}

.main-table {
  margin-top: 10px;
  margin-bottom: 10px;
  table-layout: fixed;

  th,
  td {
    padding: 2px;

    &.cl-td {
      padding: 0;
    }
  }

  th {
    vertical-align: middle;
  }

  td {
    text-align: left;
  }

  h2 {
    margin: 2px;
    padding: 0px;
  }
}

.tubes-table {
  table-layout: fixed;
}

.tube_id {
  display: flex;
  margin-bottom: 0;
  height: 100%;
  justify-content: space-between;
  align-items: center;
  padding: 0 4px;

  span {
    font-size: 16px;
    font-family: 'Courier New', Courier, monospace !important;
    font-weight: bold !important;
  }
}

.row-checked {
  background-color: rgba(#049372, 0.05);
}

.top-search {
  display: flex;
  justify-content: stretch;

  .input-group {
    flex: 1 calc(100% - 185px);
  }
}

.confirm-list-wrapper {
  padding-right: 8px;
  width: 185px;
  flex: 0 185px;
}
</style>
