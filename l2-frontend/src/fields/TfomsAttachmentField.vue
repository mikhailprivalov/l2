<template>
  <div class="input-group">
    <button
      v-if="!val && !disabled"
      class="btn btn-blue-nb nbr btn-address"
      type="button"
      tabindex="-1"
      @click="gen"
    >
      Загрузить данные из ТФОМС
    </button>
    <div class="form-control form-control-area">
      {{ val || 'не загружено' }}
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';

import * as actions from '@/store/action-types';
import directionsPoint from '@/api/directions-point';

@Component({
  props: {
    value: {
      type: String,
      required: true,
    },
    clientPk: {
      type: Number,
      required: true,
    },
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      val: '',
    };
  },
  model: {
    event: 'modified',
  },
  watch: {
    value: {
      handler() {
        this.val = this.value;
      },
      immediate: true,
    },
    val() {
      this.changeValue();
    },
  },
})
export default class TfomsAttachmentField extends Vue {
  value: string;

  val: string;

  disabled: boolean;

  clientPk: number;

  changeValue() {
    this.$emit('modified', this.val);
  }

  async gen() {
    if (this.disabled) {
      return;
    }

    await this.$store.dispatch(actions.INC_LOADING);

    const { ok, message, value } = await directionsPoint.lastFieldResult(this, 'clientPk', { fieldPk: '%tfoms-attachment' });

    if (ok && message) {
      this.$root.$emit('msg', 'ok', message);
    } else if (message) {
      this.$root.$emit('msg', 'warning', message);
    }

    if (value) {
      this.val = value;
    }

    await this.$store.dispatch(actions.DEC_LOADING);
  }
}
</script>
