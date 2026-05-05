<template>
  <tr>
    <td>
      {{ localRow.hospital }}
    </td>
    <td>
      <a
        :href="`/ui/results/descriptive#{&quot;pk&quot;:${localRow.mainDirection}}`"
        target="_blank"
        class="a-under"
      >
        {{ localRow.direction }}
      </a>
    </td>
    <td>
      {{ localRow.indicatorTitle }}
    </td>
    <td>
      {{ localRow.hospitalValue }}
    </td>
    <td>
      {{ localRow.score || '–' }}
    </td>
    <td class="cl-td">
      <TreeSelectField
        v-if="localRow.curatorFieldPk && localRow.curatorVariants && localRow.curatorVariants.length > 0"
        :value="localRow.curatorValue"
        :variants="localRow.curatorVariants"
        @modified="saveCuratorValue($event)"
      />
      <span v-else>–</span>
    </td>
    <td>
      {{ (localRow.curatorScore === 0 || localRow.curatorScore === '0') ? '0' : (localRow.curatorScore || '–') }}
    </td>
  </tr>
</template>

<script lang="ts">
import TreeSelectField from '@/fields/TreeSelectField.vue';

export default {
  name: 'IndicatorCuratorRow',
  components: {
    TreeSelectField,
  },
  props: {
    row: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      localRow: { ...this.row },
    };
  },
  watch: {
    row: {
      deep: true,
      handler(newRow) {
        this.localRow = { ...newRow };
      },
    },
  },
  methods: {
    async saveCuratorValue(value) {
      this.localRow.curatorValue = value;
      const response = await this.$api('indicators/save-indicator-value', {
        issledovaniye: this.localRow.issledovaniye,
        fieldPk: this.localRow.curatorFieldPk,
        value,
        scoreFieldPk: this.localRow.curatorScoreFieldPk,
        scoreFormula: this.localRow.curatorScoreFormula,
      });
      this.localRow.curatorScore = response.curatorScore;
      this.$emit('row-updated', { ...this.localRow });
    },
  },
};
</script>
