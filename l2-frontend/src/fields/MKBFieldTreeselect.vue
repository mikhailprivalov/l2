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
    :z-index="5001"
    placeholder="Диагноз (МКБ 10)"
    :load-options="loadOptions"
    loading-text="Загрузка"
    no-results-text="Не найдено"
    search-prompt-text="Начните писать для поиска"
    :cache-options="false"
    open-direction="top"
    :open-on-focus="true"
    @select="selectValue"
    @input="input"
  >
    <div
      slot="value-label"
      slot-scope="{ node }"
    >
      {{ node.raw.label || node.raw.id }}
    </div>
  </Treeselect>
</template>

<script lang="ts">
import Treeselect, { ASYNC_SEARCH } from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import directionsPoint from '@/api/directions-point';

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
  components: {
    Treeselect,
  },
  model: {
    event: 'modified',
  },
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
    clientPk: {
      type: Number,
      required: false,
      default: -1,
    },
  },
  data() {
    return {
      content: '',
      detailsData: {},
      fpkInitial: this.fieldPkInitial,
    };
  },
  computed: {
    isStaticLink() {
      return this.fpk?.startsWith('%');
    },
    fpk() {
      return this.disabled ? null : this.fpkInitial || this.fieldPk;
    },
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
  mounted() {
    if (this.isStaticLink) {
      this.content = '';
      this.detailsData = {};
      this.loadLast();
    }
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
    async loadLast() {
      const { result } = await directionsPoint.lastFieldResult(this, ['iss_pk', 'clientPk'], { fieldPk: this.fpk });
      try {
        const jval = JSON.parse(result.value);
        if (jval.code && jval.title) {
          this.content = `${jval.code} ${jval.title}`;
          this.detailsData = jval;
        }
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error(e);
      }
    },
  },
};
</script>
