<template>
      <TypeAhead src="/api/mkb10?keyword=:keyword" :getResponse="resp => [...resp.data.data]"
                 :onHit="onHit" ref="d" placeholder="Диагноз (МКБ 10)"
                 v-model="content" maxlength="36" :delayTime="200" :minChars="1"
                 :render="items => items.map(i => `${i.code} ${i.title}`)"
                 :limit="11"
                 :highlighting="(item, vue) => item.toString().replace(vue.query, `<b>${vue.query}</b>`)"
                 :selectFirst="true"
      />
</template>

<script>
  import TypeAhead from 'vue2-typeahead'

  export default {
    name: 'm-k-b-field',
    props: ['value'],
    components: {
      TypeAhead,
    },
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
        if (/^[a-zA-Zа-яА-Я]\d.*/g.test(this.content)) {
          this.content = this.content.toUpperCase()
          const replace = ['й', 'ц', 'у', 'к', 'е', 'н', 'г', 'ш', 'щ', 'з', 'х', 'ъ',
            'ф', 'ы', 'в', 'а', 'п', 'р', 'о', 'л', 'д', 'ж', 'э',
            'я', 'ч', 'с', 'м', 'и', 'т', 'ь', 'б', 'ю'];

          const search = ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '\\[', '\\]',
            'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', '\'',
            'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.'];

          for (let i = 0; i < replace.length; i++) {
            let reg = new RegExp(replace[i], 'mig');
            this.content = this.content.replace(reg, function (a) {
              return a === a.toLowerCase() ? search[i] : search[i].toUpperCase();
            })
          }
        }
        this.$emit('input', this.content);
      }
    },
    methods: {
      onHit(item) {
        this.content = item.split(' ')[0] || '';
      }
    },
  }
</script>
