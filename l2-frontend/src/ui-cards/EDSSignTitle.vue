<template>
  <span>{{ title }}</span>
</template>

<script lang="ts">
import { getSystemInfo, execute } from 'crypto-pro';

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
    data: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      title: this.executor || '',
    };
  },
  async mounted() {
    try {
      await getSystemInfo();
      await execute(async ({ cadesplugin }) => {
        await cadesplugin.async_spawn((function* (args) {
          const oSignedData = yield cadesplugin.CreateObjectAsync('CAdESCOM.CadesSignedData');
          yield oSignedData.propset_ContentEncoding(1);
          yield oSignedData.propset_Content(this.data);
          yield oSignedData.VerifyCades(this.signature, 1, true);
          console.log(oSignedData);
        }).bind(this));
      });
    } catch (error) {
      console.error(error);
    }
  },
};
</script>
