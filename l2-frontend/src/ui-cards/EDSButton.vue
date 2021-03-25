<template>
  <fragment v-if="direction.all_confirmed && eds">
    <button class="btn btn-blue-nb nbr" @click="modal_opened = true">
      Подписать ЭЦП
    </button>
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
  </fragment>
</template>

<script>
import Modal from "@/ui-cards/Modal";
import * as action_types from "@/store/action-types";
import axios from "axios";

export default {
  name: 'EDSButton',
  components: {
    Modal,
  },
  props: {
    directionData: {},
  },
  data() {
    return {
      modal_opened: false,
      edsMounted: false,
    }
  },
  mounted() {
    window.addEventListener("message", this.edsMessage, false);
  },
  beforeDestroy() {
    window.removeEventListener("message", this.edsMessage, false)
  },
  methods: {
    hide_modal() {
      this.modal_opened = false;
      this.edsMounted = false;
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none'
      }
    },
    edsMessage(e) {
      if (e && e.data && e.data.event === 'eds:mounted') {
        this.edsMounted = true;
      }
    },
    async loadDocuments() {
      await this.$store.dispatch(action_types.INC_LOADING);
      const documents = [];
      const config = {
          method: 'get',
          url: `/results/pdf?pk=[${this.direction.pk}]&split=1&leftnone=0&inline=1&protocol_plain_text=1`,
          responseType: "arraybuffer"
      };
      const pdfResult = await axios(config);
      documents.push({
        type: 'PDF',
        data: pdfResult.data,
      })
      window.frames.eds.passEvent('set-documents', this.directionData, documents, {
        token: this.eds_token,
      });
      await this.$store.dispatch(action_types.DEC_LOADING);
    },
  },
  watch: {
    edsMounted() {
      if (this.edsMounted) {
        this.loadDocuments();
      }
    },
  },
  computed: {
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
  },
}
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
</style>
