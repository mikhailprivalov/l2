<template>
    <div>
        <div class="radio-button-object">
          <radio-field v-model="searchTypesObject" :variants="typesObject" fullWidth @click="filteredtypesGroups"/>
        </div>
        <div class="radio-button-object radio-button-groups">
           <radio-field v-model="searchTypesGroups" :variants="typesGroups" fullWidth />
        </div>

        <div class="lists">
          <div class="edit-element" >
            <h6><strong>{{searchTypesObject}}</strong> (создание/редактирование)</h6>
            <div class="content-edit" :class="['right-top']">
              Название:
              <input type="text" :placeholder="[[searchTypesObject]] + ': введите название' " />
              <p>Код ФСЛИ</p>
              <input type="text" placeholder="Введите код ФСЛИ.."/>
            </div>
          </div>

          <div class="left">
             <v-select :clearable="false" label="title" :options="list1" :searchable="true"
                           v-model="selected"/>
            <input type="text" v-model="searchElement" placeholder="Фильтр по названию.."/>
            <draggable class="list-group" :list="list1Elements" group="some" @change="log">
              <div class="item" v-for="(element) in filteredList" :key="element.title">
                <div>
                  {{ element.title }}
                  <button class="btn btn-blue-nb sidebar-btn"
                      style="font-size: 12px"
                      @click="load_culture_groups">
                    <i class="glyphicon glyphicon-pencil" v-if="searchTypesGroups === 'Группы'"/>
                    <i class="glyphicon glyphicon-arrow-right" v-tippy="{ placement : 'bottom'}" title="Добавить в набор" v-else/>
                    </button>
                </div>

                </div>
            </draggable>

          </div>

          <div class="right">
             <v-select :clearable="false" label="title" :options="list2" :searchable="true"
                         v-model="selected1"/>
              <draggable v-if="searchTypesGroups === 'Группы'" class="list-group" :class="['right-top']" :list="list2Elements" group="some" @change="log" >
                <div class="item" v-for="(element) in list2Elements" :key="element.title">
                  {{ element.title }}
                </div>
              </draggable >
              <div v-else class="list-group" :class="['right-top']" :list="list2"  >
                <div class="item" v-for="(element) in list2" :key="element.title">
                  {{ element.title }}
                </div>
              </div >

            </div>
          </div>
       <div class="buttons">
         <div class="button-create">
           <button class="btn btn-blue-nb sidebar-footer" @click="load_culture_groups">
             Сохранить
           </button>
         </div>
         <div class="button-create"></div>
          <div class="button-create">
           <button class="btn btn-blue-nb sidebar-footer" @click="load_culture_groups">
             <i class="glyphicon glyphicon-plus"></i>
             Создать
           </button>
           <button class="btn btn-blue-nb sidebar-footer" @click="load_culture_groups">
             Сохранить
           </button>
         </div>

       </div>
    </div>

</template>

<script>

  import vSelect from 'vue-select'
  import draggable from "vuedraggable";
  import RadioField from '../fields/RadioField'

    export default {
      name: "ConstructBacteria",
      components: {
      vSelect,
      draggable,
        RadioField
    },
      data() {
      return {
        list1: [],
        list2: [],
        list1Elements: [],
        list2Elements: [],
        bacteriaGroup: 'all',
        selected: '',
        selected1: '',
        searchElement: '',
        typesObject: [
            'Бактерии',
            'Антибиоткики',
            'Бактериофаги',
        ],
        typesGroups: [],
        searchTypesObject: "",
        searchTypesGroups: ""
      }
    },
    created() {
         this.load_culture_groups()
    },
    methods:{
        load_culture_groups() {
        const t = this;
        fetch("/api/bacteria/loadculture?type=" + t.bacteriaGroup).then(r => r.json()).then(data => {
          t.list1 = data.groups
          t.list2 = [...t.list1]
          t.list1Elements = data.elements
          t.list2Elements = [...t.list1Elements]
        })
      },
      log: function(evt) {
        window.console.log(evt);
      }},
     watch: {
        bacteriaGroup() {
        this.load_culture_groups()
      }
    },
     computed: {
        selectedID: function () {
           return this.selected.title
    },
       filteredList() {
      return this.list1Elements.filter(element => {
        return element.title.toLowerCase().includes(this.searchElement.toLowerCase())
      })
    },
       filteredtypesGroups() {
         return this.searchTypesObject === "Антибиоткики" ? this.typesGroups = ['Группы', 'Наборы'] : this.typesGroups = ['Группы']
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

</style>
