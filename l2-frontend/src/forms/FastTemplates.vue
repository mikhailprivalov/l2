<template>
  <div class="field-inputs"
       v-if="values.length > 0 && !confirmed && ![10, 12, 18, 19, 21, 24, 25, 26, 27].includes(field_type)">
    <div class="input-values-wrap">
      <div class="input-values">
        <div class="inner-wrap">
          <div @click="append_value(val)" class="input-value" :key="val"
               v-for="val in values">
            {{ val }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
export default {
  name: 'FastTemplates',
  props: {
    update_value: {
      type: Function,
      required: true,
    },
    value: {
      type: String,
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
  methods: {
    append_value(value) {
      let add_val = value;
      if (add_val !== ',' && add_val !== '.') {
        if (this.value.length > 0 && this.value[this.value.length - 1] !== ' ' && this.value[this.value.length - 1] !== '\n') {
          if (this.value[this.value.length - 1] === '.') {
            add_val = add_val.replace(/./, add_val.charAt(0).toUpperCase());
          }
          add_val = ` ${add_val}`;
        } else if (
          (
            this.value.length === 0
            || (
              this.value.length >= 2
              && this.value[this.value.length - 2] === '.'
              && this.value[this.value.length - 1] === '\n'
            )
          )
          && this.field_title === ''
        ) {
          add_val = add_val.replace(/./, add_val.charAt(0).toUpperCase());
        }
      }
      this.update_value(this.value + add_val);
    },
  },
};
</script>
