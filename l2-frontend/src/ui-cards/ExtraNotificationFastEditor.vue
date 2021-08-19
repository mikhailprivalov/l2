<template>
  <div v-frag>
    <div class="input-group" v-if="editing">
      <input type="text" class="form-control" @keypress.enter="save" v-model="localValue" placeholder="Введите значение" />
      <span class="input-group-btn">
        <button class="btn btn-blue-nb" title="Сохранить" @click="save(false)" v-tippy v-if="!loading">
          <i class="fas fa-save"></i>
        </button>
        <button class="btn btn-blue-nb" v-else disabled>
          <i class="fa fa-spinner"></i>
        </button>
      </span>
      <span class="input-group-btn">
        <button
          class="btn btn-blue-nb btn-2icons"
          title="Сохранить и подтвердить"
          @click="save(true)"
          v-tippy
          :disabled="!valid"
          v-if="!loading"
        >
          <i class="fas fa-save"></i>
          <i class="fas fa-check"></i>
        </button>
        <button class="btn btn-blue-nb" v-else disabled>
          <i class="fa fa-spinner"></i>
        </button>
      </span>
    </div>
    <div v-else class="inner-text">
      {{ data.value || 'не заполнено' }}
    </div>
  </div>
</template>

<script lang="ts">
import Vue, { PropType } from 'vue';
import Component from 'vue-class-component';
import { ExtraNotificationData } from '@/types/extraNotification';
import * as actions from '@/store/action-types';

@Component({
  props: {
    data: {
      type: Object as PropType<ExtraNotificationData>,
      required: true,
    },
    canEdit: {
      type: Boolean,
    },
  },
  data() {
    return {
      localValue: '',
      loading: false,
    };
  },
  watch: {
    value: {
      immediate: true,
      handler() {
        this.localValue = this.value;
      },
    },
  },
})
export default class ExtraNotificationFastEditor extends Vue {
  canEdit: boolean;

  data: ExtraNotificationData;

  localValue: string;

  loading: boolean;

  $dialog: any;

  get value() {
    return this.data.value || '';
  }

  get editing() {
    return this.canEdit && !this.data.slaveConfirm;
  }

  get valid() {
    return this.localValue.trim().length > 0;
  }

  async save(withConfirm = false) {
    if (withConfirm) {
      try {
        await this.$dialog.confirm('Вы действительно хотите сохранить и подтвердить результат?');
      } catch (_) {
        return;
      }
    }
    this.loading = true;
    await this.$store.dispatch(actions.INC_LOADING);
    const {
      ok, message, value, slaveConfirm,
    } = await this.$api('extra-notification/save', {
      pk: this.data.slaveDir,
      value: this.localValue.trim(),
      withConfirm,
    });
    if (ok) {
      this.$root.$emit('msg', 'ok', 'Сохранено', 3000);
      if (withConfirm) {
        this.$root.$emit('msg', 'ok', 'Подтверждено', 3000);
      }
      this.data.value = value;
      this.data.slaveConfirm = slaveConfirm;
    } else {
      this.$root.$emit('msg', 'error', `Не сохранено: ${message}`);
    }
    await this.$store.dispatch(actions.DEC_LOADING);
    this.loading = false;
  }
}
</script>

<style lang="scss" scoped>
.inner-text {
  padding: 5px;
}

.form-control,
.btn {
  padding: 2px 12px;
  height: 30px;
}

.btn-2icons {
  .fas {
    display: inline-block;
    margin: 0 -5px;
    position: relative;

    &:first-child {
      opacity: 0.85;
      transform: scale(0.9);
    }

    &:last-child {
      filter: drop-shadow(0 0 1px #9da6b1);
    }
  }
}
</style>
