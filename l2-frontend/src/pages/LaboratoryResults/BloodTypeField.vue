<template>
  <td colspan="4">
    <div
      v-if="readonly"
      class="val"
      v-html="/*eslint-disable-line vue/no-v-html*/ r.value"
    />
    <template v-else>
      <div>
        <template v-for="g in GROUPS">
          <label
            v-if="g !== 'spacer'"
            :key="g"
            class="radio-inline"
          >
            <input
              v-model="/* eslint-disable-line vue/no-mutating-props */ r.value"
              type="radio"
              name="blood-type"
              :value="g"
            >
            <span v-html="/*eslint-disable-line vue/no-v-html*/ g" />
          </label>
          <hr
            v-else
            :key="g"
          >
        </template>
      </div>
    </template>
  </td>
</template>

<script lang="ts">
const GROUPS = [
  'O (I)',
  'O<sub>αβ</sub> (I)',
  'spacer',
  'B (III)',
  'Bα (III)',
  'spacer',
  'A (II)',
  'A<sub>β</sub> (II)',
  'A₂β (II)',
  'spacer',
  'AB₀ (IV)',
  'A₂B₀ (IV)',
  'AB (IV)',
];

export default {
  name: 'TextInputField',
  props: {
    readonly: {},
    r: {},
  },
  data() {
    return {
      GROUPS,
    };
  },
};
</script>

<style scoped lang="scss">
.val {
  padding: 5px;
}
</style>
