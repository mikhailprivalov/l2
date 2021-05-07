<template>
  <select :disabled="disabled" v-model="val" class="form-control">
    <option :value="v.pk" :key="v.pk" v-for="v in variants">
      {{v.title}}
    </option>
  </select>
</template>

<script>
export default {
  props: {
    value: {
      required: false,
    },
    variants: {
      required: true,
    },
    disabled: {
      required: false,
      default: false,
      type: Boolean,
    },
  },
  data() {
    return {
      val: this.value,
    };
  },
  mounted() {
    this.fixVal();
  },
  watch: {
    value() {
      this.val = this.value;
    },
    val() {
      this.changeValue(this.val);
    },
  },
  model: {
    event: 'modified',
  },
  methods: {
    changeValue(newVal) {
      this.$emit('modified', newVal);
    },
    fixVal() {
      if ((!this.val || !this.variants.map((v) => v.pk).includes(this.val)) && this.variants.length > 0) {
        this.val = this.variants[0].pk;
      }
    },
  },
};
</script>
