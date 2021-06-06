<template>
  <div v-frag>
    <button class="btn btn-blue-nb nbr" @click="modal_opened = true" v-if="visible">
      ЭЦП
    </button>
    <template v-if="edsStatus.ok">
      <div
        class="eds-status"
        :class="s.ok && 'eds-status-ok'"
        v-for="(s, i) in edsStatus.signatures"
        :key="i"
        :title="
        `Есть подписи: ${s.executors.join('; ') || 'пусто'}` +
        (s.needSignatures.length > 0 ? `; Нужны подписи: ${s.needSignatures.join('; ')}`: '')
        "
        v-tippy
      >
        <i class="fa fa-certificate"></i> {{ s.type }}
      </div>
    </template>
    <modal v-if="modal_opened" ref="modal" @close="hide_modal" show-footer="true"
           white-bg="true" width="100%" marginLeftRight="34px" margin-top="30px">
      <span slot="header">Подписать ЭЦП результат направления {{ direction.pk }}</span>
      <div slot="body" class="eds-body">
        <iframe :src="eds_base" name="eds"></iframe>
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button @click="hide_modal" class="btn btn-primary-nb btn-blue-nb" type="button">
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </modal>
  </div>
</template>

<script lang="ts">
import Modal from '@/ui-cards/Modal.vue';
import * as actions from '@/store/action-types';
import axios from 'axios';

export const EDS_API = axios.create({
  baseURL: '/mainmenu/eds/eds',
});

export default {
  name: 'EDSButton',
  components: {
    Modal,
  },
  props: {
    directionData: {},
    issData: {},
  },
  data() {
    return {
      modal_opened: false,
      edsMounted: false,
      edsStatus: {
        signatures: [],
      },
      requiredSignatures: [],
      requiredEDSDocTypes: [],
    };
  },
  mounted() {
    window.addEventListener('message', this.edsMessage, false);
    this.$root.$on('EDS:archive-document', () => this.archive());
  },
  beforeDestroy() {
    window.removeEventListener('message', this.edsMessage, false);
  },
  methods: {
    hide_modal() {
      this.modal_opened = false;
      this.edsMounted = false;
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
      this.loadStatus();
    },
    edsMessage(e) {
      if (e && e.data && e.data.event === 'eds:mounted') {
        this.edsMounted = true;
      }
    },
    async loadDocuments() {
      await this.$store.dispatch(actions.INC_LOADING);
      await this.loadStatus();
      const documents = [];
      const urlPdf = `/results/pdf?pk=[${this.direction.pk}]&split=1&leftnone=0&inline=1&protocol_plain_text=1`;
      const config = {
        method: 'GET',
      };
      const cdaResult = await EDS_API.post('cda', {
        token: this.eds_token,
        pk: this.directionData.direction.pk,
      }).then(r => r.data);
      if (!cdaResult.ok || !cdaResult.savedPDF) {
        const pdfResult = await fetch(urlPdf, config).then(r => r.arrayBuffer());
        documents.push({
          type: 'PDF',
          data: pdfResult,
        });
      } else {
        documents.push({
          type: 'PDF',
          data: Uint8Array.from(atob(cdaResult.savedPDF), c => c.charCodeAt(0)),
        });
      }
      if (cdaResult.ok) {
        if (cdaResult.needCda && cdaResult.cda) {
          documents.push({
            type: 'CDA',
            data: cdaResult.cda,
          });
        }
      } else {
        window.errmessage('CDA XML не получен');
      }
      window.frames.eds.passEvent('set-data', {
        ...this.directionData,
        confirmedAt: this.issData.confirmed_at,
      }, documents, {
        token: this.eds_token,
        requiredSignatures: this.requiredSignatures,
        requiredEDSDocTypes: this.requiredEDSDocTypes,
        allowedSign: this.eds_allowed_sign,
      });
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async archive() {
      await EDS_API.post('archive-document', {
        token: this.eds_token,
        pk: this.directionData.direction.pk,
        confirmedAt: this.issData.confirmed_at,
        hospitalTFOMSCode: this.directionData.direction.hospitalTFOMSCode,
      });
    },
    async loadStatus() {
      const requiredResult = await EDS_API.post('cda', {
        token: this.eds_token,
        pk: this.directionData.direction.pk,
        confirmedAt: this.issData.confirmed_at,
        hospitalTFOMSCode: this.directionData.direction.hospitalTFOMSCode,
        withoutRender: true,
      }).then(r => r.data);

      this.requiredSignatures = requiredResult.signsRequired || ['Врач'];
      this.requiredEDSDocTypes = requiredResult.needCda ? ['PDF', 'CDA'] : ['PDF'];

      this.edsStatus = (await EDS_API.post('signature-status', {
        token: this.eds_token,
        pk: this.directionData.direction.pk,
        confirmedAt: this.issData.confirmed_at,
        hospitalTFOMSCode: this.directionData.direction.hospitalTFOMSCode,
        requiredSignatures: requiredResult.signsRequired,
        requiredEDSDocTypes: this.requiredEDSDocTypes,
      })).data;

      this.$root.$emit('EDS:has-signs', (this.edsStatus.signatures || []).some(s => s.executors.length > 0));
    },
  },
  watch: {
    edsMounted() {
      if (this.edsMounted) {
        setTimeout(() => this.loadDocuments(), 500);
      }
    },
    visible: {
      immediate: true,
      handler() {
        if (this.visible) {
          this.loadStatus();
        }
      },
    },
  },
  computed: {
    visible() {
      return this.direction.all_confirmed && this.eds;
    },
    direction() {
      return this.directionData.direction;
    },
    eds() {
      return this.$store.getters.modules.l2_eds;
    },
    eds_base() {
      return '/mainmenu/eds';
    },
    eds_token() {
      return this.$store.getters.user_data.eds_token;
    },
    eds_allowed_sign() {
      return this.$store.getters.user_data.eds_allowed_sign;
    },
  },
};
</script>

<style scoped lang="scss">
.eds-body {
  height: calc(100vh - 179px);
  position: relative;

  iframe {
    display: block;
    width: 100%;
    height: 100%;
    border: none;
  }
}

.btn.nbr {
  margin: 0 5px;
}

.eds-status {
  align-self: stretch;
  padding: 5px;
  white-space: nowrap;
  color: red;

  &-ok {
    color: green;
  }
}
</style>
