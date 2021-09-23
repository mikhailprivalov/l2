<template>
  <Treeselect
    :multiple="false"
    :disable-branch-nodes="true"
    class="treeselect-wide treeselect-34px"
    :async="true"
    :append-to-body="true"
    :clearable="true"
    :disabled="disabled"
    :value="content"
    :zIndex="5001"
    placeholder="Диагноз (МКБ 10)"
    :load-options="loadOptions"
    @select="selectValue"
    loadingText="Загрузка"
    noResultsText="Не найдено"
    searchPromptText="Начните писать для поиска"
    :cache-options="false"
    openDirection="top"
    :openOnFocus="true"
    @input="input"
  >
    <div slot="value-label" slot-scope="{ node }">{{ node.raw.label || node.raw.id }}</div>
  </Treeselect>
</template>

<script lang="ts">
import Treeselect, { ASYNC_SEARCH } from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

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

const fixLayout = s => {
  let [s1, ...s2] = (s || '').split(' ');
  s2 = s2.join(' ');
  if (/^[a-zA-Zа-яА-Я]\d.*/g.test(s1)) {
    s1 = s1.toUpperCase();

    for (let i = 0; i < replace.length; i++) {
      const reg = new RegExp(replace[i], 'mig');
      s1 = s1.replace(reg, search[i]);
    }
  }
  return s1 + (s2 !== '' ? ` ${s2}` : '');
};

export default {
  props: {
    value: String,
    json: {
      type: Boolean,
      default: false,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    dictionary: {
      type: String,
      default: 'mkb10.4',
    },
  },
  components: {
    Treeselect,
  },
  data() {
    return {
      content: '',
      detailsData: {},
    };
  },
  watch: {
    value: {
      immediate: true,
      handler() {
        let data: any = {};
        try {
          data = JSON.parse(this.value);
          this.content = `${data.code} ${data.title}`;
        } catch (e) {
          if (this.value && !this.value.includes('{')) {
            this.content = this.value;
          }
        }
        this.detailsData = data;
      },
    },
    detailsData: {
      deep: true,
      handler() {
        this.emit();
      },
    },
    content() {
      this.content = fixLayout(this.content);
    },
  },
  methods: {
    emit() {
      const v = Object.keys(this.detailsData).length > 0 ? JSON.stringify(this.detailsData) : '';
      this.$emit('modified', v || '');
    },
    async loadOptions({ action, searchQuery, callback }) {
      if (action === ASYNC_SEARCH) {
        const { data } = await this.$api(`/mkb10-dict?query=${fixLayout(searchQuery)}&dictionary=${this.dictionary}&short=0`);
        callback(
          null,
          data.map(d => ({ ...d, label: `${d.code} ${d.title}` })),
        );
      }
    },
    selectValue(node) {
      this.content = node.label;
      this.detailsData = { code: node.code, title: node.title, id: node.id };
    },
    input(v) {
      if (!v) {
        this.content = '';
        this.detailsData = {};
      }
    },
  },
};
</script>
