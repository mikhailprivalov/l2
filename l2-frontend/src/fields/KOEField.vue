<template>
  <div v-frag>
    <select v-model="num" class="form-control" style="z-index: 0">
      <option value="0">0</option>
      <option value="1">1</option>
      <option value="2">2</option>
      <option value="3">3</option>
      <option value="4">4</option>
      <option value="5">5</option>
      <option value="6">6</option>
      <option value="7">7</option>
      <option value="8">8</option>
      <option value="9">9</option>
    </select>
    <span class="input-group-addon">
      &nbsp;×&nbsp;10^
    </span>
    <select v-model="power" class="form-control" style="z-index: 0">
      <option value="1">1</option>
      <option value="2">2</option>
      <option value="3">3</option>
      <option value="4">4</option>
      <option value="5">5</option>
      <option value="6">6</option>
      <option value="7">7</option>
      <option value="8">8</option>
      <option value="9">9</option>
      <option value="11">11</option>
      <option value="12">12</option>
      <option value="13">13</option>
      <option value="14">14</option>
      <option value="15">15</option>
    </select>
    <span class="input-group-addon">
      ({{num}}&nbsp;×&nbsp;10<sup style="top: -.3em">{{power}}</sup>)
    </span>
  </div>
</template>

<script>
const valueToParts = (value) => {
  const [num, second] = value.split(' × ');
  const [, power] = (second || '').split('^');

  return {
    num: num || '1',
    power: power || '4',
  };
};
const partsToValue = ({ num, power }) => `${num} × 10^${power}`;

export default {
  props: {
    value: String,
    disabled: {
      required: false,
      default: false,
      type: Boolean,
    },
  },
  data() {
    return {
      ...valueToParts(this.value || ''),
    };
  },
  watch: {
    num: {
      handler() {
        this.updateParts();
      },
    },
    power: {
      handler() {
        this.updateParts();
      },
      immediate: true,
    },
  },
  model: {
    event: 'modified',
  },
  methods: {
    updateParts() {
      this.changeValue(partsToValue(this));
    },
    changeValue(newVal) {
      this.$emit('modified', newVal);
    },
  },
};
</script>
