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
        v-if="localRow.curatorFieldPk && localRow.curatorFieldType === 10 && localRow.curatorVariants &&
          localRow.curatorVariants.length > 0"
        :value="localRow.curatorValue"
        :variants="localRow.curatorVariants"
        @modified="saveCuratorValue($event)"
      />
      <NumberField
        v-else-if="localRow.curatorFieldPk && localRow.curatorFieldType === 18"
        :value="localRow.curatorValue"
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
import NumberField from '@/fields/NumberField.vue';

const CURATOR_VALUE_PLACEHOLDER = '[_curator_value_]';

export function evaluateIndicatorCuratorScoreFormula(formula: string, curatorValue: unknown): string | number {
  if (!formula || !String(formula).trim()) {
    return '';
  }
  const s = String(curatorValue ?? '');
  const lit = JSON.stringify(s);
  let expr = String(formula);
  expr = expr.split(`'${CURATOR_VALUE_PLACEHOLDER}'`).join(lit);
  expr = expr.split(`"${CURATOR_VALUE_PLACEHOLDER}"`).join(lit);
  expr = expr.split(CURATOR_VALUE_PLACEHOLDER).join(lit);
  try {
    // Динамическое выражение из настроек поля; иначе потребовался бы полноценный парсер JS.
    // eslint-disable-next-line no-new-func -- формула балла куратора из конфигурации
    const fn = new Function(`return (${expr});`);
    const result = fn();
    if (result === null || result === undefined || (typeof result === 'number' && Number.isNaN(result))) {
      return '';
    }
    return result;
  } catch {
    return '';
  }
}

export default {
  name: 'IndicatorCuratorRow',
  components: {
    TreeSelectField,
    NumberField,
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
        this.$nextTick(() => {
          this.recalculateCuratorScore();
        });
      },
    },
    'localRow.curatorValue': function onCuratorValueChange() {
      this.recalculateCuratorScore();
    },
  },
  mounted() {
    this.recalculateCuratorScore();
  },
  methods: {
    recalculateCuratorScore() {
      if (!this.localRow.curatorScoreFormula || !String(this.localRow.curatorScoreFormula).trim()) {
        return;
      }
      const raw = evaluateIndicatorCuratorScoreFormula(
        this.localRow.curatorScoreFormula,
        this.localRow.curatorValue,
      );
      this.localRow.curatorScore = raw === '' || raw === null || raw === undefined ? '' : String(raw);
    },
    async saveCuratorValue(value) {
      this.localRow.curatorValue = value;
      this.recalculateCuratorScore();
      const response = await this.$api('indicators/save-indicator-value', {
        issledovaniye: this.localRow.issledovaniye,
        fieldPk: this.localRow.curatorFieldPk,
        value,
        scoreFieldPk: this.localRow.curatorScoreFieldPk,
        curatorScore: this.localRow.curatorScore,
      });
      if (!this.localRow.curatorScoreFormula || !String(this.localRow.curatorScoreFormula).trim()) {
        this.localRow.curatorScore = response.curatorScore;
      } else {
        this.recalculateCuratorScore();
      }
      this.$emit('row-updated', { ...this.localRow });
    },
  },
};
</script>
