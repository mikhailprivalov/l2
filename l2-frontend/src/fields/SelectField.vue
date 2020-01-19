<template>
  <select :disabled="disabled" v-model="val">
    <option :value="v" v-for="v in variants">
      {{v}}
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
            }
        },
        mounted() {
            if ((!this.val || this.val === '' || !this.variants.includes(this.val)) && this.variants.length > 0) {
                this.val = this.variants[0]
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
