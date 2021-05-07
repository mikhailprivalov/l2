<template>
  <div class="form-group mkb10" style="width: 100%; margin-top: 40px">
    <label>Диагноз в полной форме (код по МКБ и название):</label>
    <MKBFieldForm v-model="diagnos" :short="false"/>
    <ConfigureDispenseryResearch v-if="diagnos.length >= 5" :diagnos_code="diagnos"/>
  </div>

</template>

<script>

import ConfigureDispenseryResearch from '@/fields/ConfigureDispenseryResearch.vue';
import MKBFieldForm from '../fields/MKBFieldForm.vue';

export default {
  name: 'ConstructDispensaryPlan',
  components: { MKBFieldForm, ConfigureDispenseryResearch },
  data() {
    return {
      diagnos: '',
    };
  },
};
</script>

<style scoped lang="scss">

.mkb10 {
  z-index: 0;
}

.mkb10 ::v-deep .input-group {
  width: 100%;
}

.mkb10 ::v-deep ul {
  font-size: 13px;
  z-index: 1000;
}

.mkb10 ::v-deep ul li {
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 2px .25rem;
  margin: 0 .2rem;

  a {
    padding: 2px 10px;
  }
}

</style>
