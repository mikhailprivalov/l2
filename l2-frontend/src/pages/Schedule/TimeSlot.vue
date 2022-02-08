<template>
  <div
    class="slot"
    :class="[`slot-status-${data.status}`, mode === 'list' ? 'slot-list' : 'slot-natural']"
    :style="mode === 'list' ? '' : `top: ${offset}; min-height: ${minHeight};`"
  >
    <div class="slot-inner" @click="open">
      <div v-if="data.patient" class="patient-row">{{ data.patient.fio }}</div>
      <div v-if="data.service" class="service-row">{{ data.service.title }}</div>
      <div class="param-row">
        <span v-if="mode === 'list'">{{ smallTime(data.time) }}</span>
        <i class="far fa-circle"></i> {{ data.duration }} мин
      </div>
    </div>

    <MountingPortal mountTo="#portal-place-modal" :name="`TimeSlotPopup-${smallTime(data.time)}—${data.date}`" append>
      <transition name="fade">
        <modal
          v-if="isOpened"
          @close="close"
          show-footer="true"
          white-bg="true"
          max-width="710px"
          width="100%"
          marginLeftRight="auto"
        >
          <span slot="header">{{ data.date }} {{ data.time }}</span>
          <div slot="body" class="popup-body">
            <div class="preloader" v-if="!details"><i class="fa fa-spinner"></i> загрузка</div>
            <div v-else>
              <div class="patient-root">
                <PatientSmallPicker v-model="details.cardId" :base_pk="details.baseId" />
              </div>
            </div>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-6">
                <button @click="close" class="btn btn-blue-nb" type="button">Закрыть</button>
              </div>
              <div class="col-xs-6">
                <button @click="save" class="btn btn-blue-nb" type="button">Сохранить</button>
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
import * as actions from '@/store/action-types';
import Modal from '@/ui-cards/Modal.vue';
import PatientSmallPicker from '@/ui-cards/PatientSmallPicker.vue';

@Component({
  components: {
    Modal,
    PatientSmallPicker,
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
    mode: {
      type: String,
    },
  },
  data() {
    return {
      isOpened: false,
      details: null,
      selectedCard: {},
    };
  },
})
export default class TimeSlot extends Vue {
  data: any;

  details: any;

  selectedCard: any;

  allHoursValues: any[];

  isOpened: boolean;

  mode: string | null;

  get offset() {
    const offset = this.data.minute * 2 + this.allHoursValues.indexOf(this.data.hourValue) * 120 + 51;
    return `${offset}px`;
  }

  get minHeight() {
    return `${this.data.duration * 2}px`;
  }

  async loadData() {
    this.details = null;
    await this.$store.dispatch(actions.INC_LOADING);
    const { ok, data } = await this.$api('/schedule/details', this.data, 'id');
    this.details = data;

    if (!ok) {
      this.close();
      this.$root.$emit('msg', 'error', 'Не удалось загрузить данные!');
    } else if (this.details.patient) {
      setTimeout(() => {
        this.$root.$emit('select_card', this.details.patient);
        this.$store.dispatch(actions.DEC_LOADING);
      }, 200);
      return;
    }

    await this.$store.dispatch(actions.DEC_LOADING);
  }

  // eslint-disable-next-line class-methods-use-this
  smallTime(t) {
    const [h, m] = t.split(':');
    return `${h}:${m}`;
  }

  open() {
    this.isOpened = true;
    this.loadData();
  }

  close() {
    this.isOpened = false;
  }

  async save() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { ok, message } = await this.$api('/schedule/save', {
      ...this.data,
      ...this.details,
    });

    if (ok) {
      this.$root.$emit('msg', 'ok', 'Сохранено');
      this.close();
    } else {
      this.$root.$emit('msg', 'error', message);
    }

    this.$root.$emit('reload-slots');

    await this.$store.dispatch(actions.DEC_LOADING);
  }
}
</script>

<style lang="scss" scoped>
$slot-minimal-height: 12px;
$slot-minimal-height-opened: 60px;
$slot-left-offset: 38px;
$slot-padding: 1px;

.patient-root {
  height: 110px;
}

.preloader {
  text-align: center;
  padding: 20px;
}

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
  cursor: pointer;

  &.slot-natural {
    position: absolute;

    left: $slot-left-offset;
    right: 0;
    z-index: 1;
  }

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

  &-list {
    min-height: $slot-minimal-height * 3;
    margin-bottom: 3px;
    position: relative;
  }

  &:hover {
    box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
    z-index: 2;
    transform: scale(1.008);
    &.slot-natural {
      min-height: $slot-minimal-height-opened;
    }

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
