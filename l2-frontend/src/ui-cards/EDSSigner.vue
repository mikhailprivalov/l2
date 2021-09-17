<template>
  <div v-frag>
    <div v-if="!checked" class="eds-preloader"><i class="fa fa-spinner"></i> загрузка</div>
    <div v-frag v-else>
      <div class="row cryptopro">
        <div class="col-xs-3">
          <div v-if="!hasCP" class="eds-status status-error">Плагин CSP не настроен</div>
          <div v-else class="eds-status status-ok"><i class="fa fa-check"></i> Плагин CSP {{ systemInfo.cspVersion }}</div>
        </div>
        <div class="col-xs-5" v-if="hasCP">
          <select class="form-control" v-model="selectedCertificate" v-if="selectedCertificate.length > 0">
            <option v-for="c in certificates" :key="c.thumbprint" :value="c.thumbprint">
              {{ c.name }}
            </option>
          </select>
          <div v-else class="status-error">
            Нет сертификатов
          </div>
        </div>
        <div class="col-xs-4 cert-info" v-if="selectedCertificateObject">
          <div>{{ selectedCertificateObject.thumbprint }}</div>
          <div>{{ selectedCertificateObject.validFrom }} — {{ selectedCertificateObject.validTo }}</div>
        </div>
      </div>
    </div>

    <EDSDocument v-for="d in documents" :key="d.type" :d="d" :thumbprint="selectedCertificate" :direction="directionPk" />
  </div>
</template>

<script lang="ts">
import { getSystemInfo, getUserCertificates } from 'crypto-pro';
import moment from 'moment';

import * as actions from '@/store/action-types';
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
    allowedSign() {
      return this.$store.getters.user_data.eds_allowed_sign;
    },
  },
  mounted() {
    this.init();
    this.$root.$on('eds:reload-document', direction => {
      if (this.directionPk === direction) {
        this.loadStatus();
      }
    });
  },
  methods: {
    async loadStatus() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { documents } = await this.$api('/directions/eds/documents', {
        pk: this.directionPk,
      });
      this.documents = documents;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async getEDSStatus() {
      try {
        this.systemInfo = await getSystemInfo();
        console.log('getStatus', true, this.systemInfo);
        this.hasCP = true;
        try {
          this.certificates = await getUserCertificates();
        } catch (e) {
          console.log('getCertificates error');
          console.error(e);
          this.checked = false;
        }
        if (this.certificates.length > 0) {
          console.log('getCertificates', true, this.certificates);
          this.selectedCertificate = (this.certificates[0] || {}).thumbprint;
        } else {
          console.log('getCertificates', false);
        }
        this.checked = true;
      } catch (e) {
        console.error(e);
        console.log('getStatus', false);
        this.hasCP = false;
        this.checked = true;
      }
    },
    async init() {
      await Promise.all([this.loadStatus(), this.getEDSStatus()]);
    },
  },
  watch: {},
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
