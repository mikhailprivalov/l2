<template>
  <div class="input-group">
      <input class="form-control" v-model="content" readonly placeholder="Расчётное поле" />
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
        this.content = this.func_formula;
      },
    },
    computed: {
      func_formula() {
        let s = this.formula;
        let necessary = s.match(/{(\d+)}/g);

        if (necessary) {
          for (const n of necessary) {
            let v = null;
            if (this.f_obj[n.replace(/[{}]/g, "")]) {
              v = parseFloat(this.f_obj[n.replace(/[{}]/g, "")].value.trim().replace(",", "."));
            }
            v = v || 0;
            v = isFinite(v) ? v : 0;
            s = s.replace(new RegExp(n.replace(/{/g, '\\{').replace(/}/g, '\\}'), 'g'), v);
          }
        }
        try {
          return (new Function("return " + s + ";")()) || 0;
        } catch (e) {
          console.error(e);
          return 0;
        }

      },
      f_obj() {
        return this.fields.reduce((a, b) => ({...a, [b.pk]: b}), {})
      },
    },
  }
</script>
