<template>
  <span>{{ title }}</span>
</template>

<script lang="ts">
import { execute } from 'crypto-pro';

export default {
  name: 'EDSSignTitle',
  props: {
    executor: {
      type: String,
    },
    signature: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      title: this.executor,
    };
  },
  async mounted() {
    try {
      await execute(async ({ cadesplugin }) => {
        cadesplugin.async_spawn(function* (args) {
          const oSignedData = yield cadesplugin.CreateObjectAsync('CAdESCOM.CadesSignedData');
          yield oSignedData.propset_ContentEncoding(1);
          yield oSignedData.propset_Content(this.signature);
          console.log(oSignedData);
        });
      });
    } catch (error) {
      console.error(error);
    }
  },
};
</script>
