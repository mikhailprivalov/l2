<template>
  <TypeAhead
    ref="d"
    v-model="content"
    src="/api/mkb10?keyword=:keyword"
    :get-response="resp => [...resp.data.data]"
    :on-hit="onHit"
    placeholder="Диагноз (МКБ 10)"
    no-result-text="Не найдено"
    maxlength="255"
    :delay-time="200"
    :min-chars="1"
    :render="items => items.map(i => `${i.code} ${i.title}`)"
    :limit="11"
    :highlighting="(item, vue) => item.toString().replace(vue.query, `<b>${vue.query}</b>`)"
    :select-first="true"
    :classes="classes"
  />
</template>

<script lang="ts">
import TypeAhead from 'vue2-typeahead';

import directionsPoint from '@/api/directions-point';

export default {
  components: {
    TypeAhead,
  },
  props: {
    value: String,
    classes: {
      type: String,
      required: false,
    },
    fieldPk: {
      type: String,
      required: false,
    },
    fieldPkInitial: {
      type: String,
      required: false,
    },
    iss_pk: {
      type: [String, Number],
      required: false,
    },
    short: {
      type: Boolean,
      default: true,
    },
    form: {
      type: Boolean,
      default: false,
    },
    clientPk: {
      type: Number,
      required: false,
      default: -1,
    },
  },
  data() {
    return {
      content: this.value,
      fpkInitial: this.fieldPkInitial,
    };
  },
  computed: {
    isStaticLink() {
      return this.fpk?.startsWith('%');
    },
    fpk() {
      return this.fpkInitial || this.fieldPk;
    },
  },
  watch: {
    value() {
      this.content = this.value;
    },
    content() {
      let [s1, ...s2] = this.content.split(' ');
      s2 = s2.join(' ');
      if (/^[a-zA-Zа-яА-Я]\d.*/g.test(s1)) {
        s1 = s1.toUpperCase();
        const replace = [
          'й',
          'ц',
          'у',
          'к',
          'е',
          'н',
          'г',
          'ш',
          'щ',
          'з',
          'х',
          'ъ',
          'ф',
          'ы',
          'в',
          'а',
          'п',
          'р',
          'о',
          'л',
          'д',
          'ж',
          'э',
          'я',
          'ч',
          'с',
          'м',
          'и',
          'т',
          'ь',
          'б',
          'ю',
        ].map(x => x.toUpperCase());

        const search = [
          'q',
          'w',
          'e',
          'r',
          't',
          'y',
          'u',
          'i',
          'o',
          'p',
          '\\[',
          '\\]',
          'a',
          's',
          'd',
          'f',
          'g',
          'h',
          'j',
          'k',
          'l',
          ';',
          "'",
          'z',
          'x',
          'c',
          'v',
          'b',
          'n',
          'm',
          ',',
          '.',
        ].map(x => x.toUpperCase());

        for (let i = 0; i < replace.length; i++) {
          const reg = new RegExp(replace[i], 'mig');
          s1 = s1.replace(reg, search[i]);
        }
      }
      this.content = s1 + (s2 !== '' ? ` ${s2}` : '');
      this.$emit('input', this.content);
    },
  },
  mounted() {
    if (this.isStaticLink) {
      this.content = '';
      this.loadLast();
    }
  },
  methods: {
    onHit(item) {
      this.content = this.short ? item.split(' ')[0] || '' : item;
    },
    async loadLast() {
      const { result } = await directionsPoint.lastFieldResult(this, ['iss_pk', 'clientPk'], { fieldPk: this.fpk });
      if (result && !result.isJson) {
        this.content = result.value || '';
      } else if (result) {
        try {
          const jval = JSON.parse(result.value);
          if (jval.code && jval.title) {
            this.content = `${jval.code} ${jval.title}`;
          }
        } catch (e) {
          // eslint-disable-next-line no-console
          console.error(e);
        }
      }
    },
  },
};
</script>

<style scoped lang="scss">
::v-deep .typeahead-dropdown-container {
  top: -28px;
}
</style>
