<template>
  <div
    v-if="values.length > 0 && !confirmed && ![10, 12, 18, 19, 21, 24, 25, 26, 27, 28, 39].includes(field_type)"
    class="field-inputs"
  >
    <div class="input-values-wrap">
      <div class="input-values">
        <div class="inner-wrap">
          <div
            v-for="(val, i) in values"
            :key="`${val}_${i}`"
            class="input-value"
            @click="append_value(val)"
          >
            {{ val }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
export default {
  name: 'FastTemplates',
  props: {
    update_value: {
      type: Function,
      required: true,
    },
    value: {
      required: true,
    },
    values: {
      type: Array,
      required: true,
    },
    confirmed: {
      type: Boolean,
      required: false,
    },
    field_type: {
      type: Number,
      required: false,
    },
    field_title: {
      type: String,
      required: false,
      default: '',
    },
  },
  computed: {
    localValue() {
      return String(this.value);
    },
  },
  methods: {
    append_value(value) {
      let addVal = value;
      const val = this.localValue;
      if (addVal !== ',' && addVal !== '.') {
        if (val.length > 0 && val[val.length - 1] !== ' ' && val[val.length - 1] !== '\n') {
          if (val[val.length - 1] === '.') {
            addVal = addVal.replace(/./, addVal.charAt(0).toUpperCase());
          }
          addVal = ` ${addVal}`;
        } else if (
          (val.length === 0 || (val.length >= 2 && val[val.length - 2] === '.' && val[val.length - 1] === '\n'))
          && this.field_title === ''
        ) {
          addVal = addVal.replace(/./, addVal.charAt(0).toUpperCase());
        }
      }
      this.update_value(val + addVal);
    },
  },
};
</script>
