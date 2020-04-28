<template>
    <div>
        <div class="radio-button-object">
          <radio-field v-model="searchTypesObject" :variants="typesObject" fullWidth @click="filteredGroupObject"/>
        </div>

        <div class="radio-button-object radio-button-groups">
           <radio-field v-model="searchTypesGroups" :variants="typesGroups" fullWidth @click="onChangeGroup"/>
        </div>

        <div class="lists">
          <div class="edit-element" >
            <h6><strong>{{searchTypesObject}}</strong> (создание/редактирование)</h6>
            <div class="content-edit" :class="['right-top']">
                Название:
                  <button class="btn btn-blue-nb sidebar-btn" style="font-size: 12px" @click="onClearContentEdit">
                    <i class="glyphicon glyphicon-remove" v-tippy="{ placement : 'bottom'}" title="Очистить"></i>
                  </button>
              <input type="text" v-model="editElementTitle" :placeholder="[[searchTypesObject]] + ': введите название' " />
              <p>Код ФСЛИ</p>
              <input type="text" v-model="editElementFsli" placeholder="Введите код ФСЛИ.."/>
              <p>
              Скрыть
              <input type="checkbox" id="checkbox" v-model="editElementHide">
              </p>
              <p>{{editElementPk}}</p>
            </div>
          </div>

          <div class="left">
             <v-select :clearable="false" label="title" :options="list1" :searchable="true" placeholder="Выберите группу"
                           v-model="selected1" v-on:change="load_culture_groups(selected1.title, '1')"/>

            <input type="text" v-model="searchElement" placeholder="Фильтр по названию.."/>
            <draggable class="list-group" :list="list1Elements" group="some">
              <div class="item" v-for="(element) in filteredList" :key="element.title">
                <div :class="{background: element.hide}">
                  {{ element.title }}
                  <button class="btn btn-blue-nb sidebar-btn" style="font-size: 12px">
                    <i class="glyphicon glyphicon-pencil" v-if="searchTypesGroups === 'Группы'" @click="onEditElement(element)"/>
                    <i class="glyphicon glyphicon-arrow-right" @click="onAddToSet(element)" v-tippy="{ placement : 'bottom'}" title="Добавить в набор" v-else/>
                    </button>
                </div>
                </div>
            </draggable>
          </div>

          <div class="right">
              <v-select :clearable="false" label="title" :options="list2" :searchable="true"
                         v-model="selected2" v-on:change="load_culture_groups(selected2.title, '2')"/>
            <input type="text" v-model="newgroup" style = "width: 92%"   placeholder="Добавить группу"/>
              <button class="btn btn-blue-nb sidebar-btn" style="font-size: 12px">
                <i class="fa fa-floppy-o fa-lg" aria-hidden="true" @click="addNewGroup"
                   v-tippy="{ placement : 'bottom'}" :title="'Соханить в '+ '&#171;' + [[searchTypesGroups.toUpperCase().trim()]] +'&#187;'"></i>
              </button>
             <draggable v-if="searchTypesGroups === 'Группы'" class="list-group" :list="list2Elements" group="some">
                <div class="item" v-for="(element) in list2Elements" :key="element.title">
                  <div :class="{background: element.hide}">{{ element.title }}</div>
                </div>
              </draggable >
              <div v-else class="list-group" :list="list2"  >
                <div class="item" v-for="(element) in list2Elements" :key="element.title">
                  <div :class="{background: element.hide}">
                    {{ element.title }}
                     <button class="btn btn-blue-nb sidebar-btn" style="font-size: 12px" @click="delFromlistSetsElements(element)">
                       <i class="glyphicon glyphicon-remove" v-tippy="{ placement : 'bottom'}" title="Удалть из Набора"></i>
                     </button>
                  </div>
                </div>
              </div >

            </div>
          </div>
       <div class="buttons">
         <div class="button-create">
           <button class="btn btn-blue-nb sidebar-footer" @click="save_element">
             Сохранить
           </button>
         </div>
         <div class="button-create"></div>
          <div class="button-create">
           <button class="btn btn-blue-nb sidebar-footer" @click="save_groups">
             Сохранить
           </button>
           <button class="btn btn-blue-nb sidebar-footer" @click="group_edit">
             Изменить название
           </button>
         </div>

       </div>
          <bacteria-edit-title-group v-if="group_edit_open"
                           :group_title="Uheggf"
                           :group_pk="-3"
                           :typesGroups="searchTypesGroups"
    />
    </div>

</template>

<script>
  import bacteria_point from '../api/bacteria-point'
  import vSelect from 'vue-select'
  import draggable from "vuedraggable";
  import RadioField from '../fields/RadioField'
  import BacteriaEditTitleGroup from './BacteriaEditTitleGroup'
  import * as action_types from "../store/action-types";

    export default {
      name: "ConstructBacteria",
      components: {
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
        selected1: "" ,
        selected2: "",
        searchElement: '',
        typesObject: [
            'Бактерии',
            'Антибиотики',
            'Бактериофаги',
        ],
        typesGroups: [],
        searchTypesObject: "Бактерии",
        searchTypesGroups: "",
        editElementTitle: "",
        editElementFsli: "",
        editElementHide: "",
        editElementPk: -1,
        newgroup: "",
        group_edit_open: false
      }
    },
    methods:{
      group_edit() {
        this.group_edit_open = true
      },
      group_edit_hide() {
        this.group_edit_open = false
      },
      async load_culture_groups(titlegroup, objList) {
        const t = this;
        if (!titlegroup || titlegroup.length === 0) {
          titlegroup = "Все"
        }
        if (t.searchTypesGroups === "Группы") {
          bacteria_point.loadCultures({'type': titlegroup, 'searchObj': t.searchTypesObject})
            .then(data => {
                t.list1 = data.groups;
                t.list2 = [...t.list1];
                objList === "1" ? t.list1Elements = data.elements : t.list2Elements = data.elements;
              }
            )
        } else {
          bacteria_point.loadCultures({'type': titlegroup, 'searchObj': t.searchTypesObject})
            .then(data => {
                t.list1 = data.groups;
                objList === "1" ? t.list1Elements = data.elements : t.list2Elements = data.elements;
              }
            );

          const data = await bacteria_point.loadantibioticset({
            'TypesObject': t.searchTypesObject,
            'typeGroups': t.searchTypesGroups
          });
          t.list2 = data.groups;
          t.list2Elements = [];
          if (titlegroup.length !== 0) {
            const setElements = await bacteria_point.loadSetElements({
              'type': titlegroup,
              'typeGroups': t.searchTypesGroups
            });
            t.list2Elements = setElements.elements
          }
        }
      },
      onEditElement: function(element) {
          this.editElementPk = element.pk;
          this.editElementTitle = element.title;
          this.editElementFsli = element.fsli;
          this.editElementHide = element.hide;
       },
      onAddToSet(element) {
          return this.list2Elements.push(element)
      },
      delFromlistSetsElements(element){
        return this.list2Elements = this.list2Elements.filter(item => item !== element)
      },
      async save_element() {
        this.$store.dispatch(action_types.INC_LOADING).then();
        const {ok, message} = await bacteria_point.saveElement({'TypesObject': this.searchTypesObject ,'title': this.editElementTitle, 'fsli': this.editElementFsli,
          'pk': this.editElementPk, 'hide': this.editElementHide});
        if (ok) {
          okmessage('Элемент сохранён', `${this.searchTypesObject} – ${this.editElementTitle}`)
        } else {
          errmessage('Ошибка', message)
        }
        this.onClearContentEdit();
        this.load_culture_groups("Все", "1")
        this.$store.dispatch(action_types.DEC_LOADING).then()
      },
      onClearContentEdit() {
        this.editElementTitle = '';
        this.editElementFsli = '';
        this.editElementPk = -1;
      },
      async addNewGroup() {
        this.$store.dispatch(action_types.INC_LOADING).then();
        const {ok, message} = await bacteria_point.addNewGroup({'TypesObject': this.searchTypesObject, 'typeGroups': this.searchTypesGroups,
            'newgroup': this.newgroup});
        if (ok) {
          this.load_culture_groups("Все", "1");
          okmessage('Сохранено в:', `${this.searchTypesGroups} - ${this.searchTypesObject} – ${this.newgroup}`)
        } else {
          errmessage('Ошибка', message)
        }
          this.$store.dispatch(action_types.DEC_LOADING).then()
      },
      async save_groups() {
        let pksElements2 = [];
        for (let i in this.list2Elements) {
          if (i > -1) {
            pksElements2.push(this.list2Elements[i].pk)
            }
          }
        let pksElements1 = [];
        for (let i in this.list1Elements) {
          if (i > -1) {
            pksElements1.push(this.list1Elements[i].pk)
            }
          }
        this.$store.dispatch(action_types.INC_LOADING).then();
        const {ok, message} = await bacteria_point.saveGroup({'TypesObject': this.searchTypesObject, 'typeGroups': this.searchTypesGroups,
          'obj': [{'group':this.selected1.title, 'elements': pksElements1}, {'group': this.selected2.title, 'elements': pksElements2}],
           'set': {'group': this.selected2.title, 'elements': pksElements2}});
        if (ok) {
          okmessage('Группа сохранена', `${this.searchTypesObject} – ${this.selected2.title}`)
        } else {
          errmessage('Ошибка', message)
        }
        this.onClearContentEdit();
        this.load_culture_groups("Все", "1");
        pksElements1 = [];
        pksElements2 = [];
        this.$store.dispatch(action_types.DEC_LOADING).then()
      }
    },
      // created() {
      //   this.load_culture_groups("Все", "1")
      // },
      computed: {
       filteredList() {
        return this.list1Elements.filter(element => {
          return element.title.toLowerCase().includes(this.searchElement.toLowerCase())
      })
    },
       filteredGroupObject() {
         this.load_culture_groups("Все", "1")
         this.selected1 = '';
         this.selected2 = '';
         if (this.searchTypesObject === "Бактерии") {
         this.searchTypesGroups = 'Группы';}
         return this.searchTypesObject === "Антибиотики" ? this.typesGroups = ['Группы', 'Наборы'] : this.typesGroups = ['Группы'];
       },
       onChangeGroup() {
         if (this.searchTypesGroups === "Наборы") {
           this.list2 = [];
           this.list2Elements = [];
           this.onClearContentEdit();
           return this.selected2 = "";
         }
         else {
           this.load_culture_groups("Все", "1");
           return this.onClearContentEdit();
         }
       }
    }
  }
</script>

<style lang="scss" scoped>
  input[type="text"] {
    width: 45vh;
}

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
    padding-left: 5vw;
    margin-left: auto;
    margin-right: auto;
    display: flex;
    width: 100%;
    align-items: flex-start;
    .content-edit {
      height: 40vh;
      width: 45vh;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
      transition: all .2s cubic-bezier(.25, .8, .25, 1);
      position: relative;
      border-radius: 4px;
      padding-right: 50px;
    }
    .left,
    .right {
      padding-left: 40px;
      .list-group {
        height: 40vh;
        width: 45vh;
        overflow-y: scroll;
        .item {
          background-color: #fff;
          padding: 1px;
          margin: 7px;
          border-radius: 4px;
          cursor: pointer;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
          transition: all .2s cubic-bezier(.25, .8, .25, 1);
          position: relative;
          i {
            cursor: pointer;
            float: right;
          }
        }
      }
    }
  }

  .right-top {
    margin-top: 3.5vh;
  }


  .buttons {
    padding-left: 5vw;
    margin-right: auto;
    display: flex;
    width: 100%;
    align-items: flex-start;

  .button-create {
    height: 5vh;
    width: 45vh;
    margin-right: 40px;
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

  p{
    padding-top: 15px;
  }
  input {
    border-radius: 4px;}

  .background {
    padding: 0;
    background-color: #cacfd2;
    border-radius: 4px;
  }

</style>
