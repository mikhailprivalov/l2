<template>
  <div class="eds-document">
    <div class="doc-header">Документ {{ d.type }}</div>

    <div class="sign-block" v-if="emptyAllowedSignatures.length > 0 && thumbprint">
      <div class="input-group">
        <span class="input-group-addon">Роль подписи</span>
        <select class="form-control" v-model="selectedSignatureMode">
          <option v-for="s in emptyAllowedSignatures" :key="s" :value="s">
            {{ s }}
          </option>
        </select>
        <span class="input-group-btn">
          <button type="button" class="btn btn-default btn-primary-nb" @click="addSign">
            Подписать
          </button>
        </span>
      </div>
    </div>

    <div>
      <a class="btn btn-default" :href="fileHref" :download="d.fileName" v-if="d.fileContent">
        <i class="fa fa-download"></i> Загрузить {{ d.fileName }}
      </a>
    </div>
  </div>
</template>

<script lang="ts">
import { createDetachedSignature, createHash } from 'crypto-pro';

import * as actions from '@/store/action-types';

export default {
  name: 'EDSSigner',
  props: {
    d: {
      type: Object,
      required: true,
    },
    thumbprint: {
      type: String,
      required: false,
    },
    direction: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      selectedSignatureMode: null,
    };
  },
  computed: {
    fileHref() {
      let body = this.d.fileContent || '';
      if (!body) {
        return null;
      }
      const isString = typeof body === typeof '';
      body = isString ? body : new Uint8Array(body);
      const t = this.d.type === 'PDF' ? 'application/pdf;base64' : 'data:text/xml';
      const dataStr = isString
        ? encodeURIComponent(body)
        : btoa(body.reduce((data, byte) => data + String.fromCharCode(byte), ''));
      return `data:${t},${dataStr}`;
    },
    eds_allowed_sign() {
      return this.$store.getters.user_data.eds_allowed_sign || [];
    },
    emptySignatures() {
      return Object.keys(this.d.signatures).filter(s => !this.d.signatures[s]);
    },
    emptyAllowedSignatures() {
      return this.emptySignatures.filter(s => this.eds_allowed_sign.includes(s));
    },
    emptyNotAllowedSignatures() {
      return this.emptySignatures.filter(s => !this.eds_allowed_sign.includes(s));
    },
  },
  watch: {
    emptyAllowedSignatures: {
      immediate: true,
      handler() {
        if (this.emptyAllowedSignatures.length === 0) {
          this.selectedSignatureMode = null;
          return;
        }

        if (this.emptyAllowedSignatures.includes(this.selectedSignatureMode)) {
          return;
        }

        // eslint-disable-next-line prefer-destructuring
        this.selectedSignatureMode = this.emptyAllowedSignatures[0];
      },
    },
  },
  methods: {
    async addSign() {
      await this.$store.dispatch(actions.INC_LOADING);
      try {
        const isString = typeof this.d.data === typeof '';
        const body = this.d.fileContent;

        const bodyEncoded = isString ? body : new Uint8Array(body);

        const m = await createHash(bodyEncoded);
        const sign = await createDetachedSignature(this.thumbprint, m);
        const { ok, message } = await this.$api('/directions/eds/add-sign', {
          pk: this.d.pk,
          sign,
          mode: this.selectedSignatureMode,
        });

        if (ok) {
          this.$root.$emit('eds:reload-document', this.direction);
          this.$root.$emit('msg', 'ok', 'Подпись успешно добавлена');
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      } catch (e) {
        console.error(e);
        this.$root.$emit('msg', 'error', 'Ошибка создания подписи!');
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style scoped lang="scss">
.eds-document {
  margin: 0 0 10px 0;
  padding: 5px;
  border: 1px solid #bbb;
  border-radius: 4px;
}

.doc-header {
  font-weight: bold;
}

.sign-block {
  margin: 10px 0;
  max-width: 500px;
}
</style>
