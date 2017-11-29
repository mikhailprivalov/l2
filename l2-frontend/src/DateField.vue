<template>
  <input :type="type" class="form-control" v-model="val" :min="min" :max="max"/>
</template>

<script>
  export default {
    name: 'date-field',
    props: {
      type: {
        type: String,
        required: false,
        default: 'text'
      },
      min: {
        type: String,
        required: false,
        default: ''
      },
      max: {
        type: String,
        required: false,
        default: ''
      },
      def: {
        type: String,
        required: false,
        default: ''
      }
    },
    data() {
      return {
        val: this.def
      }
    }
  }
</script>
