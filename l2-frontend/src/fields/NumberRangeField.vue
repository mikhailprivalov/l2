<template>
  <label>
    <input type="range" v-model="val" :readonly="disabled"/>
    {{val}}
  </label>
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
        min: 0,
        max: 1,
        step: 1,
      }
    },
    mounted() {
      const l = this.variants.length;
      if (l > 0) {
        this.min = Number(this.variants[0])
      }
      if (l > 1) {
        this.max = Number(this.variants[1])
      }
      if (l > 2) {
        this.step = Number(this.variants[2])
      }
    },
    watch: {
      val() {
        this.changeValue(this.val)
      },
    },
    model: {
      event: `modified`
    },
    methods: {
      changeValue(newVal) {
        this.$emit('modified', newVal)
      }
    }
  }
</script>
