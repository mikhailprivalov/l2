<template>
  <span>
    {{display}}
  </span>
</template>

<script>
import moment from 'moment';

export default {
  name: 'DisplayDateTime',
  props: {
    value: {
      required: true,
      type: String,
    },
  },
  computed: {
    display() {
      return moment(this.value).format('HH:mm DD.MM');
    },
  },
};
</script>
