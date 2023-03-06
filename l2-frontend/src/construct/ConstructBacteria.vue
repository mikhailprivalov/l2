<template>
  <div>
    <div class="radio-button-object">
      <RadioField
        v-model="searchTypesObject"
        :variants="typesObject"
        full-width
        @modified="filteredGroupObject"
      />
    </div>

    <div class="radio-button-object radio-button-groups">
      <RadioField
        v-model="searchTypesGroups"
        :variants="typesGroups"
        full-width
        @modified="filteredGroupObject"
      />
    </div>

    <div class="row lists">
      <div class="col-xs-4">
        <div class="edit-element">
          <h6><strong>{{ searchTypesObject }}</strong> (создание/редактирование)</h6>

          <div class="content-edit margin-top">
            <div class="form-group">
              <label for="create-title">Название:</label>
              <div class="input-group">
                <input
                  id="create-title"
                  v-model.trim="editElementTitle"
                  class="form-control"
                  :placeholder="`${searchTypesObject}: введите название`"
                >
                <span class="input-group-btn">
                  <button
                    v-tippy="{ placement : 'bottom'}"
                    class="btn btn-default btn-primary-nb"
                    title="Очистить"
                    @click="onClearContentEdit"
                  >
                    <i class="fa fa-times" />
                  </button>
                </span>
              </div>
            </div>
            <div class="form-group">
              <label for="create-fsli">Код ФСЛИ:</label>
              <input
                id="create-fsli"
                v-model="editElementFsli"
                class="form-control"
                placeholder="Введите код ФСЛИ.."
              >
            </div>
            <div class="form-group">
              <label for="create-code-lis">Код LIS:</label>
              <input
                id="create-code-lis"
                v-model="editElementLis"
                class="form-control"
                placeholder="Введите код LIS"
              >
            </div>
            <div class="checkbox">
              <label>
                <input
                  v-model="editElementHide"
                  type="checkbox"
                > Скрыть
              </label>
            </div>
            <div class="form-group">
              <strong>Группа:</strong> {{ editElementGroup || 'все' }}
            </div>
          </div>
        </div>

        <button
          class="btn btn-blue-nb sidebar-footer"
          :disabled="!editElementTitle"
          @click="save_element"
        >
          Сохранить
        </button>
      </div>

      <div class="col-xs-4">
        <v-select
          v-model="selected1"
          :clearable="false"
          label="title"
          :options="list1"
          :searchable="true"
          placeholder="Выберите группу"
          :class="{background: selected1.hide}"
          @change="load_culture_groups(selected1.title, '1')"
        />
        <input
          v-model="searchElement"
          class="form-control"
          placeholder="Фильтр по названию.."
        >
        <draggable
          class="list-group"
          :list="list1Elements"
          group="some"
        >
          <div
            v-for="element in filteredList"
            :key="element.title"
            class="item"
          >
            <div :class="{background: element.hide}">
              {{ element.title }}
              <button
                class="btn btn-blue-nb sidebar-btn"
                style="font-size: 12px"
              >
                <i
                  v-if="searchTypesGroups === 'Группы'"
                  class="glyphicon glyphicon-pencil"
                  @click="onEditElement(element)"
                />
                <i
                  v-else-if="selected2.title !== 'Все'"
                  v-tippy="{ placement : 'bottom'}"
                  class="glyphicon glyphicon-arrow-right"
                  title="Добавить в набор"
                  @click="onAddToSet(element)"
                />
              </button>
            </div>
          </div>
        </draggable>
      </div>

      <div class="col-xs-4">
        <v-select
          v-model="selected2"
          :clearable="false"
          label="title"
          :options="list2"
          :searchable="true"
          :class="{background: selected2.hide}"
          @change="load_culture_groups(selected2.title, '2')"
        />

        <div class="input-group">
          <input
            v-model.trim="newgroup"
            class="form-control"
            :placeholder="`Добавить: ${searchTypesGroups}`"
          >
          <span class="input-group-btn">
            <button
              v-tippy="{ placement : 'bottom' }"
              class="btn btn-default btn-primary-nb"
              :title="`Сохранить в &#171;${searchTypesGroups.toUpperCase().trim()}&#187;`"
              :disabled="!newgroup"
              @click="addNewGroup"
            >
              <i class="fa fa-floppy-o" />
            </button>
          </span>
        </div>

        <draggable
          v-if="searchTypesGroups === 'Группы'"
          class="list-group"
          :list="list2Elements"
          group="some"
        >
          <div
            v-for="element in list2Elements"
            :key="element.title"
            class="item"
          >
            <div :class="{background: element.hide}">
              {{ element.title }}
            </div>
          </div>
        </draggable>
        <div
          v-else
          class="list-group"
        >
          <div
            v-for="element in list2Elements"
            :key="element.title"
            class="item"
          >
            <div :class="{background: element.hide}">
              {{ element.title }}
              <button
                v-if="selected2.title !== 'Все'"
                v-tippy="{ placement : 'bottom'}"
                class="btn btn-blue-nb sidebar-btn"
                title="Удалить из набора"
                @click="delFromlistSetsElements(element)"
              >
                <i class="fa fa-times" />
              </button>
            </div>
          </div>
        </div>

        <button
          class="btn btn-blue-nb sidebar-footer"
          @click="save_groups"
        >
          Сохранить
        </button>
        <button
          v-if="selected2.pk >= 0"
          class="btn btn-blue-nb sidebar-footer"
          @click="group_edit"
        >
          Редактировать группу
        </button>
      </div>
    </div>

    <div class="sub-buttons">
      <button
        v-if="searchTypesGroups === 'Группы'"
        class="btn btn-blue-nb"
        @click="openFcafbg"
      >
        Быстрое создание и заполнение: {{ searchTypesObject }} – {{ searchTypesGroups }}
      </button>
    </div>

    <BacteriaEditTitleGroup
      v-if="group_edit_open"
      :group_obj="selected2"
      :types-object="searchTypesObject"
      :types-groups="searchTypesGroups"
    />

    <FastCreateAndFillBacteriaGroup
      v-if="isFcafbgOpen"
      :types-object="searchTypesObject"
      :types-groups="searchTypesGroups"
    />
  </div>
</template>

<script lang="ts">
import vSelect from 'vue-select';
import 'vue-select/dist/vue-select.css';
import draggable from 'vuedraggable';

import bacteriaPoint from '@/api/bacteria-point';
import RadioField from '@/fields/RadioField.vue';
import BacteriaEditTitleGroup from '@/modals/BacteriaEditTitleGroup.vue';
import * as actions from '@/store/action-types';
import FastCreateAndFillBacteriaGroup from '@/modals/FastCreateAndFillBacteriaGroup.vue';

export default {
  name: 'ConstructBacteria',
  components: {
    FastCreateAndFillBacteriaGroup,
    vSelect,
    draggable,
    RadioField,
    BacteriaEditTitleGroup,
  },
  data() {
    return {
      list1: [],
      list2: [],
      listSets: [],
      list1Elements: [],
      list2Elements: [],
      listSetsElements: [],
      selected1: { pk: -2, title: 'Без группы' },
      selected2: { pk: -1, title: 'Все' },
      searchElement: '',
      typesObject: [
        'Бактерии',
        'Антибиотики',
      ],
      typesGroups: ['Группы'],
      searchTypesObject: 'Бактерии',
      searchTypesGroups: 'Группы',
      editElementTitle: '',
      editElementFsli: '',
      editElementLis: '',
      editElementHide: false,
      editElementPk: -1,
      editElementGroup: '',
      newgroup: '',
      group_edit_open: false,
      isFcafbgOpen: false,
    };
  },
  computed: {
    filteredList() {
      return this.list1Elements.filter((element) => element.title.toLowerCase().includes(this.searchElement.toLowerCase()));
    },
  },
  watch: {
    selected1() {
      this.load_culture_groups(this.selected1.title, '1');
    },
    selected2() {
      this.load_culture_groups(this.selected2.title, '2');
    },
  },
  mounted() {
    this.load_culture_groups(this.selected1.title, '1');
    this.load_culture_groups(this.selected2.title, '2');
    this.$root.$on('hide_ge', () => this.group_edit_hide());
    this.$root.$on('hide_fcafbg', () => this.hide_fcafbg());
    this.$root.$on('select2', async (obj) => {
      await this.load_culture_groups(this.selected1.title, '1');
      this.selected2 = obj;
    });
  },
  methods: {
    group_edit() {
      this.group_edit_open = true;
    },
    async group_edit_hide() {
      this.group_edit_open = false;
      await this.load_culture_groups(this.selected1.title, '1');
      await this.load_culture_groups(this.selected2.title, '2');
    },
    openFcafbg() {
      this.isFcafbgOpen = true;
    },
    async hide_fcafbg() {
      this.isFcafbgOpen = false;
      await this.load_culture_groups(this.selected1.title, '1');
      await this.load_culture_groups(this.selected2.title, '2');
    },
    async load_culture_groups(titlegroupOrig, objList) {
      let titlegroup = titlegroupOrig;
      if (!titlegroup || titlegroup.length === 0) {
        titlegroup = 'Все';
        this.selected1 = { pk: -2, title: 'Без группы' };
        this.selected2 = { pk: -1, title: 'Все' };
      }
      if (this.searchTypesGroups === 'Группы') {
        bacteriaPoint.loadCultures({ type: titlegroup, searchObj: this.searchTypesObject })
          .then((data) => {
            this.list1 = data.groups;
            this.list2 = [...this.list1];
            if (objList === '1') {
              this.list1Elements = data.elements;
            } else {
              this.list2Elements = data.elements;
            }
          });
      } else {
        bacteriaPoint.loadCultures({ type: this.selected1.title, searchObj: this.searchTypesObject })
          .then((data) => {
            this.list1 = data.groups;
            this.list2Elements = [];
            this.list1Elements = data.elements;
          });

        const data = await bacteriaPoint.loadantibioticset({
          TypesObject: this.searchTypesObject,
          typeGroups: this.searchTypesGroups,
        });
        this.list2 = data.groups;
        this.list2Elements = [];
        if (this.selected2.title !== 'Все') {
          const setElements = await bacteriaPoint.loadSetElements({
            type: this.selected2.title,
            typeGroups: this.searchTypesGroups,
          });
          this.list2Elements = setElements.elements;
        }
      }
    },
    onEditElement(element) {
      this.editElementPk = element.pk;
      this.editElementTitle = element.title;
      this.editElementFsli = element.fsli;
      this.editElementLis = element.lis;
      this.editElementHide = element.hide;
      this.editElementGroup = element.group;
    },
    onAddToSet(element) {
      this.list2Elements.push(element);
    },
    delFromlistSetsElements(element) {
      this.list2Elements = this.list2Elements.filter((item) => item !== element);
    },
    async save_element() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await bacteriaPoint.saveElement({
        TypesObject: this.searchTypesObject,
        title: this.editElementTitle,
        fsli: this.editElementFsli,
        pk: this.editElementPk,
        hide: this.editElementHide,
        lis: this.editElementLis,
      });
      if (ok) {
        this.$root.$emit('msg', 'ok', `Элемент сохранён\n${this.searchTypesObject} – ${this.editElementTitle}`);
      } else {
        this.$root.$emit('msg', 'error', `Ошибка\n${message}`);
      }
      this.onClearContentEdit();
      await this.load_culture_groups(this.selected1.title, '1');
      await this.load_culture_groups(this.selected2.title, '2');
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    onClearContentEdit() {
      this.editElementTitle = '';
      this.editElementFsli = '';
      this.editElementLis = '';
      this.editElementPk = -1;
      this.editElementHide = false;
      this.editElementGroup = '';
    },
    async addNewGroup() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message, obj = this.selected2 } = await bacteriaPoint.addNewGroup({
        TypesObject: this.searchTypesObject,
        typeGroups: this.searchTypesGroups,
        newgroup: this.newgroup,
      });
      if (ok) {
        this.newgroup = '';
        await this.load_culture_groups(this.selected1.title, '1');
        this.selected2 = obj;
        this.$root.$emit('msg', 'ok', `Сохранено\n${this.searchTypesGroups} - ${this.searchTypesObject} – ${this.newgroup}`);
      } else {
        this.$root.$emit('msg', 'error', `Ошибка\n${message}`);
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async save_groups() {
      const pksElements2 = [];
      for (const i of this.list2Elements) {
        pksElements2.push(i.pk);
      }
      const pksElements1 = [];
      for (const i of this.list1Elements) {
        pksElements1.push(i.pk);
      }
      await this.$store.dispatch(actions.INC_LOADING);
      const { ok, message } = await bacteriaPoint.saveGroup({
        TypesObject: this.searchTypesObject,
        typeGroups: this.searchTypesGroups,
        obj: [{ group: this.selected1.title, elements: pksElements1 }, {
          group: this.selected2.title,
          elements: pksElements2,
        }],
        set: { group: this.selected2.title, elements: pksElements2 },
      });
      if (ok) {
        this.$root.$emit('msg', 'ok', `Группа сохранена\n${this.searchTypesObject} – ${this.selected2.title}`);
      } else {
        this.$root.$emit('msg', 'error', `Ошибка\n${message}`);
      }
      this.onClearContentEdit();
      await this.load_culture_groups(this.selected1.title, '1');

      await this.$store.dispatch(actions.DEC_LOADING);
    },
    filteredGroupObject() {
      this.load_culture_groups(this.selected1.title, '1');
      this.selected1 = { pk: -2, title: 'Без группы' };
      this.selected2 = { pk: -1, title: 'Все' };
      if (this.searchTypesObject !== 'Антибиотики') {
        this.searchTypesGroups = 'Группы';
      }
      this.typesGroups = this.searchTypesObject === 'Антибиотики' ? ['Группы', 'Наборы'] : ['Группы'];
    },
  },
};
</script>

<style lang="scss">
  body {
    background: #fff;
  }
</style>

<style lang="scss" scoped>
  .radio-button-object {
    width: 70%;
    margin-left: auto;
    margin-right: auto;
    margin-top: 2%;
  }

  .radio-button-groups {
    width: 40%;
    margin-bottom: 3%;
  }

  .sidebar-footer {
    border-radius: 4px;
    margin: 0;
  }

  .lists {
    padding: 0 70px;
  }

  .content-edit {
    height: 330px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
    position: relative;
    border-radius: 4px;
    padding: 5px;
  }

  .edit-element {
    background: #fff;
  }

  .list-group {
    height: 330px;
    overflow-y: scroll;
    background: #fff;

    .item {
      background-color: #fff;
      padding: 1px;
      margin: 7px;
      border-radius: 4px;
      cursor: pointer;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
      position: relative;

      i {
        cursor: pointer;
        float: right;
      }
    }
  }

  .margin-top {
    margin-top: 34px;
    margin-bottom: 20px;
  }

  .buttons {
    padding: 0 70px;
    margin-right: auto;
    display: flex;
    width: 100%;
    align-items: flex-start;

    .button-create {
      width: calc(50% - 5px);
      margin-right: 10px;
    }
  }

  .sidebar-btn {
    float: right;
    border-radius: 4px;

    &:not(.text-center) {
      text-align: left;
    }

    border-top: none !important;
    border-right: none !important;
    border-left: none !important;
    border-bottom: none !important;
    padding: 4px;
    height: 23px;

    &:not(:hover), &.active-btn:hover {
      cursor: default;
      background-color: rgba(#737373, .01) !important;
      color: #37BC9B;
    }
  }

  .background {
    padding: 0;
    background-color: #cacfd2;
    border-radius: 4px;
  }

  .sub-buttons {
    text-align: center;
    margin: 15px;
  }

</style>
