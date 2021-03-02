<template>
  <td class="val">
    <typeahead
      class="form-control result-field"
      :class="[
               r.fraction.units.length > 0 && 'with-units',
               `isnorm_${r.norm}`,
             ]"
      :readonly="readonly"
      :keyup-enter="moveFocusNext"
      v-model="r.value"
      :id="`fraction-${r.fraction.pk}`"
      :data-x="Math.min(r.fraction.units.length, 9)"
      :local="options"
      defaultSuggestion
    />
    <div class="unit">{{ r.fraction.units }}</div>
  </td>
</template>
<script>
import Typeahead from './Typeahead';

export default {
  name: 'TextInputField',
  components: {Typeahead},
  props: {
    readonly: {},
    moveFocusNext: {},
    r: {}
  },
  computed: {
    options() {
      const {type} = this.r.fraction;
      if (!type || type.length === 0 || type[0] === 'Без вариантов') {
        return [];
      }

      return type;
    },
  },
}
</script>

<style scoped lang="scss">
.val {
  position: relative;
}

.val .unit {
  color: #888;
  top: 1px;
  right: 2px;
  display: block;
}

.val .unit:not(:empty) {
  z-index: 1;
  word-break: keep-all;
  white-space: nowrap;
  height: 20px;
  margin-top: -24px;
  padding-bottom: 4px;
  padding-right: 5px;
  float: right;
  text-align: right;
  box-sizing: border-box;
  overflow: hidden;
  font-size: 12px;
  max-width: 64px;
}

.val input.with-units {
  padding-right: calc(64px / 9 * var(--x) + 7px);
  top: 0;
  left: 0;
  display: block;
}

[data-x="1"] {
  --x: 1;
}

[data-x="2"] {
  --x: 2;
}

[data-x="3"] {
  --x: 3;
}

[data-x="4"] {
  --x: 4;
}

[data-x="5"] {
  --x: 5;
}

[data-x="6"] {
  --x: 6;
}

[data-x="7"] {
  --x: 7;
}

[data-x="8"] {
  --x: 8;
}

[data-x="9"] {
  --x: 9;
}

.isnorm_maybe {
  border-color: darkgoldenrod;
  box-shadow: 0 0 4px darkgoldenrod;
}

.isnorm_not_normal {
  border-color: darkred;
  box-shadow: 0 0 4px darkred;
}

::v-deep .twitter-typeahead {
  position: relative;
  z-index: 0;
}
</style>
