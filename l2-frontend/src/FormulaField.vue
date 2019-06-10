<template>
  <div class="input-group">
      <input class="form-control" :value="content" readonly placeholder="Расчётное поле" />
  </div>
</template>

<script>
  export default {
    name: 'formula-field',
    props: ['value', 'fields', 'formula'],
    data() {
      return {
        content: this.value
      }
    },
    watch: {
      value() {
        this.content = this.value
      },
      content() {
        this.$emit('input', this.content);
      },
      func_formula() {
        this.content = this.func_formula.toString();
      },
    },
    computed: {
      func_formula() {
        let s = this.formula;
        let necessary = s.match(/{(\d+)}/g);

        if (necessary) {
          for (const n of necessary) {
            let v = null;
            let vOrig = ((this.f_obj[n.replace(/[{}]/g, "")] || {}).value || '').trim();
            if ((/^\d+([,.]\d+)?$/).test(vOrig)) {
              if (this.f_obj[n.replace(/[{}]/g, "")]) {
                v = parseFloat(vOrig.trim().replace(",", "."));
              }
              v = v || 0;
              v = isFinite(v) ? v : 0;
            } else {
              v = vOrig;
            }
            s = s.replace(new RegExp(n.replace(/{/g, '\\{').replace(/}/g, '\\}'), 'g'), v || '');
          }
        }
        s = `return (${s});`
        try {
          return (new Function(s)()) || 0;
        } catch (e) {
          return '';
        }

      },
      f_obj() {
        return this.fields.reduce((a, b) => ({...a, [b.pk]: b}), {})
      },
    },
  }
</script>
