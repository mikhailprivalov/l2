<template>
  <select v-model="name" data-width="100%" class="selectpicker" @change="func">
    <option v-bind:value="option.value" v-for="option in options">{{ option.label }}2</option>
  </select>
</template>

<script>
  export default {
    name: 'select-picker',
    props: ['options', 'name', 'func'],
    updated: function () {
      $(this.$el).selectpicker('refresh')
    }
  }
</script>
