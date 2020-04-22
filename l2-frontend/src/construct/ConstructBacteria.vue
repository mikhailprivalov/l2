<template>
    <div>
        <div class="r-button">
          <radio-field v-model="searchTypes" :variants="types" fullWidth />
        </div>
        <div class="lists">
          <div class="left">
             <v-select :clearable="false" label="title" :options="bacteriaGroups" :searchable="true"
                           v-model="selected"/>
            <input type="text" v-model="searchElement" placeholder="Фильтр по названию.."/>
            <draggable class="list-group" :list="list1" group="people" @change="log">

              <div class="item" v-for="(element) in filteredList" :key="element.title">
                {{ element.title }} <i class="glyphicon glyphicon-pencil"></i>
              </div>

            </draggable>
            <button class="btn btn-blue-nb sidebar-footer" @click="load_culture_groups">
                <i class="glyphicon glyphicon-plus"></i>
                Добавить
            </button>
            <button class="btn btn-blue-nb sidebar-footer" @click="load_culture_groups">
                Сохранить
            </button>

          </div>

            <div class="right">
               <v-select :clearable="false" label="title" :options="bacteriaGroups2" :searchable="true"
                           v-model="selected1"/>
                <draggable class="list-group" :class="['right-top']" :list="list2" group="people" @change="log">
                  <div class="item" v-for="(element) in list2" :key="element.title">
                    {{ element.title }}
                  </div>
                </draggable>
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
        bacteriaGroups: [],
        bacteriaGroups2: [],
        list1: [],
        list2: [],
        bacteriaGroup: 'all',
        selected: '',
        selected1: '',
        searchElement: '',
        types: [
            'Бактерии',
            'Антибиоткики',
            'Бактериофаги',
            // 'Среды',
        ],
        searchTypes: ""
      }
    },
    created() {
         this.load_culture_groups()
    },
    methods:{
        load_culture_groups() {
        const t = this;
        t.bacteriaGroups = [];
        t.bacteriaGroups2 = [];
        fetch("/api/bacteria/loadculture?type=" + t.bacteriaGroup).then(r => r.json()).then(data => {
          console.log("22",data.groups)
          t.bacteriaGroups = data.groups
          // t.bacteriaGroups2 = JSON.parse(JSON.stringify(t.bacteriaGroups));
          t.bacteriaGroups2 = {...data.groups}
          t.list1 = data.groups
          t.list2 = [{"pk": "43", "title": "Бактерия1"}, {"pk": "44", "title": "Бактерия2"},
            {"pk": "45", "title": "Бактеррррррр ррррррррррррррррррр рррррррррия3"},
            {"pk": "46", "title": "Бактерия4"}, {"pk": "23", "title": "Бактерия5"}, {"pk": "24", "title": "Бактерия6"},
            {"pk": "25", "title": "Бактерия7"}, {"pk": "26", "title": "Бактерия8"}]
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
      return this.list1.filter(element => {
        return element.title.toLowerCase().includes(this.searchElement.toLowerCase())
      })
    }
  }

    }
</script>

<style lang="scss" scoped>
  input[type="text"] {
    width: 45vh;
}
  .r-button {
    /*width: 500px;*/
    width: 70%;
    margin-left: auto;
    margin-right: auto;
    margin-top: 2%;
    margin-bottom: 3%;
  }
  .sidebar-footer {
    border-radius: 4px;
    margin: 0;
  }
  .glyphicon {
    alignment: right;
  }
  .lists {
    padding-left: 5vw;
    margin-left: auto;
    margin-right: auto;
    display: flex;
    width: 70%;

    align-items: flex-start;

    .left,
    .right {
      padding-left: 40px;
      .list-group {
        height: 40vh;
        width: 45vh;
        overflow-y: scroll;
        .item {
          background-color: #fff;
          padding: 3px;
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


</style>
