<template>
  <div class="slot" :class="`slot-status-${data.status}`" :style="`top: ${offset}; min-height: ${minHeight};`">
    <div class="slot-inner" @click="open">
      <div v-if="data.patient" class="patient-row">{{ data.patient.fio }}</div>
      <div v-if="data.service" class="service-row">{{ data.service.title }}</div>
      <div class="param-row"><i class="far fa-circle"></i> {{ data.duration }} мин</div>
    </div>

    <MountingPortal mountTo="#portal-place-modal" name="TimeSlotPopup" append>
      <transition name="fade">
        <modal
          v-if="isOpened"
          @close="close"
          show-footer="true"
          white-bg="true"
          max-width="400px"
          width="100%"
          marginLeftRight="auto"
        >
          <span slot="header">{{ data.date }} {{ data.time }}</span>
          <div slot="body" class="popup-body">
            TODO
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-6">
                <button @click="close" class="btn btn-blue-nb" type="button">
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
import Vue from 'vue';
import Component from 'vue-class-component';
import Modal from '@/ui-cards/Modal.vue';

@Component({
  components: {
    Modal,
  },
  props: {
    data: {
      type: Object,
      required: true,
    },
    allHoursValues: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      isOpened: false,
    };
  },
})
export default class TimeSlot extends Vue {
  data: any;

  allHoursValues: any[];

  isOpened: boolean;

  get offset() {
    const offset = this.data.minute * 2 + this.allHoursValues.indexOf(this.data.hourValue) * 120 + 51;
    return `${offset}px`;
  }

  get minHeight() {
    return `${this.data.duration * 2}px`;
  }

  open() {
    this.isOpened = true;
  }

  close() {
    this.isOpened = false;
  }
}
</script>

<style lang="scss" scoped>
$slot-minimal-height: 12px;
$slot-minimal-height-opened: 60px;
$slot-left-offset: 38px;
$slot-padding: 1px;

.patient-row,
.service-row,
.param-row {
  white-space: nowrap;
  overflow: hidden;

  font-size: 12px;
}

.patient-row + .param-row,
.service-row + .param-row {
  margin-top: 2px;
  border-top: 1px solid #bbb;
}

.param-row {
  padding: 0 2px;
  line-height: 14px;

  .fa {
    font-size: 10px;
  }
}

.patient-row {
  font-weight: bold;
}

.slot {
  position: absolute;
  cursor: pointer;

  left: $slot-left-offset;
  right: 0;
  z-index: 1;

  &-inner {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    padding: $slot-padding $slot-padding * 3;
  }

  border-radius: $slot-padding * 3;
  min-height: $slot-minimal-height;
  line-height: 1;
  border: 1px solid rgb(176, 176, 176);
  background: linear-gradient(to bottom, rgb(250, 250, 250) 0%, rgb(219, 219, 219) 100%);
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);

  &:hover {
    box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
    z-index: 2;
    transform: scale(1.008);
    min-height: $slot-minimal-height-opened;

    .patient-row,
    .service-row,
    .param-row {
      white-space: unset;
    }
  }
}

.popup-body {
  min-height: 350px;
}
</style>
