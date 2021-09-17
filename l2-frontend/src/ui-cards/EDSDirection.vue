<template>
  <div v-frag>
    <button class="btn btn-blue-nb nbr" @click="modal_opened = true" v-if="visible">
      ЭЦП
    </button>

    <div
      class="eds-status"
      :class="d.status && 'eds-status-ok'"
      v-for="d in requiredDocuments"
      :key="d.type"
      :title="
        `Есть подписи: ${d.has.join('; ') || 'пусто'}` + (d.empty.length > 0 ? `; Нужны подписи: ${d.empty.join('; ')}` : '')
      "
      v-tippy
    >
      <i class="fa fa-certificate"></i> {{ d.type }}
    </div>

    <MountingPortal mountTo="#portal-place-modal" :name="`EDSDirection_modal_${directionPk}`" append>
      <transition name="fade">
        <modal
          v-if="modal_opened"
          ref="modal"
          @close="hide_modal"
          show-footer="true"
          white-bg="true"
          width="100%"
          max-width="1020px"
          marginLeftRight="auto"
          margin-top="30px"
        >
          <span slot="header">Подписать ЭЦП результат направления {{ directionPk }}</span>
          <div slot="body" class="eds-body">
            <EDSSigner :direction-pk="directionPk" />
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
  },
  data() {
    return {
      modal_opened: false,
      requiredDocuments: [],
    };
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
      await this.$store.dispatch(actions.INC_LOADING);
      const { documents } = await this.$api('/directions/eds/required-signatures', {
        pk: this.directionPk,
      });
      this.requiredDocuments = documents;
      await this.$store.dispatch(actions.DEC_LOADING);
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
