<template>
  <div v-frag>
    <button
      v-if="visible"
      class="btn btn-blue-nb nbr"
      @click="modal_opened = true"
    >
      <i
        v-if="documentsPrefetched"
        class="fa fa-eye"
      />
      <template v-else>
        ЭЦП
      </template>
    </button>

    <div
      v-for="d in requiredDocuments"
      :key="d.type"
      v-tippy
      class="eds-status"
      :class="d.status && 'eds-status-ok'"
      :title="
        `Есть подписи: ${d.has.join('; ') || 'пусто'}` + (d.empty.length > 0 ? `; Нужны подписи: ${d.empty.join('; ')}` : '')
      "
    >
      <i class="fa fa-certificate" /> {{ d.type }}
    </div>

    <MountingPortal
      mount-to="#portal-place-modal"
      :name="`EDSDirection_modal_${directionPk}`"
      append
    >
      <transition name="fade">
        <Modal
          v-if="modal_opened"
          ref="modal"
          show-footer="true"
          white-bg="true"
          width="100%"
          max-width="1020px"
          margin-left-right="auto"
          margin-top="30px"
          @close="hide_modal"
        >
          <span slot="header">Подписать ЭЦП результат направления {{ directionPk }}</span>
          <div
            slot="body"
            class="eds-body"
          >
            <EDSSigner :direction-pk="directionPk" />
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-4">
                <button
                  class="btn btn-primary-nb btn-blue-nb"
                  type="button"
                  @click="hide_modal"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </Modal>
      </transition>
    </MountingPortal>
  </div>
</template>

<script lang="ts">
import Modal from '@/ui-cards/Modal.vue';
import * as actions from '@/store/action-types';

export default {
  name: 'EDSDirection',
  components: {
    Modal,
    EDSSigner: () => import('@/ui-cards/EDSSigner.vue'),
  },
  props: {
    all_confirmed: {
      type: Boolean,
    },
    directionPk: {
      type: Number,
      required: true,
    },
    documentsPrefetched: {
      type: Array,
      required: false,
    },
  },
  data() {
    return {
      inited: false,
      modal_opened: false,
      requiredDocuments: [],
    };
  },
  computed: {
    visible() {
      return this.all_confirmed && this.eds;
    },
    eds() {
      return this.$store.getters.modules.l2_eds;
    },
    eds_base() {
      return '/mainmenu/eds';
    },
    eds_allowed_sign() {
      return this.$store.getters.user_data.eds_allowed_sign;
    },
  },
  watch: {
    visible: {
      immediate: true,
      handler() {
        if (this.visible) {
          this.loadStatus();
        }
      },
    },
  },
  methods: {
    hide_modal() {
      this.modal_opened = false;
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
      this.loadStatus();
    },
    async loadStatus() {
      if (this.documentsPrefetched && !this.inited) {
        this.inited = true;
        this.requiredDocuments = this.documentsPrefetched;
        return;
      }
      this.inited = true;
      await this.$store.dispatch(actions.INC_LOADING);
      const { documents } = await this.$api('/directions/eds/required-signatures', {
        pk: this.directionPk,
      });
      this.requiredDocuments = documents;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style scoped lang="scss">
.eds-body {
  height: calc(100vh - 179px);
  position: relative;
}

.btn.nbr {
  margin: 0 5px;
}

.eds-status {
  align-self: stretch;
  padding: 5px;
  white-space: nowrap;
  color: #932a04;
  text-shadow: 0 0 7px #fff;

  &-ok {
    color: #049372;
  }
}
</style>
