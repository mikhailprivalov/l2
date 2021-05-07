<template>
  <td class="val">
    <div class="input-group" :class="(readonly || !r.fraction.formula) && 'val-full'">
      <span class="input-group-btn" v-if="!readonly && r.fraction.formula">
        <button type="button"
                @click="calcFormula"
                class="btn btn-default btn-primary-nb btn30"
                title="Рассчитать результат"
                v-tippy>
          <i class="fa fa-circle"></i>
        </button>
      </span>
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
    </div>
    <div class="unit">{{ r.fraction.units }}</div>
  </td>
</template>
<script>
import * as actions from '@/store/action-types';
import Typeahead from './Typeahead.vue';

function is_float(str) {
  return /^-?\d+\.\d+$/.test(str);
}

function is_lnum(str) {
  return /^-?\d+(\.\d+)?$/.test(str);
}

function ready_formula(formula, resolve, dir_data) {
  function get_age(s_age) {
    return parseInt(s_age.split(' ')[0], 10);
  }

  // eslint-disable-next-line no-new-func
  let v = new Function('dir_data', 'get_age', `return ${formula.tmp};`)(dir_data, get_age);
  if (is_float(v)) {
    v = Math.round(parseFloat(v) * 1000) / 1000;
  }
  if (!Number.isNaN(v) && Number.isFinite(v)) {
    resolve(v);
    // @ts-ignore
    // eslint-disable-next-line no-undef
    window.$.amaran({
      theme: 'awesome ok',
      content: {
        title: 'Результат посчитан',
        message: `Формула:<br/>${formula.str}<br/>Процесс подсчета:<br/>${formula.tmp}`,
        info: '',
        icon: 'fa fa-exclamation',
      },
      position: 'bottom right',
      delay: 10000,
    });
    return;
  }

  if (!Number.isFinite(v) && !Number.isNaN(v)) {
    // @ts-ignore
    // eslint-disable-next-line no-undef
    window.$.amaran({
      theme: 'awesome wrn',
      closeButton: true,
      sticky: true,
      content: {
        title: 'Ошибка',
        message: `Произошло деление на ноль.<br/>Формула:<br/>${formula.str}<br/>Процесс подсчета:<br/>${formula.tmp}`,
        info: '',
        icon: 'fa fa-exclamation',
      },
      position: 'bottom right',
    });
  } else {
    // @ts-ignore
    // eslint-disable-next-line no-undef
    window.$.amaran({
      theme: 'awesome wrn',
      closeButton: true,
      sticky: true,
      content: {
        title: 'Ошибка',
        message: 'Возможно, не все необходимые исследования были назначены',
        info: '',
        icon: 'fa fa-exclamation',
      },
      position: 'bottom right',
    });
  }

  resolve(null);
}

function exec_formula(dir_data, allDirPks, formulaString, resolve) {
  const formula = {};
  formula.body = formulaString;
  formula.necessary = formula.body.match(/{(\d{1,})}/g);
  formula.necessary_complex = formula.body.match(/{\d{1,}\|\d+}/g);
  formula.tmp = formula.body;
  formula.str = formula.body;

  if (formula.necessary !== null) {
    for (let i = 0; i < formula.necessary.length; i++) {
      formula.necessary[i] = formula.necessary[i].replace(/[{}]/g, '');
      let fval = 0;
      try {
        fval = parseFloat(window.$(`#fraction-${formula.necessary[i]}`).val().trim().replace(',', '.'));
      } catch (e) {
        // pass
      }
      if (!fval) {
        fval = 0;
      }
      formula.tmp = formula.tmp.replace(`{${formula.necessary[i]}}`, fval);
    }
  }

  function perform_complex(k) {
    formula.necessary_complex[k] = formula.necessary_complex[k].split('|');

    formula.necessary_complex[k][0] = parseInt(formula.necessary_complex[k][0].replace(/[{}]/g, ''), 10);
    formula.necessary_complex[k][1] = parseInt(formula.necessary_complex[k][1].replace(/[{}]/g, ''), 10);

    const iss_obj = allDirPks.find((i) => i.research_pk === formula.necessary_complex[k][0]);
    if (iss_obj) {
      formula.str = formula.str.replace(`{${formula.necessary_complex[k][0]}|${formula.necessary_complex[k][1]}}`, iss_obj.title);
      const fraction = formula.necessary_complex[k][1];
      window.$.ajax({ url: '/results/get', data: { iss_id: iss_obj.pk } }).done((data) => {
        let fval = '0';
        if (data.results[fraction]) {
          const g = `${data.results[fraction]}`;
          fval = g.replace(',', '.').trim();
          if (!is_lnum(fval)) {
            fval = '0';
          }
        }
        formula.tmp = formula.tmp.replace(`{${iss_obj.research_pk}|${fraction}}`, fval);
        if (k === formula.necessary_complex.length - 1) {
          ready_formula(formula, resolve, dir_data);
        } else {
          perform_complex(k + 1);
        }
      });
    } else {
      formula.tmp = formula.tmp.replace(`{${formula.necessary_complex[k][0]}|${formula.necessary_complex[k][1]}}`, '0');
      if (k === formula.necessary_complex.length - 1) {
        ready_formula(formula, resolve, dir_data);
      } else {
        perform_complex(k + 1);
      }
    }
  }

  if (formula.necessary_complex != null) {
    perform_complex(0);
  } else {
    ready_formula(formula, resolve, dir_data);
  }
}

export default {
  name: 'TextInputField',
  components: { Typeahead },
  props: {
    readonly: {},
    moveFocusNext: {},
    r: {},
    allDirPks: {},
    dirData: {},
  },
  computed: {
    options() {
      const { type } = this.r.fraction;
      if (!type || type.length === 0 || type[0] === 'Без вариантов') {
        return [];
      }

      return type;
    },
  },
  methods: {
    async calcFormula() {
      await this.$store.dispatch(actions.INC_LOADING);
      try {
        const r = await new Promise((resolve) => exec_formula(this.dirData, this.allDirPks, this.r.fraction.formula, resolve));
        if (r !== null) {
          this.r.value = String(r);
          setTimeout(() => {
            window.$(`#fraction-${this.r.fraction.pk}`).focus();
          }, 50);
        }
      } catch (e) {
        console.error(e);
        window.errmessage('Произошла ошибка рассчёта');
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style scoped lang="scss">
.val {
  position: relative;
  &-full {
    width: 100%;
  }
}

.val .unit {
  color: #888;
  top: 1px;
  right: 2px;
  display: block;
}

.val .unit:not(:empty) {
  right: 5px;
  position: absolute;
  z-index: 2;
  word-break: keep-all;
  white-space: nowrap;
  top: 11px;
  overflow: hidden;
  font-size: 12px;
  max-width: 64px;
}

.val input.with-units {
  padding-right: calc(64px / 9 * var(--x) + 5px);
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
}
</style>
