<template>
  <tr v-if="research.show">
    <td colspan="6">
      <DescriptiveForm
        :research="research"
        :confirmed="false"
        :patient="patient"/>
    </td>
  </tr>
</template>

<script>
import DescriptiveForm from '../forms/DescriptiveForm'

export default {
  name: "SelectedRsearchesParams",
  components: {
    DescriptiveForm,
  },
  props: {
    research: {
      type: Object,
      required: true,
    },
    patient: {
      type: Object,
      required: true,
    },

  },
}
</script>
