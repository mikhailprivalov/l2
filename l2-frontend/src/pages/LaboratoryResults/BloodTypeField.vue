<template>
  <td colspan="3">
    <div v-if="readonly" v-html="r.value" class="val"></div>
    <template v-else>
      <div>
        <template v-for="g in GROUPS">
          <label :key="g" class="radio-inline" v-if="g !== 'spacer'">
            <input type="radio" name="blood-type" v-model="r.value" :value="g"/> <span v-html="g"></span>
          </label>
          <hr v-else :key="g"/>
        </template>
      </div>
    </template>
  </td>
</template>

<script>

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
