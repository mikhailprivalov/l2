<template>
  <div class="root RTE-root">
    <div
      v-if="disabled"
      v-html="/*eslint-disable-line vue/no-v-html*/ value"
    />
    <div v-else>
      <EditorMenuBar
        v-slot="{ commands, isActive }"
        :editor="editor"
      >
        <div class="menubar">
          <div class="toolbar">
            <button
              v-tippy
              class="menubar__button"
              title="Отменить"
              @click="commands.undo"
            >
              <i class="fa fa-undo" />
            </button>

            <button
              v-tippy
              class="menubar__button"
              title="Вернуть"
              @click="commands.redo"
            >
              <i class="fa fa-redo" />
            </button>

            <button
              v-tippy
              class="menubar__button"
              :class="{ 'is-active': isActive.bold() }"
              title="Полужирный"
              @click="commands.bold"
            >
              <i class="fa fa-bold" />
            </button>

            <button
              v-tippy
              class="menubar__button"
              :class="{ 'is-active': isActive.italic() }"
              title="Курсив"
              @click="commands.italic"
            >
              <i class="fa fa-italic" />
            </button>

            <button
              v-tippy
              class="menubar__button"
              :class="{ 'is-active': isActive.strike() }"
              title="Перечёркнутый"
              @click="commands.strike"
            >
              <i class="fa fa-strikethrough" />
            </button>

            <button
              v-tippy
              class="menubar__button"
              :class="{ 'is-active': isActive.underline() }"
              title="Подчёркнутый"
              @click="commands.underline"
            >
              <i class="fa fa-underline" />
            </button>

            <button
              v-tippy
              class="menubar__button"
              :class="{ 'is-active': isActive.paragraph() }"
              title="Параграф"
              @click="commands.paragraph"
            >
              <i class="fa fa-paragraph" />
            </button>

            <button
              v-tippy
              class="menubar__button"
              :class="{ 'is-active': isActive.heading({ level: 1 }) }"
              title="Основной заголовок"
              @click="commands.heading({ level: 1 })"
            >
              H1
            </button>

            <button
              v-tippy
              class="menubar__button"
              :class="{ 'is-active': isActive.heading({ level: 2 }) }"
              title="Заголовок"
              @click="commands.heading({ level: 2 })"
            >
              H2
            </button>

            <button
              v-tippy
              class="menubar__button"
              :class="{ 'is-active': isActive.heading({ level: 3 }) }"
              title="Подзаголовок"
              @click="commands.heading({ level: 3 })"
            >
              H3
            </button>

            <button
              v-tippy
              class="menubar__button"
              :class="{ 'is-active': isActive.bullet_list() }"
              title="Маркированный список"
              @click="commands.bullet_list"
            >
              <i class="fa fa-list-ul" />
            </button>

            <button
              v-tippy
              class="menubar__button"
              :class="{ 'is-active': isActive.ordered_list() }"
              title="Нумерованный список"
              @click="commands.ordered_list"
            >
              <i class="fa fa-list-ol" />
            </button>

            <button
              v-tippy
              class="menubar__button"
              title="Таблица"
              @click="commands.createTable({ rowsCount: 3, colsCount: 2, withHeaderRow: false })"
            >
              <i class="fa fa-table" />
            </button>

            <span v-if="isActive.table()">
              <button
                v-tippy
                class="menubar__button"
                title="Удалить таблицу"
                @click="commands.deleteTable"
              >
                <img src="@/icons/delete_table.svg">
              </button>
              <button
                v-tippy
                class="menubar__button"
                title="Добавить колонку до"
                @click="commands.addColumnBefore"
              >
                <img src="@/icons/add_col_before.svg">
              </button>
              <button
                v-tippy
                class="menubar__button"
                title="Добавить колонку после"
                @click="commands.addColumnAfter"
              >
                <img src="@/icons/add_col_after.svg">
              </button>
              <button
                v-tippy
                class="menubar__button"
                title="Удалить колонку"
                @click="commands.deleteColumn"
              >
                <img src="@/icons/delete_col.svg">
              </button>
              <button
                v-tippy
                class="menubar__button"
                title="Добавить строку до"
                @click="commands.addRowBefore"
              >
                <img src="@/icons/add_row_before.svg">
              </button>
              <button
                v-tippy
                class="menubar__button"
                title="Добавить строку после"
                @click="commands.addRowAfter"
              >
                <img src="@/icons/add_row_after.svg">
              </button>
              <button
                v-tippy
                class="menubar__button"
                title="Удалить строку"
                @click="commands.deleteRow"
              >
                <img src="@/icons/delete_row.svg">
              </button>
              <button
                v-tippy
                class="menubar__button"
                title="Объединить ячейки"
                @click="commands.toggleCellMerge"
              >
                <img src="@/icons/combine_cells.svg">
              </button>
            </span>
          </div>
        </div>
      </EditorMenuBar>
      <EditorContent :editor="editor" />
    </div>
  </div>
</template>

<script lang="ts">
import { Editor, EditorContent, EditorMenuBar } from 'tiptap';
import {
  Bold,
  BulletList,
  HardBreak,
  Heading,
  History,
  Italic,
  ListItem,
  OrderedList,
  Strike,
  Table,
  TableCell,
  TableHeader,
  TableRow,
  Underline,
} from 'tiptap-extensions';

export default {
  components: {
    EditorContent,
    EditorMenuBar,
  },
  model: {
    event: 'modified',
  },
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
      editor: new Editor({
        extensions: [
          new BulletList(),
          new HardBreak(),
          new Heading({ levels: [1, 2, 3] }),
          new ListItem(),
          new OrderedList(),
          new Bold(),
          new Italic(),
          new Strike(),
          new Underline(),
          new History(),
          new Table({
            resizable: true,
          }),
          new TableHeader(),
          new TableCell(),
          new TableRow(),
        ],
        content: this.value,
      }),
    };
  },
  mounted() {
    this.editor.on('update', ({ getHTML }) => {
      this.changeValue(getHTML());
    });
  },
  beforeDestroy() {
    this.editor.destroy();
  },
  methods: {
    changeValue(newVal) {
      this.$emit('modified', newVal);
    },
  },
};
</script>

<style scoped lang="scss">
.root {
  padding: 5px;
  border: 1px solid #eee;
  background: #fff;
}
</style>

<style lang="scss">
.RTE-root {
  table {
    width: 100%;
    table-layout: fixed;
    border-collapse: collapse;
  }

  table,
  th,
  td {
    border: 1px solid black;
  }

  th,
  td {
    word-break: break-word;
    white-space: normal;
  }

  td {
    padding: 2px;
  }

  td,
  li {
    p {
      margin: 0;
    }
  }

  h1 {
    font-size: 24px;
  }

  h2 {
    font-size: 20px;
  }

  h3 {
    font-size: 18px;
  }

  .ProseMirror {
    &-focused {
      outline: none;
    }

    &.resize-cursor {
      cursor: move;
    }
  }
}

.menubar__button {
  vertical-align: middle;
  img {
    height: 14px;
    width: auto;
  }
}
</style>
