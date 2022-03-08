<template>
  <div v-frag>
    <ul
      v-show="showStatus"
      class="nav navbar-nav"
    >
      <li>
        <a
          v-tippy="{
            html: `#${tippyId}`,
            placement: 'bottom',
            arrow: true,
            reactive: true,
            interactive: true,
            theme: 'light bordered',
            zIndex: 4999,
            popperOptions: {
              modifiers: {
                preventOverflow: {
                  boundariesElement: 'window',
                },
                hide: {
                  enabled: false,
                },
              },
            },
          }"
          href="#"
          @click.prevent
        >
          <i
            v-if="status !== 'available'"
            class="fa fa-circle status"
            :class="`status-${status}`"
          /> Экспертиза
        </a>
      </li>
    </ul>

    <div
      :id="tippyId"
      class="tp"
    >
      <div class="tp-title">
        Экспертиза для протокола {{ pk }}
      </div>
      <div>Статус: {{ statusTitle }}</div>
      <ul v-if="directions.length > 0">
        <li
          v-for="d in directions"
          :key="d.pk"
        >
          {{ d.pk }} — {{ d.serviceTitle }},
          <span v-if="d.confirmedAt">{{ d.confirmedAt }}</span>
          <span v-else>не подтверждено</span> —
          <a
            href="#"
            class="a-under"
            @click.prevent="open(d.pk)"
          >{{ d.confirmedAt ? 'открыть' : 'редактировать' }}</a>
        </li>
      </ul>
      <button
        v-if="showFillButton"
        class="btn btn-blue-nb"
        type="button"
        @click="open(-1)"
      >
        Заполнить новую экспертизу
      </button>
    </div>

    <MountingPortal
      mount-to="#portal-place-modal"
      name="ExpertiseStatus_embedded"
      append
    >
      <transition name="fade">
        <Modal
          v-if="embeddedPk"
          ref="modalEmbedded"
          white-bg="true"
          width="100%"
          margin-left-right="34px"
          margin-top="30px"
          show-footer="true"
          @close="hideModalEmbedded"
        >
          <span slot="header">Заполнение экспертизы</span>
          <div
            v-if="canCreateExpertise && !withoutPreview"
            slot="body"
            class="embedded-body"
          >
            <div class="le">
              <iframe
                :src="toEnterUrl"
                name="toEnterEmbedded"
              />
            </div>
            <div class="re">
              <iframe
                :src="toEnterPdfUrl"
                name="toEnterPdf"
              />
            </div>
          </div>
          <div
            v-else
            slot="body"
            class="embedded-body"
          >
            <iframe
              :src="toEnterUrl"
              name="toEnterEmbedded"
            />
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-4">
                <button
                  class="btn btn-primary-nb btn-blue-nb"
                  type="button"
                  @click="hideModalEmbedded"
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

export default {
  name: 'ExpertiseStatus',
  components: { Modal },
  props: {
    withoutPreview: {
      type: Boolean,
      default: false,
      required: false,
    },
  },
  data() {
    return {
      status: 'empty',
      pk: -1,
      directions: [],
      serviceId: null,
      serviceTitle: null,
      canCreateExpertise: false,
      embeddedPk: null,
      loading: false,
    };
  },
  computed: {
    showStatus() {
      return !!this.status && this.status !== 'empty' && this.pk !== -1;
    },
    tippyId() {
      return `expertise-status-${this.pk}`;
    },
    statusTitle() {
      return (
        {
          available: 'доступно для заполнения',
          ok: 'без замечаний',
          error: 'есть замечания',
        }[this.status] || ''
      );
    },
    showFillButton() {
      return (
        this.canCreateExpertise && (this.directions.length === 0 || !!this.directions[this.directions.length - 1].confirmedAt)
      );
    },
    toEnterUrl() {
      return `/ui/results/descriptive?embedded=1&embeddedFull=1#{"pk":${this.embeddedPk}}`;
    },
    toEnterPdfUrl() {
      return `/results/pdf?pk=${JSON.stringify([this.pk])}&leftnone=1&embedded=1`;
    },
  },
  mounted() {
    this.$root.$on('open-pk', (pk) => {
      this.status = 'empty';
      this.pk = pk;
      this.loadStatus();
    });
  },
  methods: {
    async open(pk) {
      if (pk === -1) {
        if (this.loading) {
          return;
        }
        this.loading = true;
        const { pk: pkToOpen } = await this.$api('directions/expertise-create', this, 'pk');
        this.loadStatus(true);
        this.open(pkToOpen);
        this.loading = false;
      } else {
        this.embeddedPk = pk;
      }
    },
    async loadStatus(reload = false) {
      if (!reload) {
        this.status = 'empty';
        this.directions = [];
        this.serviceId = null;
        this.serviceTitle = null;
        this.canCreateExpertise = false;
      }
      if (this.pk !== -1) {
        const statusData = await this.$api('directions/expertise-status', this, 'pk');
        this.status = statusData.status;
        this.directions = statusData.directions;
        this.serviceId = statusData.serviceId;
        this.serviceTitle = statusData.serviceTitle;
        this.canCreateExpertise = statusData.canCreateExpertise;
      }
    },
    hideModalEmbedded() {
      this.embeddedPk = null;
      this.loadStatus(true);
    },
  },
};
</script>

<style lang="scss" scoped>
.status {
  text-shadow: 0 0 1px #fff;
  display: inline-block;
  margin-right: 2px;

  &-error {
    color: #cf3a24;
  }

  &-available {
    color: #f4d03f;
  }

  &-ok {
    color: #049372;
  }
}

.tp {
  text-align: left;
  padding: 1px;

  max-width: 1000px;

  .btn {
    width: 100%;
    padding: 4px;
    margin-top: 5px;
  }
}

.tp-title {
  font-weight: bold;
  margin-bottom: 5px;
}

.embedded-body {
  height: calc(100vh - 179px);
  position: relative;

  .le,
  .re {
    position: absolute;
    top: 0;
    bottom: 0;
  }

  .le {
    left: 0;
    right: 50%;
  }

  .re {
    left: calc(50% + 1px);
    right: 0;
  }

  iframe {
    display: block;
    width: 100%;
    height: 100%;
    border: none;
  }
}
</style>
