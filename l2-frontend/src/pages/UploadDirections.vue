<template>
  <div class="root">
    <div class="top-block row">
      <div class="col-xs-6">
        <div class="radio-wrapper">
          <RadioFieldById
            v-model="filters.mode"
            :variants="modesAvailable"
            :disabled="disabledByNumber"
          />
        </div>
        <treeselect
          v-if="filters.mode === 'mo'"
          v-model="filters.department"
          class="treeselect-wide treeselect-34px"
          :multiple="false"
          :disable-branch-nodes="true"
          :options="deps"
          :clearable="false"
          placeholder="Подразделение не выбано"
          :disabled="disabledByNumber"
        />
      </div>
      <div class="col-xs-6">
        <div class="radio-wrapper">
          <RadioFieldById
            v-model="filters.status"
            :variants="STATUSES"
            :disabled="disabledByNumber"
          />
        </div>
        <div class="row">
          <div class="col-xs-6">
            <DateFieldNav2
              v-model="filters.date"
              w="100%"
              :brn="false"
              :disabled="disabledByNumber"
            />
          </div>
          <div class="col-xs-6">
            <input
              v-model.trim="filters.number"
              type="text"
              class="form-control"
              placeholder="номер направления"
            >
          </div>
        </div>
      </div>
    </div>

    <button
      class="top-button btn btn-blue-nb2 btn-block"
      type="button"
      @click="load(null)"
    >
      <i class="fa fa-search" /> Поиск
    </button>

    <div
      v-if="!loaded || error"
      class="not-loaded"
    >
      Данные не загружены
      <br>
      <span class="status-error">{{ message }}</span>
    </div>
    <div
      v-else
      class="data"
    >
      <div>
        <div
          v-if="hasAnyChecked"
          class="float-right input-group"
          style="width: 450px;"
        >
          <span class="input-group-addon">Роль подписи</span>
          <select
            v-model="selectedSignatureMode"
            class="form-control"
          >
            <option
              v-for="s in commonSignModes"
              :key="s"
              :value="s"
            >
              {{ s }}
            </option>
          </select>
          <span class="input-group-btn">
            <button
              type="button"
              class="btn btn-default btn-primary-nb"
              :disabled="!selectedSignatureMode"
              @click="listSign()"
            >
              Подписать списком
            </button>
          </span>
        </div>
        <button
          v-else
          class="btn btn-blue-nb float-right"
          @click="load(page)"
        >
          <i class="fa fa-refresh" />
        </button>
        <paginate
          v-model="page"
          :page-count="pages"
          :page-range="4"
          :margin-pages="2"
          :click-handler="load"
          prev-text="Назад"
          next-text="Вперёд"
          container-class="pagination"
        />
      </div>
      <table class="table table-bordered table-condensed">
        <colgroup>
          <col style="width: 130px">
          <col>
          <col>
          <col style="width: 160px">
          <col style="width: 25px">
        </colgroup>
        <thead>
          <tr>
            <th>
              № направления
            </th>
            <th>
              Подтверждено
            </th>
            <th>
              Услуги
            </th>
            <th>
              Подписи
            </th>
            <td
              :key="`check_${globalCheckStatus}`"
              class="x-cell"
            >
              <label
                v-if="hasToCheck"
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
          <tr
            v-for="r in rows"
            :key="r.pk"
            :class="totallySigned(r) && 'tr-ok'"
          >
            <td>
              {{ r.pk }}
              <span
                v-if="!r.hasSnils"
                class="status-error"
              > <i class="fa fa-exclamation-triangle" />СНИЛС</span>
            </td>
            <td>{{ r.confirmedAt }}, {{ r.docConfirmation }}</td>
            <td>
              {{ r.services.join('; ') }}
            </td>
            <td class="eds-td cl-td">
              <div>
                <EDSDirection
                  :direction-pk="r.pk"
                  :all_confirmed="true"
                  :documents-prefetched="r.documents"
                />
              </div>
              <div
                v-if="totallySigned(r)"
                class="uploading-status"
                :class="r.n3number ? 'm-ok' : 'm-error'"
              >
                {{ r.n3number ? 'выгружено в ИЭМК' : 'не выгружено в ИЭМК' }}
              </div>
            </td>
            <td class="x-cell">
              <label v-if="!totallySigned(r) && r.hasSnils">
                <input
                  v-model="r.checked"
                  type="checkbox"
                >
              </label>
            </td>
          </tr>
        </tbody>
      </table>
      <div>
        <div
          v-if="hasAnyChecked"
          class="float-right input-group"
          style="width: 450px;"
        >
          <span class="input-group-addon">Роль подписи</span>
          <select
            v-model="selectedSignatureMode"
            class="form-control"
          >
            <option
              v-for="s in commonSignModes"
              :key="s"
              :value="s"
            >
              {{ s }}
            </option>
          </select>
          <span class="input-group-btn">
            <button
              type="button"
              class="btn btn-default btn-primary-nb"
              :disabled="!selectedSignatureMode"
              @click="listSign()"
            >
              Подписать списком
            </button>
          </span>
        </div>
        <button
          v-else
          class="btn btn-blue-nb float-right"
          @click="load(page)"
        >
          <i class="fa fa-refresh" />
        </button>
        <paginate
          v-model="page"
          :page-count="pages"
          :page-range="4"
          :margin-pages="2"
          :click-handler="load"
          prev-text="Назад"
          next-text="Вперёд"
          container-class="pagination"
        />
      </div>
      <div class="founded">
        Найдено записей: <strong>{{ total }}</strong>
      </div>
    </div>
    <transition name="fade">
      <div
        v-if="signingProcess.active"
        class="signing-root"
      >
        <div class="signing-inner">
          <div class="signing-header">
            Создание подписей как {{ selectedSignatureMode }}
            <i
              v-if="signingProcess.progress"
              class="fa fa-spinner"
            />
            <i
              v-else
              class="fa fa-check"
            />
          </div>

          <ProgressBar
            size="large"
            :val="signP"
            :text="
              `${signP}% – ${signingProcess.currentDocument}/${signingProcess.totalDocuments} ${signingProcess.currentOperation}`
            "
            bar-transition="all 0.1s linear"
            text-position="bottom"
            text-align="left"
            :font-size="14"
            text-fg-color="#fff"
            bar-color="#049372"
          />

          <button
            type="button"
            class="btn btn-default btn-primary-nb"
            :disabled="signingProcess.progress"
            @click="load(page)"
          >
            Закрыть и перезагрузить список
          </button>

          <table class="table table-condensed table-bordered">
            <thead>
              <tr>
                <th>Направление</th>
                <th>Документ</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="p in signingProcess.log"
                :key="`${p.direction}_${p.type}`"
                :class="p.status ? 'tr-ok' : 'tr-error'"
              >
                <td>{{ p.direction }}</td>
                <td>{{ p.type }}</td>
                <td :class="p.status ? 'm-ok' : 'm-error'">
                  {{ p.status ? 'ОК' : 'ОШИБКА' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </transition>
  </div>
</template>

<script lang="ts">
import {
  createDetachedSignature, createHash, getCertificate, getSystemInfo, getUserCertificates,
} from 'crypto-pro';
import moment from 'moment';
import Vue from 'vue';
import Component from 'vue-class-component';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import Paginate from 'vuejs-paginate';
import ProgressBar from 'vue-simple-progress';

import * as actions from '@/store/action-types';
import usersPoint from '@/api/user-point';
import RadioFieldById from '@/fields/RadioFieldById.vue';
import DateFieldNav2 from '@/fields/DateFieldNav2.vue';
import EDSDirection from '@/ui-cards/EDSDirection.vue';
import { convertSubjectNameToCertObject, convertSubjectNameToTitle, subjectNameHasOGRN } from '@/utils';

const MODES = [
  { id: 'mo', label: 'Подписи медицинской организации' },
  { id: 'my', label: 'Мои документы' },
];

const STATUSES = [
  { id: 'need', label: 'Требуют отправки' },
  { id: 'ok-role', label: 'Отправлены' },
];

@Component({
  components: {
    Treeselect,
    RadioFieldById,
    DateFieldNav2,
    Paginate,
    EDSDirection,
    ProgressBar,
  },
  data() {
    return {
      systemInfo: null,
      certificates: [],
      selectedCertificate: null,
      checked: false,
      hasCP: false,
      filters: {
        mode: null,
        department: null,
        status: STATUSES[0].id,
        number: '',
        date: moment().format('YYYY-MM-DD'),
      },
      MODES,
      STATUSES,
      users: [],
      page: 1,
      pages: 0,
      total: 0,
      loaded: false,
      error: false,
      message: '',
      rows: [],
      selectedSignatureMode: null,
      signingProcess: {
        active: false,
        progress: false,
        totalDocuments: 0,
        currentDocument: 0,
        log: [],
        currentOperation: '',
      },
    };
  },
  mounted() {
    this.getEDSStatus();
    this.loadUsers();
  },
  watch: {
    modesAvailable: {
      immediate: true,
      handler() {
        if (!this.modesAvailable.find(m => m.id === this.filters.mode)) {
          this.filters.mode = this.modesAvailable[0].id;
        }
      },
    },
    commonSignModes: {
      immediate: true,
      handler() {
        if (this.commonSignModes.length === 0) {
          this.selectedSignatureMode = null;
          return;
        }

        if (this.commonSignModes.includes(this.selectedSignatureMode)) {
          return;
        }

        // eslint-disable-next-line prefer-destructuring
        this.selectedSignatureMode = this.commonSignModes[0];
      },
    },
  },
})
export default class EDS extends Vue {
  systemInfo: any;

  certificates: any[];

  selectedCertificate: string | null;

  checked: boolean;

  hasCP: boolean;

  filters: any;

  MODES: any[];

  STATUSES: any[];

  users: any[];

  page: number;

  pages: number;

  total: number;

  loaded: boolean;

  error: boolean;

  message: string;

  rows: any[];

  selectedSignatureMode: any;

  signingProcess: any;

  get noOGRN() {
    const cert = this.certificates.find(c => c.thumbprint === this.selectedCertificate);

    if (!cert) {
      return false;
    }

    return !subjectNameHasOGRN(null, cert.subjectName);
  }

  get snilsUser() {
    return (this.$store.getters.user_data.snils);
  }

  get accessToMO() {
    return (this.$store.getters.user_data.groups || []).includes('ЭЦП Медицинской организации');
  }

  get modesAvailable() {
    return this.MODES.filter(m => m.id !== 'mo' || this.accessToMO);
  }

  get edsAllowedSign() {
    return this.$store.getters.user_data.eds_allowed_sign;
  }

  get commonSignModes() {
    const m = [];
    for (const r of this.rows.filter(v => v.checked)) {
      for (const d of r.documents) {
        for (const e of d.empty) {
          if (!m.includes(e) && this.edsAllowedSign.includes(e)) {
            m.push(e);
          }
        }
      }
    }
    return m;
  }

  get disabledByNumber() {
    return Boolean(this.filters.number);
  }

  get selectedCertificateObject() {
    if (!this.selectedCertificate) {
      return {};
    }

    const cert = this.certificates.find(c => c.thumbprint === this.selectedCertificate);
    if (!cert) {
      return {};
    }

    return {
      thumbprint: cert.thumbprint,
      validFrom: moment(cert.validFrom).format('DD.MM.YYYY HH:mm'),
      validTo: moment(cert.validTo).format('DD.MM.YYYY HH:mm'),
    };
  }

  get certificatesDisplay() {
    const filteredCertificates = this.certificates.filter((cert) => {
      const certObj = convertSubjectNameToCertObject(cert.subjectName);
      const snilsCert = certObj['СНИЛС'] || certObj.SNILS;
      if (this.filters.mode === 'my') {
        return snilsCert === this.snilsUser;
      }
      return !!(certObj.ORGN || certObj['ОГРН']);
    });
    if (filteredCertificates.length === 0) {
      this.selectedCertificate = null;
    } else {
      this.selectedCertificate = filteredCertificates[0]?.thumbprint;
    }
    return filteredCertificates.map(c => ({
      thumbprint: c.thumbprint,
      name: convertSubjectNameToTitle(null, c.subjectName),
    }));
  }

  get deps() {
    return [
      ...this.users.map(d => ({ id: d.id, label: d.label })),
      { id: -1, label: 'Все отделения' },
    ];
  }

  get globalCheckStatus() {
    return this.rows.every(r => r.checked && this.totallySigned(r));
  }

  get hasAnyChecked() {
    return this.rows.some(r => r.checked && !this.totallySigned(r));
  }

  get rowsChecked() {
    return this.rows.filter(r => r.checked && !this.totallySigned(r));
  }

  get hasToCheck() {
    return this.hasCP && this.checked && this.selectedCertificate && this.rows.some(r => !this.totallySigned(r));
  }

  get signP() {
    return Math.ceil((this.signingProcess.currentDocument / this.signingProcess.totalDocuments) * 1000) / 10;
  }

  async loadUsers() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { users } = await usersPoint.loadUsersByGroup({ group: '*' });
    this.users = users;
    this.filters.department = this.$store.getters.user_data?.department?.pk || null;
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async getEDSStatus() {
    try {
      this.systemInfo = await getSystemInfo();
      // eslint-disable-next-line no-console
      console.log('getStatus', true, this.systemInfo);
      this.hasCP = true;
      try {
        this.certificates = await getUserCertificates();
      } catch (e) {
        // eslint-disable-next-line no-console
        console.log('getCertificates error');
        // eslint-disable-next-line no-console
        console.error(e);
        this.checked = false;
      }
      if (this.certificates.length > 0) {
        // eslint-disable-next-line no-console
        console.log('getCertificates', true, this.certificates);
      } else {
        // eslint-disable-next-line no-console
        console.log('getCertificates', false);
      }
      this.checked = true;
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error(e);
      // eslint-disable-next-line no-console
      console.log('getStatus', false);
      this.hasCP = false;
      this.checked = true;
    }
  }

  async load(pageToLoad) {
    if (this.signingProcess.active) {
      this.rows = [];
    }
    const prevSelectedSignatureMode = this.selectedSignatureMode;
    this.signingProcess.progress = false;
    this.signingProcess.active = false;
    if (pageToLoad !== null) {
      this.page = pageToLoad;
    } else {
      this.page = 1;
    }
    await this.$store.dispatch(actions.INC_LOADING);
    const {
      rows, page, pages, total, error, message,
    } = await this.$api('/directions/eds/to-sign', this, ['filters', 'page']);
    this.rows = rows.map(r => ({ ...r, checked: false }));
    this.page = page;
    this.pages = pages;
    this.total = total;
    this.error = error;
    this.message = message;
    await this.$store.dispatch(actions.DEC_LOADING);
    this.loaded = true;
    if (this.commonSignModes.includes(prevSelectedSignatureMode)) {
      this.selectedSignatureMode = prevSelectedSignatureMode;
    }
  }

  toggleGlobalCheck() {
    const newStatus = !this.globalCheckStatus;
    this.rows = this.rows.map(r => ({ ...r, checked: newStatus && !this.totallySigned(r) && r.hasSnils }));
  }

  // eslint-disable-next-line class-methods-use-this
  totallySigned(r) {
    if (r.totallySigned) {
      return true;
    }

    return r.documents.every(x => x.empty.length === 0);
  }

  async listSign() {
    if (this.noOGRN && this.selectedSignatureMode === 'Медицинская организация') {
      this.$error('Отсутствует ОГРН в сертификате');
      return;
    }

    if (this.signingProcess.active) {
      return;
    }
    try {
      await this.$dialog.confirm(`Подтвердите подпись всех выбранных документов как "${this.selectedSignatureMode}"`);
    } catch (_) {
      return;
    }
    this.signingProcess.active = true;
    this.signingProcess.progress = true;
    this.signingProcess.log = [];
    this.signingProcess.currentOperation = '';
    this.signingProcess.totalDocuments = this.rowsChecked.reduce((a, b) => a + b.documents.length, 0);
    this.signingProcess.currentDocument = 0;

    const cert = await getCertificate(this.selectedCertificate);

    for (const r of this.rowsChecked) {
      try {
        this.signingProcess.currentOperation = `${r.pk} получение документов`;
        const { documents } = await this.$api('/directions/eds/documents', {
          pk: r.pk,
        });
        for (const d of documents) {
          if (d.signatures[this.selectedSignatureMode]) {
            this.signingProcess.currentDocument++;
            continue;
          }
          const docTitle = `${r.pk} ${d.type}`;
          const docToLog = {
            direction: r.pk,
            type: d.type,
            status: false,
          };
          try {
            let body = d.fileContent;
            if (d.type === 'PDF') {
              body = Uint8Array.from(atob(body), c => c.charCodeAt(0));
            }
            const isString = typeof body === typeof '';

            const bodyEncoded = isString ? body : new Uint8Array(body);

            this.signingProcess.currentOperation = `${docTitle} создание подписи`;
            const m = await createHash(bodyEncoded);
            const sign = await createDetachedSignature(this.selectedCertificate, m);

            this.signingProcess.currentOperation = `${docTitle} отправка подписи`;
            const { ok, message } = await this.$api('/directions/eds/add-sign', {
              pk: d.pk,
              sign,
              mode: this.selectedSignatureMode,
              certThumbprint: this.selectedCertificate,
              certDetails: cert ? {
                subjectName: cert.subjectName,
                validFrom: cert.validFrom,
                validTo: cert.validTo,
              } : null,
            });

            if (ok) {
              const msg = `Подпись успешно добавлена: ${r.pk}, ${d.type}, ${this.selectedSignatureMode}`;
              this.$root.$emit('msg', 'ok', msg, 1500);
              docToLog.status = true;
            } else {
              this.$root.$emit('msg', 'error', message);
            }
          } catch (e) {
            // eslint-disable-next-line no-console
            console.error(e);
            this.$root.$emit('msg', 'error', 'Ошибка создания подписи!');
          }
          this.signingProcess.log.push(docToLog);
          this.signingProcess.currentDocument++;
        }
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error(e);
        this.$root.$emit('msg', 'error', `Ошибка подписи ${r.pk}`);
        const docToLog = {
          direction: r.pk,
          type: '???',
          status: false,
        };
        this.signingProcess.log.push(docToLog);
      }
    }
    this.signingProcess.progress = false;
    this.signingProcess.currentOperation = '';
  }
}
</script>

<style lang="scss" scoped>
.eds-preloader {
  padding: 20px;
  text-align: center;
}

.status {
  &-error {
    color: #cf3a24;
  }

  &-ok {
    color: #049372;
  }
}

.cert-info {
  font-size: 12px;
}

.eds-status {
  padding: 5px 0;
}

.top-block {
  margin: 0 0 10px 0;
  padding: 5px 0;
  border-radius: 4px;
  box-shadow: 0 0 5px rgba(0, 0, 0, 0.4);
  background: #fff;

  &.row,
  &.eds-preloader {
    min-height: 44px;
  }
}

.root {
  margin: -10px auto 0 auto;
  max-width: 1200px;
  padding: 0 10px;
}

.radio-wrapper {
  margin-bottom: 5px;
}

.top-button {
  margin-bottom: 15px;
}

.not-loaded {
  text-align: center;
  color: grey;
}

.data {
  padding: 0 20px;
}

.founded {
  text-align: center;
  padding: 5px;
  margin-top: -5px;
}

.tr-ok {
  background-color: rgba(#049372, 0.1);
}

.tr-error {
  background-color: rgba(#930425, 0.1);
}

.m-ok {
  font-weight: bold;
  color: #049372;
}

.m-error {
  font-weight: bold;
  color: #930425;
}

.eds-td > div {
  display: flex;
  flex-direction: row;
  margin-left: -5px;
}

.signing {
  &-root {
    position: fixed;
    width: 100%;
    height: 100%;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(1px);
    z-index: 100000;
  }

  &-inner {
    margin: 0 auto;
    max-width: 1200px;
    width: 100%;
    padding: 0 10px;
    height: 100%;
    padding: 50px 0;
    overflow-y: auto;

    .btn {
      width: auto !important;
      margin: 10px auto 20px auto !important;
      display: block;
    }

    .table {
      background: #fff;
    }
  }

  &-header {
    text-align: center;
    margin-bottom: 10px;
    color: #fff;
    font-size: 20px;
    font-weight: bold;
  }
}

.uploading-status {
  margin-left: 0 !important;
  text-align: center;
  display: block !important;
}
</style>

<style>
.pagination {
  margin-top: 0 !important;
}
</style>
