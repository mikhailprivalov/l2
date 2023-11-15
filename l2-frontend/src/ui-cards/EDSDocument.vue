<template>
  <div
    class="eds-document"
    :class="ok && 'eds-document-ok'"
  >
    <div class="doc-header">
      Вложение {{ d.type }}
    </div>

    <div
      v-if="!isDocAllowedSign"
      class="sign-block"
    >
      <div class="block-header">
        Подпись врача может добавить только:
      </div>

      <ul>
        <li
          v-for="(v, k) in executors"
          :key="k"
        >
          {{ v }}
        </li>
      </ul>
    </div>

    <div
      v-if="emptyNotAllowedSignatures.length > 0"
      class="sign-block"
    >
      <div class="block-header">
        Недоступные роли для подписи:
      </div>

      <ul>
        <li
          v-for="s in emptyNotAllowedSignatures"
          :key="s"
        >
          {{ s }}
        </li>
      </ul>
    </div>

    <div
      v-if="emptyAllowedSignatures.length > 0 && thumbprint"
      class="sign-block"
    >
      <div class="input-group">
        <span class="input-group-addon">Роль подписи</span>
        <select
          v-model="selectedSignatureMode"
          class="form-control"
        >
          <option
            v-for="s in emptyAllowedSignatures"
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
            @click="addSign()"
          >
            Подписать
          </button>
        </span>
      </div>
    </div>

    <div
      v-if="hasSigns"
      class="has-signs"
    >
      <div class="block-header">
        Добавленные подписи:
      </div>
      <ul>
        <li
          v-for="s in signs"
          :key="s.type"
        >
          <a
            v-tippy
            :href="fileHref(s.signValue, 'text/plain')"
            :download="signFileName(s)"
            class="a-under"
            title="Скачать файл подписи"
          >
            <i class="fa fa-download" />
          </a>
          <strong>{{ s.type }}</strong>, <EDSSignTitle
            :executor="s.executor"
            :signature="s.signValue"
            :data="d.fileContent"
            :type="d.type"
          />, {{ s.signedAt }}
        </li>
      </ul>
    </div>

    <div class="download-block">
      <a
        v-if="d.fileContent"
        class="btn btn-default"
        :href="docHref"
        :download="d.fileName"
      >
        <i class="fa fa-download" /> Загрузить {{ d.fileName }}
      </a>
    </div>

    <div
      v-if="isL2VI && d.type === 'CDA'"
      class="download-block"
    >
      <div
        v-if="d.vi_id"
        class="block-header"
      >
        Отправлено в ВИМИС как {{ d.vi_id }}
      </div>
      <a
        v-else
        class="btn btn-default"
        href="#"
        @click.prevent="sendToVI"
      >
        Отправить в ВИМИС
      </a>
    </div>
  </div>
</template>

<script lang="ts">
import { createDetachedSignature, createHash, getCertificate } from 'crypto-pro';

import * as actions from '@/store/action-types';

import EDSSignTitle from './EDSSignTitle.vue';

export default {
  name: 'EDSDocument',
  components: {
    EDSSignTitle,
  },
  props: {
    d: {
      type: Object,
      required: true,
    },
    executors: {
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
    noOGRN: {
      type: Boolean,
      required: false,
    },
  },
  data() {
    return {
      selectedSignatureMode: null,
    };
  },
  computed: {
    docHref() {
      return this.fileHref(this.d.fileContent, this.d.type === 'PDF' ? 'application/pdf;base64' : 'data:text/xml');
    },
    eds_allowed_sign() {
      return (this.$store.getters.user_data.eds_allowed_sign || []).filter(s => s !== 'Врач' || this.isDocAllowedSign);
    },
    isDocAllowedSign() {
      return Boolean(this.executors[this.$store.getters.user_data.doc_pk]);
    },
    isL2VI() {
      return !!this.$store.getters.modules.l2_l2vi;
    },
    emptySignatures() {
      return Object.keys(this.d.signatures).filter(s => !this.d.signatures[s]);
    },
    emptyAllowedSignatures() {
      return this.emptySignatures.filter(s => this.eds_allowed_sign.includes(s));
    },
    emptyNotAllowedSignatures() {
      return this.emptySignatures.filter(s => !this.emptyAllowedSignatures.includes(s));
    },
    signs() {
      return Object.keys(this.d.signatures)
        .filter(s => this.d.signatures[s])
        .map(s => ({
          ...this.d.signatures[s],
          type: s,
        }));
    },
    hasSigns() {
      return Object.keys(this.signs).length > 0;
    },
    ok() {
      return this.emptySignatures.length === 0;
    },
    invalidMessage() {
      if (!this.noOGRN || this.selectedSignatureMode !== 'Медицинская организация') {
        return null;
      }

      return 'Отсутствует ОГРН в сертификате';
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
  mounted() {
    this.$root.$on('eds:fast-sign', (pk, type) => {
      if (pk === this.d.pk && this.emptyAllowedSignatures.includes(type)) {
        this.selectedSignatureMode = type;
        this.addSign(true);
      }
    });
  },
  methods: {
    fileHref(fileContent, type) {
      let body = fileContent || '';
      if (!body) {
        return null;
      }
      const isString = typeof body === typeof '';
      body = isString ? body : new Uint8Array(body);
      const dataStr = isString
        ? encodeURIComponent(body)
        : btoa(body.reduce((data, byte) => data + String.fromCharCode(byte), ''));
      return `data:${type},${dataStr}`;
    },
    signFileName(sign) {
      return `${this.d.fileName}-${sign.type}.sgn`;
    },
    async sendToVI() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { data } = await this.$api('/directions/send-to-l2vi', this.d, 'pk');
      if (data.ok) {
        this.$root.$emit('msg', 'ok', 'Успешная отправка!');
      } else {
        // eslint-disable-next-line no-console
        console.log(data);
        this.$root.$emit('msg', 'error', 'Ошибка!');
      }
      await this.$store.dispatch(actions.DEC_LOADING);
      this.$root.$emit('eds:reload-document', this.direction);
    },
    async addSign(fast = false) {
      if (this.invalidMessage) {
        this.$error(this.invalidMessage);
        return;
      }
      if (!fast) {
        try {
          await this.$dialog.confirm(
            `Подтвердите подпись вложения документа №${this.direction} — ${this.d.type} как "${this.selectedSignatureMode}"`,
          );
        } catch (e) {
          return;
        }
      }
      await this.$store.dispatch(actions.INC_LOADING);
      try {
        let body = this.d.fileContent;
        if (this.d.type === 'PDF') {
          body = Uint8Array.from(atob(body), c => c.charCodeAt(0));
        }
        const isString = typeof body === typeof '';

        const bodyEncoded = isString ? body : new Uint8Array(body);

        const m = await createHash(bodyEncoded);
        const sign = await createDetachedSignature(this.thumbprint, m);
        let cert = null;
        try {
          cert = await getCertificate(this.thumbprint);
        } catch (e) {
          // eslint-disable-next-line no-console
          console.log(e);
        }
        const { ok, message } = await this.$api('/directions/eds/add-sign', {
          pk: this.d.pk,
          sign,
          mode: this.selectedSignatureMode,
          certThumbprint: this.thumbprint,
          certDetails: cert ? {
            subjectName: cert.subjectName,
            validFrom: cert.validFrom,
            validTo: cert.validTo,
          } : null,
        });

        if (ok) {
          this.$root.$emit('eds:reload-document', this.direction);
          this.$root.$emit(
            'msg',
            'ok',
            `Подпись успешно добавлена: ${this.direction}, ${this.d.type}, ${this.selectedSignatureMode}`,
            2000,
          );
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      } catch (e) {
        // eslint-disable-next-line no-console
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

  &-ok {
    border-color: #049372;
    background: linear-gradient(to bottom, #04937212 0%, #04937230 100%);
  }
}

.doc-header {
  font-weight: bold;
  padding-bottom: 5px;
  border-bottom: 1px solid #bbb;
}

.sign-block {
  margin: 10px 0;
  max-width: 500px;

  & + & {
    margin-top: 0;
  }
}

.has-signs {
  margin: 10px 0;

  &-header {
    font-weight: bold;
  }
}

.sign-block + .has-signs {
  margin-top: 0;
}

.block-header {
  font-weight: bold;
}

.download-block {
  margin-top: 5px;
}
</style>
