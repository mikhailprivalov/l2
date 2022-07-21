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
        const oSignedData = await cadesplugin.CreateObjectAsync('CAdESCOM.CadesSignedData');
        await oSignedData.propset_ContentEncoding(1);
        await oSignedData.propset_Content(this.signature);
        console.log(oSignedData);
      });
    } catch (error) {
      console.error(error);
    }
  },
};
</script>
