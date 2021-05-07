<template>
  <div class="popper-root">
    <textarea v-model="val"
              @focusout="focusout" @focus="focus" @blur="focusout"
              @keydown.13="chooseItem" @keydown.tab="chooseItem" @keydown.40="moveDown" @keydown.38="moveUp"
              @select="updateSelect"
              ref="textarea"
              class="form-control"
              :readonly="disabled"
              rows="5"
    />

    <div class="pop" :style="offset" v-if="searchMatch.length > 0 && !disabled && !forceHide">
      <template v-for="(result, index) in searchMatch">
        <div class="item" :key="result" :class="{active: selectedIndex === index}"
             @click="selectItem(index)" @mousedown.prevent @mouseover="selectIndex(index)">
          <span v-html="highlightWord(result)"/>
        </div>
      </template>
    </div>
  </div>
</template>

<script>
//! ТЕСТОВЫЙ КОМПОНЕНТ ДЛЯ ЭКСПЕРИМЕНТОВ С АВТОКОМПЛИТОМ

import getCaretCoordinates from 'textarea-caret';

const standardItems = [
  'input',
  'h1',
  'h2',
  'h3',
  'h4',
  'h5',
  'h6',
  'span',
  'div',
  'textarea',
  'margin',
  'padding',
  'display',
  'background',
  'background-color',
  'background-size',
  'background-repeat',
  'position',
  'top',
  'left',
  'right',
  'bottom',
];

function escapeRegex(string) {
  return string.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&');
}

export default {
  props: {
    value: {
      required: false,
    },
    disabled: {
      required: false,
      default: false,
      type: Boolean,
    },
  },
  data() {
    return {
      val: this.value,
      searchMatch: [],
      selectedIndex: 0,
      wordIndex: 0,
      clickedChooseItem: false,
      offset: { top: '0', left: '0' },
      int: null,
      forceHide: false,
    };
  },
  mounted() {
    this.int = setInterval(() => {
      this.updateSelect();
    }, 100);
  },
  beforeDestroy() {
    clearInterval(this.int);
  },
  watch: {
    value() {
      this.val = this.value;
    },
    val() {
      this.changeValue(this.val);
      this.focus();
      this.selectedIndex = 0;
      this.wordIndex = this.inputSplitted.length - 1;
      this.loadSuggestions();
      this.updateOffset();
    },
  },
  computed: {
    listToSearch() {
      if (typeof this.items !== 'undefined' && this.items.length > 0) {
        return this.items;
      }
      return standardItems;
    },
    currentWord() {
      return this.val.replace(/(\r\n|\n|\r)/gm, ' ').split(' ')[this.wordIndex];
    },
    inputSplitted() {
      return this.val.replace(/(\r\n|\n|\r)/gm, ' ').split(' ');
    },
  },
  model: {
    event: 'modified',
  },
  methods: {
    updateSelect() {
      if (this.searchMatch.length !== 0 && this.$refs.textarea.selectionEnd !== this.val.length) {
        this.forceHide = true;
      } else if (this.forceHide) {
        this.forceHide = false;
        this.loadSuggestions();
      }
    },
    updateOffset() {
      if (this.searchMatch.length > 0) {
        const { textarea } = this.$refs;
        const cwl = this.currentWord.length;
        const caret = getCaretCoordinates(textarea, textarea.selectionEnd - cwl);
        this.offset = {
          top: `${caret.top + 17}px`,
          left: `${caret.left - 4}px`,
        };
      }
    },
    changeValue(newVal) {
      this.$emit('modified', newVal);
    },
    highlightWord(word) {
      const regex = new RegExp(`^(${escapeRegex(this.currentWord)})`, 'gi');
      return word.replace(regex, '<span class="inner">$1</span>');
    },
    setWord(word) {
      const currentWords = this.val.replace(/(\r\n|\n|\r)/gm, '__br__ ').split(' ');
      currentWords[this.wordIndex] = currentWords[this.wordIndex].replace(this.currentWord, `${word} `);
      this.wordIndex += 1;
      this.val = currentWords.join(' ').replace(/__br__\s/g, '\n');
    },
    moveDown() {
      if (this.selectedIndex < this.searchMatch.length - 1) {
        this.selectedIndex++;
      } else {
        this.selectedIndex = 0;
      }
    },
    moveUp() {
      if (this.selectedIndex !== -1) {
        this.selectedIndex--;
      }
    },
    selectIndex(index) {
      this.selectedIndex = index;
    },
    selectItem(index) {
      this.selectedIndex = index;
      this.chooseItem();
    },
    chooseItem(e) {
      this.clickedChooseItem = true;

      if (this.selectedIndex !== -1 && this.searchMatch.length > 0) {
        if (e) {
          e.preventDefault();
        }
        this.setWord(this.searchMatch[this.selectedIndex]);
        this.selectedIndex = -1;
      }
    },
    focusout() {
      setTimeout(() => {
        if (!this.clickedChooseItem) {
          this.searchMatch = [];
          this.selectedIndex = -1;
        }
        this.clickedChooseItem = false;
        this.forceHide = false;
      }, 100);
    },
    focus() {
      this.forceHide = false;
      this.searchMatch = [];
      this.loadSuggestions();
    },
    loadSuggestions() {
      if (this.currentWord) {
        this.searchMatch = this.listToSearch.filter(
          (el) => el.startsWith(this.currentWord),
        );
      } else {
        this.searchMatch = [];
      }
    },
  },
};
</script>

<style>
  .item .inner {
    color: #1b6d85;
    font-family: "Lucida Console", Monaco, monospace;
  }
</style>

<style scoped lang="scss">
  textarea {
    font-family: "Lucida Console", Monaco, monospace;
  }

  .popper-root {
    position: relative;
  }

  .pop {
    position: absolute;

    z-index: 10;

    overflow: auto;

    min-width: 250px;
    max-height: 300px;

    top: 0;
    left: 0;

    border: 1px solid #ddd;

    list-style: none;

    background-color: #fff;
    box-shadow: 0 5px 5px rgba(0, 0, 0, 0.2);

    .item {
      span {
        font-family: "Lucida Console", Monaco, monospace;
      }

      cursor: pointer;
      padding: 4px;

      border-bottom: 1px solid #ddd;

      &:last-child {
        border-bottom: 0;
      }

      &.active {
        background-color: #f5f5f5;
      }

    }
  }

</style>
