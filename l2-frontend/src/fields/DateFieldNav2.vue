<template>
  <div class="flex">
    <template v-if="!right">
      <button
        class="btn btn-blue-nb"
        type="button"
        :disabled="disabled || readonly"
        @click="decDate"
      >
        <i
          class="glyphicon glyphicon-arrow-left"
        />
      </button>
      <button
        class="btn btn-blue-nb"
        type="button"
        :disabled="disabled || readonly"
        @click="incDate"
      >
        <i
          class="glyphicon glyphicon-arrow-right"
        />
      </button>
    </template>
    <input
      v-model="val"
      type="date"
      class="form-control no-context"
      :class="{brn: brn}"
      :style="{ width: w }"
      maxlength="10"
      :disabled="disabled"
      :readonly="readonly"
    >
    <template v-if="right">
      <button
        class="btn btn-blue-nb"
        type="button"
        :disabled="disabled || readonly"
        @click="decDate"
      >
        <i
          class="glyphicon glyphicon-arrow-left"
        />
      </button>
      <button
        class="btn btn-blue-nb"
        type="button"
        :disabled="disabled || readonly"
        @click="incDate"
      >
        <i
          class="glyphicon glyphicon-arrow-right"
        />
      </button>
    </template>
  </div>
</template>

<script lang="ts">
import moment from 'moment';

export default {
  name: 'DateFieldNav2',
  model: {
    event: 'modified',
  },
  props: {
    value: {
      type: String,
      default: '',
    },
    w: {
      default: '94px',
    },
    brn: {
      default: true,
      type: Boolean,
    },
    right: {
      default: false,
      type: Boolean,
    },
    disabled: {
      default: false,
      type: Boolean,
    },
    readonly: {
      default: false,
      type: Boolean,
    },
  },
  data() {
    return {
      val: this.value,
    };
  },
  computed: {
    md() {
      return moment(this.val, 'YYYY-MM-DD');
    },
  },
  watch: {
    val() {
      this.emitv();
    },
  },
  methods: {
    decDate() {
      const a = this.md.clone();
      a.subtract(1, 'days');
      this.emit(a);
    },
    incDate() {
      const a = this.md.clone();
      a.add(1, 'days');
      this.emit(a);
    },
    emit(v) {
      this.emitf(v.format('YYYY-MM-DD'));
    },
    emitf(v) {
      this.val = v;
    },
    emitv() {
      this.$emit('modified', this.val);
    },
  },
};
</script>

<style scoped>
.form-control {
  padding-left: 2px;
  padding-right: 2px;
  text-align: center;
  border-radius: 0;
}

.brn {
  border: none;
}

.btn {
  border-radius: 0;
}

.flex {
  display: flex;
}
</style>
