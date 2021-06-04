<template>
  <div class="field-inputs"
       v-if="values.length > 0 && !confirmed && ![10, 12, 18, 19, 21, 24, 25, 26, 27, 28].includes(field_type)">
    <div class="input-values-wrap">
      <div class="input-values">
        <div class="inner-wrap">
          <div @click="append_value(val)" class="input-value" :key="`${val}_${i}`"
               v-for="(val, i) in values">
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
      let add_val = value;
      const val = this.localValue;
      if (add_val !== ',' && add_val !== '.') {
        if (val.length > 0 && val[val.length - 1] !== ' ' && val[val.length - 1] !== '\n') {
          if (val[val.length - 1] === '.') {
            add_val = add_val.replace(/./, add_val.charAt(0).toUpperCase());
          }
          add_val = ` ${add_val}`;
        } else if (
          (val.length === 0
            || (val.length >= 2
              && val[val.length - 2] === '.'
              && val[val.length - 1] === '\n'
            )
          )
          && this.field_title === ''
        ) {
          add_val = add_val.replace(/./, add_val.charAt(0).toUpperCase());
        }
      }
      this.update_value(val + add_val);
    },
  },
};
</script>
