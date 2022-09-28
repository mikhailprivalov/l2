<template>
  <div class="input-group">
    <button
      v-if="!val && !disabled"
      class="btn btn-blue-nb nbr btn-address"
      type="button"
      tabindex="-1"
      @click="gen"
    >
      Сгенерировать номер
    </button>
    <button
      v-else-if="!disabled"
      class="btn btn-blue-nb nbr btn-address"
      type="button"
      tabindex="-1"
      @click="free"
    >
      Освободить номер
    </button>
    <div class="form-control form-control-area">
      {{ val || 'номер не сгенерирован' }}
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';

import * as actions from '@/store/action-types';

@Component({
  props: {
    value: {
      type: String,
      required: true,
    },
    numberKey: {
      type: String,
      required: true,
    },
    issPk: {
      type: Number,
      required: true,
    },
    fieldPk: {
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
  mounted() {
    this.checkVal();
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
export default class NumberGeneratorField extends Vue {
  value: string;

  numberKey: string;

  val: string;

  disabled: boolean;

  issPk: number;

  fieldPk: number;

  changeValue() {
    this.$emit('modified', this.val);
  }

  checkVal() {
    if (this.val === this.numberKey) {
      this.val = '';
    }
  }

  async gen() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { ok, message, number } = await this.$api('/directions/gen-number', this, ['numberKey', 'fieldPk', 'issPk']);
    if (ok) {
      this.val = number;

      if (message) {
        this.$root.$emit('msg', 'warning', message);
      }

      this.$root.$emit('msg', 'ok', 'Номер сгенерирован');
    } else {
      this.$root.$emit('msg', 'error', message);
    }
    await this.$store.dispatch(actions.DEC_LOADING);
  }

  async free() {
    try {
      await this.$dialog.confirm(
        'Вы действительно хотите освободить номер? Освобождённый номер может быть использован в другом протоколе',
      );
    } catch (_) {
      return;
    }
    await this.$store.dispatch(actions.INC_LOADING);
    const { ok, message } = await this.$api('/directions/free-number', this, ['numberKey', 'fieldPk', 'issPk']);
    if (ok) {
      this.val = '';

      this.$root.$emit('msg', 'ok', 'Номер освобождён');
    } else {
      this.$root.$emit('msg', 'error', message);
    }
    await this.$store.dispatch(actions.DEC_LOADING);
  }
}
</script>
