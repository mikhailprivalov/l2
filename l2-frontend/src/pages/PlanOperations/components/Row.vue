<template>
  <tr>
    <td>
      {{data.date}}
    </td>
    <td>
      {{data.direction}}
    </td>
    <td>
      {{data.fio_patient}} {{data.birthday}}
    </td>
    <td>
      {{data.type_operation}}
    </td>
    <td></td>
    <td></td>
    <td></td>
  </tr>
</template>

<script>
  export default {
    name: "Row",
    props: {
      data: {
        type: Object,
        required: true,
      }
    }
  }
</script>

<style scoped>

</style>
