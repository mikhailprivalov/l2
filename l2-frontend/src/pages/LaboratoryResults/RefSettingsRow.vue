<template>
  <div v-frag>
    <td>
      {{ r.fraction.title }}
    </td>
    <td>
      <select class="form-control" v-model.number="r.selectedReference">
        <option :value="k" :key="k" v-for="(v, k) in r.fraction.references.available">{{ v.title }}</option>
      </select>
    </td>
    <td>
      <template v-if="r.selectedReference !== -3">
        <table class="table table-bordered table-condensed">
          <tbody>
          <Ref :data="r.ref.m" with-border-right/>
          <Ref :data="r.ref.f"/>
          </tbody>
        </table>
      </template>
      <template v-else>
        <RefEditor :reference="r.ref"/>
      </template>
    </td>
  </div>
</template>

<script>
import _ from 'lodash';

import Ref from '@/pages/LaboratoryResults/Ref.vue';
import RefEditor from '@/pages/LaboratoryResults/RefEditor.vue';

export default {
  name: 'RefSettingsRow',
  components: { RefEditor, Ref },
  props: {
    r: {},
  },
  watch: {
    selectedReference() {
      const { r } = this;
      if (!r.ref) {
        r.ref = {};
      }
      for (let pk of Object.keys(r.fraction.references.available)) {
        pk = Number(pk);
        if (pk === this.selectedReference) {
          r.ref = _.cloneDeep(r.fraction.references.available[pk]);
          return;
        }
      }
      r.ref.m = {};
      r.ref.f = {};
    },
  },
  computed: {
    selectedReference() {
      return this.r.selectedReference;
    },
  },
};
</script>
