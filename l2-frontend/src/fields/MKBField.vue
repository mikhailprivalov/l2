<template>
      <TypeAhead src="/api/mkb10?keyword=:keyword" :getResponse="resp => [...resp.data.data]"
                 :onHit="onHit" ref="d" placeholder="Диагноз (МКБ 10)"
                 v-model="content" maxlength="200" :delayTime="200" :minChars="1"
                 :render="items => items.map(i => `${i.code} ${i.title}`)"
                 :limit="11"
                 :highlighting="(item, vue) => item.toString().replace(vue.query, `<b>${vue.query}</b>`)"
                 :selectFirst="true"
      />
</template>

<script>
import TypeAhead from 'vue2-typeahead';

export default {
  name: 'm-k-b-field',
  props: {
    value: String,
    short: {
      type: Boolean,
      default: true,
    },
  },
  components: {
    TypeAhead,
  },
  data() {
    return {
      content: this.value,
    };
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
        const replace = ['й', 'ц', 'у', 'к', 'е', 'н', 'г', 'ш', 'щ', 'з', 'х', 'ъ',
          'ф', 'ы', 'в', 'а', 'п', 'р', 'о', 'л', 'д', 'ж', 'э',
          'я', 'ч', 'с', 'м', 'и', 'т', 'ь', 'б', 'ю'].map((x) => x.toUpperCase());

        const search = ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '\\[', '\\]',
          'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', '\'',
          'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.'].map((x) => x.toUpperCase());

        for (let i = 0; i < replace.length; i++) {
          const reg = new RegExp(replace[i], 'mig');
          s1 = s1.replace(reg, search[i]);
        }
      }
      this.content = s1 + (s2 !== '' ? ` ${s2}` : '');
      this.$emit('input', this.content);
    },
  },
  methods: {
    onHit(item) {
      this.content = this.short ? (item.split(' ')[0] || '') : item;
    },
  },
};
</script>
