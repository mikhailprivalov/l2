<template>
  <div>
    <div class="radio-button-object">
      <radio-field v-model="searchTypesObject" :variants="typesObject" @modified="filteredGroupObject" fullWidth/>
    </div>

    <div class="radio-button-object radio-button-groups">
      <radio-field v-model="searchTypesGroups" :variants="typesGroups" fullWidth @modified="filteredGroupObject"/>
    </div>

    <div class="row lists">
      <div class="col-xs-4">
        <div class="edit-element">
          <h6><strong>{{searchTypesObject}}</strong> (создание/редактирование)</h6>

          <div class="content-edit margin-top">
            <div class="form-group">
              <label for="create-title">Название:</label>
              <div class="input-group">
                <input class="form-control" v-model="editElementTitle"
                       id="create-title"
                       :placeholder="`${searchTypesObject}: введите название`">
                <span class="input-group-btn">
                  <button @click="onClearContentEdit" class="btn btn-default btn-primary-nb"
                          v-tippy="{ placement : 'bottom'}" title="Очистить">
                    <i class="fa fa-times"/>
                  </button>
                </span>
              </div>
            </div>
            <div class="form-group">
              <label for="create-fsli">Код ФСЛИ:</label>
              <input class="form-control" id="create-fsli" v-model="editElementFsli" placeholder="Введите код ФСЛИ.."/>
            </div>
            <div class="form-group">
              <label for="create-code-lis">Код LIS:</label>
              <input class="form-control" id="create-code-lis" v-model="editElementLis" placeholder="Введите код LIS"/>
            </div>
            <div class="checkbox">
              <label>
                <input type="checkbox" v-model="editElementHide"> Скрыть
              </label>
            </div>
            <div class="form-group"><strong>Группа:</strong> {{editElementGroup || 'все' }}</div>
          </div>
        </div>

        <button class="btn btn-blue-nb sidebar-footer" @click="save_element">
          Сохранить
        </button>
      </div>

      <div class="col-xs-4">
        <v-select :clearable="false" label="title" :options="list1" :searchable="true" placeholder="Выберите группу"
                  v-model="selected1" @change="load_culture_groups(selected1.title, '1')"
                  :class="{background: selected1.hide}"
        />
        <input class="form-control" v-model="searchElement" placeholder="Фильтр по названию.."/>
        <draggable class="list-group" :list="list1Elements" group="some">
          <div class="item" v-for="element in filteredList" :key="element.title">
            <div :class="{background: element.hide}">
              {{ element.title }}
              <button class="btn btn-blue-nb sidebar-btn" style="font-size: 12px">
                <i class="glyphicon glyphicon-pencil" v-if="searchTypesGroups === 'Группы'"
                   @click="onEditElement(element)"/>
                <i class="glyphicon glyphicon-arrow-right" @click="onAddToSet(element)"
                   v-tippy="{ placement : 'bottom'}" title="Добавить в набор" v-else-if="selected2.title !== 'Все'"/>
              </button>
            </div>
          </div>
        </draggable>
      </div>

      <div class="col-xs-4">
        <v-select :clearable="false" label="title" :options="list2" :searchable="true"
                  v-model="selected2" @change="load_culture_groups(selected2.title, '2')"
                  :class="{background: selected2.hide}"
        />

        <div class="input-group">
          <input class="form-control" v-model="newgroup"
                 :placeholder="`Добавить: ${searchTypesGroups}`">
          <span class="input-group-btn">
            <button @click="addNewGroup" class="btn btn-default btn-primary-nb"
                    v-tippy="{ placement : 'bottom' }"
                    :title="`Соханить в &#171;${searchTypesGroups.toUpperCase().trim()}&#187;`">
              <i class="fa fa-floppy-o"/>
            </button>
          </span>
        </div>

        <draggable v-if="searchTypesGroups === 'Группы'" class="list-group" :list="list2Elements" group="some">
          <div class="item" v-for="element in list2Elements" :key="element.title">
            <div :class="{background: element.hide}">{{ element.title }}</div>
          </div>
        </draggable>
        <div v-else class="list-group">
          <div class="item" v-for="element in list2Elements" :key="element.title">
            <div :class="{background: element.hide}">
              {{ element.title }}
              <button class="btn btn-blue-nb sidebar-btn"
                      v-if="selected2.title !== 'Все'"
                      v-tippy="{ placement : 'bottom'}" title="Удалть из Набора"
                      @click="delFromlistSetsElements(element)">
                <i class="fa fa-times"/>
              </button>
            </div>
          </div>
        </div>

        <button class="btn btn-blue-nb sidebar-footer" @click="save_groups">
          Сохранить
        </button>
        <button class="btn btn-blue-nb sidebar-footer" @click="group_edit" v-if="selected2.pk >= 0">
          Редактировать группу
        </button>
      </div>
    </div>

    <div class="sub-buttons">
      <button class="btn btn-blue-nb" @click="openFcafbg" v-if="searchTypesGroups === 'Группы'">
        Быстрое создание и заполнение: {{searchTypesObject}} – {{searchTypesGroups}}
      </button>
    </div>

    <bacteria-edit-title-group v-if="group_edit_open"
                               :group_obj="selected2"
                               :typesObject="searchTypesObject"
                               :typesGroups="searchTypesGroups"/>

    <fast-create-and-fill-bacteria-group v-if="isFcafbgOpen"
                                         :typesObject="searchTypesObject"
                                         :typesGroups="searchTypesGroups"/>
  </div>
</template>

<script>
import vSelect from 'vue-select';
import 'vue-select/dist/vue-select.css';
import draggable from 'vuedraggable';
import bacteriaPoint from '../api/bacteria-point';
import RadioField from '../fields/RadioField.vue';
import BacteriaEditTitleGroup from '../modals/BacteriaEditTitleGroup.vue';
import * as actions from '../store/action-types';
import FastCreateAndFillBacteriaGroup from '../modals/FastCreateAndFillBacteriaGroup.vue';

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
        'Бактериофаги',
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
        window.okmessage('Элемент сохранён', `${this.searchTypesObject} – ${this.editElementTitle}`);
      } else {
        window.errmessage('Ошибка', message);
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
        window.okmessage('Сохранено', `${this.searchTypesGroups} - ${this.searchTypesObject} – ${this.newgroup}`);
      } else {
        window.errmessage('Ошибка', message);
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
        window.okmessage('Группа сохранена', `${this.searchTypesObject} – ${this.selected2.title}`);
      } else {
        window.errmessage('Ошибка', message);
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
