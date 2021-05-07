<template>
  <span :class="'status-' + status" class="status">{{text}}</span>
</template>

<script>
const statuses = {
  true: {
    none: 'не сохр.',
    saved: 'сохр.',
    confirmed: 'подтв.',
  },
  false: {
    none: 'Не сохранено',
    saved: 'Сохранено',
    confirmed: 'Подтверждено',
  },
};

export default {
  name: 'IssStatus',
  props: {
    i: {
      type: Object,
      required: true,
    },
    short: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    text() {
      return statuses[this.short][this.status];
    },
    status() {
      const { i } = this;
      if (!i.confirmed && !i.saved) {
        return 'none';
      }
      if (!i.confirmed && i.saved) {
        return 'saved';
      }
      return 'confirmed';
    },
  },
};
</script>

<style lang="scss" scoped>
  .status {
    padding: 5px;
    font-weight: bold;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;

    &-none {
      color: #CF3A24
    }

    &-saved {
      color: #F4D03F
    }

    &-confirmed {
      color: #049372
    }
  }
</style>
