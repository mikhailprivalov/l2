<template>
  <td class="val">
    <div
      class="input-group"
      :class="(readonly || !r.fraction.formula) && 'val-full'"
    >
      <span
        v-if="!readonly && r.fraction.formula"
        class="input-group-btn"
      >
        <button
          v-tippy
          type="button"
          class="btn btn-default btn-primary-nb btn30"
          title="Рассчитать результат"
          @click="calcFormula"
        >
          <i class="fa fa-circle" />
        </button>
      </span>
      <Typeahead
        :id="`fraction-${r.fraction.pk}`"
        v-model="/* eslint-disable-line vue/no-mutating-props */ r.value"
        class="form-control result-field"
        :class="[
          r.fraction.units.length > 0 && 'with-units',
          `isnorm_${r.norm}`,
        ]"
        :readonly="readonly"
        :keyup-enter="moveFocusNext"
        :data-x="Math.min(r.fraction.units.length, 9)"
        :local="options"
        default-suggestion
        :hide="showContext"
        @contextmenu.native.prevent="handlerContext"
        @set-id="setId"
      />
    </div>
    <div class="unit">
      {{ r.fraction.units }}
    </div>
    <div
      v-if="showContext"
      v-click-outside="vcoConfig"
      class="context-menu"
    >
      <div class="input-group">
        <span class="input-group-addon">Число</span>
        <input
          v-model.number="ctxPowerNumber"
          type="number"
          class="form-control"
          placeholder="Число"
        >
        <span class="input-group-addon">Степень</span>
        <input
          v-model.number="ctxPowerPower"
          type="number"
          class="form-control"
          placeholder="Степень"
        >
        <div class="input-group-btn">
          <button
            class="btn btn-blue-nb"
            type="button"
            @click="applyCtxPower"
          >
            Дописать
          </button>
        </div>
      </div>
      <hr>
      <div class="input-group">
        <span class="input-group-addon">Пересчёт</span>
        <input
          v-model="ctxRecalc"
          type="text"
          class="form-control"
          placeholder="Пересчёт"
        >
        <div class="input-group-btn">
          <button
            class="btn btn-blue-nb"
            type="button"
            @click="applyCtxRecalc"
          >
            Дописать
          </button>
        </div>
      </div>
      <hr>
      <div class="input-group leic-group">
        <template v-for="(v, k) in LEIC_FIELDS">
          <span
            :key="`s-${k}`"
            class="input-group-addon"
          >{{ v }}</span>
          <input
            :key="`v-${k}`"
            v-model="ctxLeic[k]"
            type="text"
            class="form-control"
            :placeholder="v"
          >
        </template>
        <div class="input-group-btn">
          <button
            class="btn btn-blue-nb"
            type="button"
            @click="applyCtxLeic"
          >
            Ок
          </button>
        </div>
      </div>
    </div>
  </td>
</template>

<script lang="ts">
import vClickOutside from 'v-click-outside';

import * as actions from '@/store/action-types';

import Typeahead from './Typeahead.vue';

function isFloat(str) {
  return /^-?\d+\.\d+$/.test(str);
}

function isLnum(str) {
  return /^-?\d+(\.\d+)?$/.test(str);
}

function readyFormula(formula, resolve, dirData) {
  function getAge(sAge) {
    return parseInt(sAge.split(' ')[0], 10);
  }

  // eslint-disable-next-line no-new-func
  let v = new Function('dir_data', 'get_age', `return ${formula.tmp};`)(dirData, getAge);
  if (isFloat(v)) {
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

function execFormula(dirData, allDirPks, formulaString, resolve) {
  const formula: any = {};
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

  function performComplex(k) {
    formula.necessary_complex[k] = formula.necessary_complex[k].split('|');

    formula.necessary_complex[k][0] = parseInt(formula.necessary_complex[k][0].replace(/[{}]/g, ''), 10);
    formula.necessary_complex[k][1] = parseInt(formula.necessary_complex[k][1].replace(/[{}]/g, ''), 10);

    const issObj = allDirPks.find((i) => i.research_pk === formula.necessary_complex[k][0]);
    if (issObj) {
      formula.str = formula.str.replace(`{${formula.necessary_complex[k][0]}|${formula.necessary_complex[k][1]}}`, issObj.title);
      const fraction = formula.necessary_complex[k][1];
      window.$.ajax({ url: '/results/get', data: { iss_id: issObj.pk } }).done((data) => {
        let fval = '0';
        if (data.results[fraction]) {
          const g = `${data.results[fraction]}`;
          fval = g.replace(',', '.').trim();
          if (!isLnum(fval)) {
            fval = '0';
          }
        }
        formula.tmp = formula.tmp.replace(`{${issObj.research_pk}|${fraction}}`, fval);
        if (k === formula.necessary_complex.length - 1) {
          readyFormula(formula, resolve, dirData);
        } else {
          performComplex(k + 1);
        }
      });
    } else {
      formula.tmp = formula.tmp.replace(`{${formula.necessary_complex[k][0]}|${formula.necessary_complex[k][1]}}`, '0');
      if (k === formula.necessary_complex.length - 1) {
        readyFormula(formula, resolve, dirData);
      } else {
        performComplex(k + 1);
      }
    }
  }

  if (formula.necessary_complex != null) {
    performComplex(0);
  } else {
    readyFormula(formula, resolve, dirData);
  }
}

const LEIC_FIELDS = {
  p: 'п',
  s: 'с',
  e: 'э',
  m: 'м',
  l: 'л',
  y: 'ю',
  b: 'б',
  pk: 'п.кл',
};

const makeLeic = () => Object.keys(LEIC_FIELDS).reduce((a, f) => ({ ...a, [f]: '' }), {});

export default {
  name: 'TextInputField',
  components: { Typeahead },
  directives: {
    clickOutside: vClickOutside.directive,
  },
  props: {
    readonly: {},
    moveFocusNext: {},
    r: {},
    allDirPks: {},
    dirData: {},
  },
  data() {
    return {
      showContext: false,
      id: '',
      ctxPowerNumber: 10,
      ctxPowerPower: 1,
      ctxRecalc: '',
      LEIC_FIELDS,
      ctxLeic: makeLeic(),
    };
  },
  computed: {
    options() {
      const { type } = this.r.fraction;
      if (!type || type.length === 0 || type[0] === 'Без вариантов') {
        return [];
      }

      return type;
    },
    vcoConfig() {
      return {
        handler: this.onClickOutside,
        middleware: this.middleware,
        events: ['dblclick', 'click', 'auxclick'],
      };
    },
  },
  methods: {
    async calcFormula() {
      await this.$store.dispatch(actions.INC_LOADING);
      try {
        const r = await new Promise((resolve) => {
          execFormula(this.dirData, this.allDirPks, this.r.fraction.formula, resolve);
        });
        if (r !== null) {
          // eslint-disable-next-line vue/no-mutating-props
          this.r.value = String(r);
          setTimeout(() => {
            window.$(`#fraction-${this.r.fraction.pk}`).focus();
          }, 50);
        }
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error(e);
        this.$root.$emit('msg', 'error', 'Произошла ошибка расчёта');
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    handlerContext() {
      this.showContext = true;
    },
    onClickOutside() {
      this.showContext = false;
    },
    setId(id) {
      this.id = id;
    },
    middleware(e) {
      return e.target.id !== this.id || e.type !== 'auxclick';
    },
    applyCtxPower() {
      // eslint-disable-next-line vue/no-mutating-props
      this.r.value = `${this.r.value} ${this.ctxPowerNumber}<sup>${this.ctxPowerPower}</sup>`.trim();
      this.hideContext();
    },
    applyCtxRecalc() {
      // eslint-disable-next-line vue/no-mutating-props
      this.r.value = `${this.r.value} (пересчитано${this.ctxRecalc ? ' ' : ''}${this.ctxRecalc})`.trim();
      this.hideContext();
      this.ctxRecalc = '';
    },
    applyCtxLeic() {
      const v = Object.keys(LEIC_FIELDS).map(k => `${LEIC_FIELDS[k]}${this.ctxLeic[k]}`).join('\\');
      // eslint-disable-next-line vue/no-mutating-props
      this.r.value = `${this.r.value} ${v}`.trim();
      this.hideContext();
      this.ctxLeic = makeLeic();
    },
    hideContext() {
      this.showContext = false;
      if (this.id && window.$(`#${this.id}`).length) {
        setTimeout(() => {
          window.$(`#${this.id}`).focus();
          window.$(`#${this.id}`)[0].selectionStart = window.$(`#${this.id}`)[0].value.length;
        }, 50);
      }
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

.context-menu {
  position: absolute;
  top: 100%;
  right: 0;
  left: 0;
  min-width: 480px;
  z-index: 999;
  background: #c7ccd3;
  padding: 10px;
  border-radius: 0 0 5px 5px;
  border: 1px solid #717e90;

  hr {
    margin: 10px 0;
  }
}

.leic-group {
  .input-group-addon, .form-control, .btn {
    padding: 6px;
  }
}
</style>
