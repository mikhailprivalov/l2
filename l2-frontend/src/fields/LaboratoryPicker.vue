<template>
  <div class="input-group">
    <span class="input-group-addon">Лаборатория</span>
    <SelectFieldTitled
      v-model="val"
      :variants="labs"
    />
  </div>
</template>

<script lang="ts">
import SelectFieldTitled from '@/fields/SelectFieldTitled.vue';

export default {
  components: {
    SelectFieldTitled,
  },
  model: {
    event: 'modified',
  },
  props: {
    value: {
      required: true,
    },
    withAll: {
      required: false,
      default: false,
      type: Boolean,
    },
  },
  data() {
    return {
      val: this.value,
    };
  },
  computed: {
    labs() {
      let labs = this.$store.getters.allDepartments.filter(d => d.type === '2');

      if (this.withAll) {
        labs = [{ pk: 0, title: 'Все' }, ...labs];
      }

      return labs;
    },
  },
  watch: {
    value() {
      this.val = this.value;
    },
    val() {
      this.changeValue(this.val);
    },
  },
  methods: {
    changeValue(newVal) {
      this.$emit('modified', newVal);
    },
  },
};
</script>

<style lang="scss" scoped>
.fullWidth {
  width: 100%;
}
</style>
