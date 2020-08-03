<template>
  <div>
    <template v-if="Boolean(mode)">

    </template>
  </div>
</template>

<script>
  const fieldModes = {
    3: 'formula', 11: 'fraction', 13: 'field', 14: 'field', 23: 'field-and-group'
  };

  export default {
    name: "FieldHelper",
    props: {
      fieldType: {
        type: Number,
        required: true,
      },
      value: {
        type: String,
        required: true,
      }
    },
    computed: {
      mode() {
        return fieldModes[this.type];
      },
    }
  }
</script>

<style scoped lang="scss">

</style>
