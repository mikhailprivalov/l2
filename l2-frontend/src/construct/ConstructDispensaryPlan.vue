<template>
  <div
    class="form-group mkb10 root"
  >
    <label>Диагноз в полной форме (код по МКБ и название):</label>
    <MKBFieldForm
      v-model="diagnos"
      :short="false"
    />
    <ConfigureDispenseryResearch
      v-if="diagnos.length >= 5"
      :diagnos_code="diagnos"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import ConfigureDispenseryResearch from '@/fields/ConfigureDispenseryResearch.vue';
import MKBFieldForm from '@/fields/MKBFieldForm.vue';

const diagnos = ref('');
</script>

<style scoped lang="scss">

.root {
  width: 100%;
  padding: 20px 40px;
}

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
