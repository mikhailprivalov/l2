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
        @modified="onCuratorValueChange($event)"
      />
      <NumberField
        v-else-if="localRow.curatorFieldPk && localRow.curatorFieldType === 18"
        :value="localRow.curatorValue"
        @modified="onCuratorValueChange($event)"
      />
      <span v-else>–</span>
    </td>
    <td>
      {{ (localRow.curatorScore === 0 || localRow.curatorScore === '0') ? '0' : (localRow.curatorScore || '–') }}
    </td>
    <td class="approve-td">
      <button
        v-if="localRow.curatorFieldPk && !localRow.curatorApproved"
        class="btn btn-blue-nb btn-sm"
        :disabled="saving"
        @click="saveRow(true)"
      >
        Утвердить
      </button>
      <button
        v-else-if="localRow.curatorFieldPk"
        class="btn btn-default btn-blue2-nb btn-sm"
        :disabled="saving"
        @click="saveRow(false)"
      >
        Отменить
      </button>
    </td>
    <td class="status-td">
      {{ localRow.curatorApproved ? 'утверждено' : '–' }}
    </td>
    <td class="comment-td">
      <input
        v-if="localRow.curatorFieldPk"
        v-model="localRow.curatorComment"
        type="text"
        class="form-control input-sm"
        placeholder="Комментарий"
      >
      <span v-else>–</span>
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
      saving: false,
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
    onCuratorValueChange(value) {
      this.localRow.curatorValue = value;
      this.recalculateCuratorScore();
    },
    async saveRow(approved) {
      if (!this.localRow.curatorFieldPk || this.saving) {
        return;
      }
      this.saving = true;
      try {
        const response = await this.$api('indicators/save-indicator-value', {
          issledovaniye: this.localRow.issledovaniye,
          fieldPk: this.localRow.curatorFieldPk,
          value: this.localRow.curatorValue,
          scoreFieldPk: this.localRow.curatorScoreFieldPk,
          curatorScore: this.localRow.curatorScore,
          approved,
          comment: this.localRow.curatorComment || '',
        });
        this.localRow.curatorApproved = approved;
        if (!this.localRow.curatorScoreFormula || !String(this.localRow.curatorScoreFormula).trim()) {
          this.localRow.curatorScore = response.curatorScore;
        } else {
          this.recalculateCuratorScore();
        }
        this.$emit('row-updated', { ...this.localRow });
      } finally {
        this.saving = false;
      }
    },
  },
};
</script>

<style scoped lang="scss">
.approve-td {
  text-align: center;
  vertical-align: middle;
}

.status-td {
  text-align: center;
  vertical-align: middle;
}

.comment-td {
  .form-control {
    width: 100%;
    min-width: 0;
  }
}
</style>
