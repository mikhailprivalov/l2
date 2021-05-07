<template>
  <div class="root RTE-root">
    <div v-if="disabled" v-html="value"></div>
    <div v-else>
      <editor-menu-bar :editor="editor" v-slot="{ commands, isActive }">
        <div class="menubar">
          <div class="toolbar">
            <button
              class="menubar__button"
              @click="commands.undo"
              title="Отменить"
              v-tippy
            >
              <i class="fa fa-undo"></i>
            </button>

            <button
              class="menubar__button"
              @click="commands.redo"
              title="Вернуть"
              v-tippy
            >
              <i class="fa fa-redo"></i>
            </button>

            <button
              class="menubar__button"
              :class="{ 'is-active': isActive.bold() }"
              @click="commands.bold"
              title="Полужирный"
              v-tippy
            >
              <i class="fa fa-bold"></i>
            </button>

            <button
              class="menubar__button"
              :class="{ 'is-active': isActive.italic() }"
              @click="commands.italic"
              title="Курсив"
              v-tippy
            >
              <i class="fa fa-italic"></i>
            </button>

            <button
              class="menubar__button"
              :class="{ 'is-active': isActive.strike() }"
              @click="commands.strike"
              title="Перечёркнутый"
              v-tippy
            >
              <i class="fa fa-strikethrough"></i>
            </button>

            <button
              class="menubar__button"
              :class="{ 'is-active': isActive.underline() }"
              @click="commands.underline"
              title="Подчёркнутый"
              v-tippy
            >
              <i class="fa fa-underline"></i>
            </button>

            <button
              class="menubar__button"
              :class="{ 'is-active': isActive.paragraph() }"
              @click="commands.paragraph"
              title="Параграф"
              v-tippy
            >
              <i class="fa fa-paragraph"></i>
            </button>

            <button
              class="menubar__button"
              :class="{ 'is-active': isActive.heading({ level: 1 }) }"
              @click="commands.heading({ level: 1 })"
              title="Основной заголовок"
              v-tippy
            >
              H1
            </button>

            <button
              class="menubar__button"
              :class="{ 'is-active': isActive.heading({ level: 2 }) }"
              @click="commands.heading({ level: 2 })"
              title="Заголовок"
              v-tippy
            >
              H2
            </button>

            <button
              class="menubar__button"
              :class="{ 'is-active': isActive.heading({ level: 3 }) }"
              @click="commands.heading({ level: 3 })"
              title="Подзаголовок"
              v-tippy
            >
              H3
            </button>

            <button
              class="menubar__button"
              :class="{ 'is-active': isActive.bullet_list() }"
              @click="commands.bullet_list"
              title="Маркированный список"
              v-tippy
            >
              <i class="fa fa-list-ul"></i>
            </button>

            <button
              class="menubar__button"
              :class="{ 'is-active': isActive.ordered_list() }"
              @click="commands.ordered_list"
              title="Нумерованный список"
              v-tippy
            >
              <i class="fa fa-list-ol"></i>
            </button>

            <button
              class="menubar__button"
              @click="commands.createTable({rowsCount: 3, colsCount: 2, withHeaderRow: false })"
              title="Таблица"
              v-tippy
            >
              <i class="fa fa-table"></i>
            </button>

            <span v-if="isActive.table()">
              <button
                class="menubar__button"
                @click="commands.deleteTable"
                title="Удалить таблицу"
                v-tippy
              >
                <img src="@/icons/delete_table.svg" />
              </button>
              <button
                class="menubar__button"
                @click="commands.addColumnBefore"
                title="Добавить колонку до"
                v-tippy
              >
                <img src="@/icons/add_col_before.svg" />
              </button>
              <button
                class="menubar__button"
                @click="commands.addColumnAfter"
                title="Добавить колонку после"
                v-tippy
              >
                <img src="@/icons/add_col_after.svg" />
              </button>
              <button
                class="menubar__button"
                @click="commands.deleteColumn"
                title="Удалить колонку"
                v-tippy
              >
                <img src="@/icons/delete_col.svg" />
              </button>
              <button
                class="menubar__button"
                @click="commands.addRowBefore"
                title="Добавить строку до"
                v-tippy
              >
                <img src="@/icons/add_row_before.svg" />
              </button>
              <button
                class="menubar__button"
                @click="commands.addRowAfter"
                title="Добавить строку после"
                v-tippy
              >
                <img src="@/icons/add_row_after.svg" />
              </button>
              <button
                class="menubar__button"
                @click="commands.deleteRow"
                title="Удалить строку"
                v-tippy
              >
                <img src="@/icons/delete_row.svg" />
              </button>
              <button
                class="menubar__button"
                @click="commands.toggleCellMerge"
                title="Объединить ячейки"
                v-tippy
              >
                <img src="@/icons/combine_cells.svg" />
              </button>
            </span>
          </div>
        </div>
      </editor-menu-bar>
      <editor-content :editor="editor"/>
    </div>
  </div>
</template>

<script>
import { Editor, EditorContent, EditorMenuBar } from 'tiptap';
import {
  HardBreak,
  Heading,
  OrderedList,
  BulletList,
  ListItem,
  Bold,
  Italic,
  Table,
  TableHeader,
  TableCell,
  TableRow,
  Strike,
  Underline,
  History,
} from 'tiptap-extensions';

export default {
  components: {
    EditorContent,
    EditorMenuBar,
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
  model: {
    event: 'modified',
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

    table, th, td {
      border: 1px solid black;
    }

    th, td {
      word-break: break-word;
      white-space: normal;
    }

    td {
      padding: 2px;
    }

    td, li {
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
