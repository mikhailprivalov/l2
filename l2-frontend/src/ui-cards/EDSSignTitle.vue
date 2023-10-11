<template>
  <span>{{ title }}</span>
</template>

<script lang="ts">
import { execute, getSystemInfo } from 'crypto-pro';
import { encode } from 'js-base64';

import { convertSubjectNameToTitle } from '@/utils';

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
    type: {
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
        await cadesplugin.async_spawn((function* () {
          const oSignedData = yield cadesplugin.CreateObjectAsync('CAdESCOM.CadesSignedData');
          yield oSignedData.propset_ContentEncoding(1);
          yield oSignedData.propset_Content(this.type === 'PDF' ? this.data : encode(this.data));
          yield oSignedData.VerifyCades(this.signature, 1, true);
          const signers = yield oSignedData.Signers;
          const s1 = yield signers.Item(1);
          const cert = yield s1.Certificate;
          const sn = yield cert.SubjectName;

          this.title = convertSubjectNameToTitle(null, sn);
        }).bind(this));
      });
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error(error);
    }
  },
};
</script>
