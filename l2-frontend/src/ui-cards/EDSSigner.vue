<template>
  <div v-frag>
    <div
      v-if="!checked"
      class="eds-preloader"
    >
      <i class="fa fa-spinner" /> загрузка
    </div>
    <div
      v-else
      v-frag
    >
      <div class="row cryptopro">
        <div
          v-if="!hasCP"
          class="col-xs-3"
        >
          <div class="eds-status status-error">
            Плагин CSP не настроен
          </div>
        </div>
        <div
          v-else
          class="col-xs-8"
        >
          <select
            v-if="certificatesDisplay.length > 0"
            v-model="selectedCertificate"
            class="form-control"
          >
            <option
              v-for="c in certificatesDisplay"
              :key="c.thumbprint"
              :value="c.thumbprint"
            >
              {{ c.name }}
            </option>
          </select>
          <div
            v-else
            class="status-error"
          >
            Нет сертификатов
          </div>
        </div>
        <div
          v-if="selectedCertificateObject"
          class="col-xs-4 cert-info"
        >
          <div>{{ selectedCertificateObject.thumbprint }}</div>
          <div>{{ selectedCertificateObject.validFrom }} — {{ selectedCertificateObject.validTo }}</div>
        </div>
      </div>
    </div>

    <EDSDocument
      v-for="d in documents"
      :key="d.type"
      :d="d"
      :thumbprint="selectedCertificate"
      :direction="directionPk"
      :executors="executors"
      :no-o-g-r-n="noOGRN"
    />

    <div
      v-if="commonRoles.length > 0 && selectedCertificate && selectedSignatureMode"
      class="sign-block"
    >
      <div class="input-group">
        <span class="input-group-addon">Роль подписи для всех вложений</span>
        <select
          v-model="selectedSignatureMode"
          class="form-control"
        >
          <option
            v-for="s in commonRoles"
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
            :disabled="!!invalidMessage"
            @click="addSign"
          >
            Подписать все вложения
          </button>
        </span>
      </div>
    </div>
    <div
      v-if="error || invalidMessage"
      class="status-error"
    >
      <h4><strong>{{ message || invalidMessage }}</strong></h4>
    </div>
  </div>
</template>

<script lang="ts">
import { getSystemInfo, getUserCertificates } from 'crypto-pro';
import moment from 'moment';
import { debounce } from 'lodash/function';

import * as actions from '@/store/action-types';
import { convertSubjectNameToTitle, subjectNameHasOGRN } from '@/utils';

import EDSDocument from './EDSDocument.vue';

export default {
  name: 'EDSSigner',
  components: {
    EDSDocument,
  },
  props: {
    directionPk: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      requiredSignatures: [],
      requiredEDSDocTypes: [],
      systemInfo: null,
      certificates: [],
      selectedCertificate: null,
      checked: false,
      hasCP: false,
      documents: [],
      executors: {},
      selectedSignatureMode: null,
      error: false,
      message: '',
    };
  },
  computed: {
    selectedCertificateObject() {
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
    },
    certificatesDisplay() {
      return this.certificates.map(c => ({
        thumbprint: c.thumbprint,
        name: convertSubjectNameToTitle(null, c.subjectName),
      }));
    },
    isDocAllowedSign() {
      return Boolean(this.executors[this.$store.getters.user_data.doc_pk]);
    },
    eds_allowed_sign() {
      return (this.$store.getters.user_data.eds_allowed_sign || []).filter(s => s !== 'Врач' || this.isDocAllowedSign);
    },
    commonRoles() {
      const r = {};
      for (const d of Array.isArray(this.documents) ? this.documents : []) {
        for (const s of Object.keys(d.signatures)) {
          if (!d.signatures[s] && (s !== 'Врач' || this.isDocAllowedSign)) {
            r[s] = true;
          }
        }
      }

      return Object.keys(r);
    },
    noOGRN() {
      const cert = this.certificates.find(c => c.thumbprint === this.selectedCertificate);

      if (!cert) {
        return false;
      }

      return !subjectNameHasOGRN(null, cert.subjectName);
    },
    invalidMessage() {
      if (!this.noOGRN || this.selectedSignatureMode !== 'Медицинская организация') {
        return null;
      }

      return 'Отсутствует ОГРН в сертификате';
    },
  },
  watch: {
    commonRoles: {
      immediate: true,
      handler() {
        if (this.commonRoles.length === 0) {
          this.selectedSignatureMode = null;
          return;
        }

        if (this.commonRoles.includes(this.selectedSignatureMode)) {
          return;
        }

        // eslint-disable-next-line prefer-destructuring
        this.selectedSignatureMode = this.commonRoles[0];
      },
    },
  },
  mounted() {
    this.init();
    this.$root.$on('eds:reload-document', direction => {
      if (this.directionPk === direction) {
        this.loadStatusDebounced();
      }
    });
  },
  methods: {
    async loadStatus() {
      await this.$store.dispatch(actions.INC_LOADING);
      const {
        documents, executors, error, message,
      } = await this.$api('/directions/eds/documents', {
        pk: this.directionPk,
      });
      this.documents = documents;
      this.executors = executors;
      this.error = error;
      this.message = message;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    loadStatusDebounced: debounce(function loadStatusDebounced() {
      this.loadStatus();
    }, 100),
    async addSign() {
      try {
        await this.$dialog.confirm(
          `Подтвердите подпись всех вложений в документ №${this.directionPk} как "${this.selectedSignatureMode}"`,
        );
      } catch (e) {
        return;
      }

      for (const d of this.documents) {
        this.$root.$emit('eds:fast-sign', d.pk, this.selectedSignatureMode);
      }
    },
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
          this.selectedCertificate = this.certificates[0]?.thumbprint;
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
    },
    async init() {
      await Promise.all([this.loadStatusDebounced(), this.getEDSStatus()]);
    },
  },
};
</script>

<style scoped lang="scss">
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

.cryptopro {
  margin: 0 0 10px 0;
  padding: 5px 0;
  border-radius: 4px;
  box-shadow: 0 0 5px rgba(0, 0, 0, 0.4);
  background: #fff;
}
</style>
