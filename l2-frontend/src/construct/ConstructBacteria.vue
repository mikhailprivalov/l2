<template>
    <div>
        <label style="width: 25%;text-align: left; ">
                Группа:
                <select class="form-control">
                    <option v-for="b in bacteriaGroups" :value="b.pk">{{b.title}}</option>
                </select>

                <v-select :clearable="false" label="title" :options="bacteriaGroups" :searchable="true"
                           v-model="selected"/>
        </label>

        <input type="text" v-model.lazy="bacteriaGroup">
        <p>{{bacteriaGroup}}</p>
        <p>selectedID : {{selectedID}}</p>
        <button class="btn btn-blue-nb sidebar-footer" @click="load_culture_groups">
          <i class="glyphicon glyphicon-plus"></i>
          Добавить
        </button>

        <div class="lists">
          <div class="left">
            <h4>Draggable 1</h4>
            <draggable class="list-group" :list="list1" group="people" @change="log">
              <div
                class="item"
                v-for="(element, index) in list1"
                :key="element.title"
              >
                {{ element.title }} {{ index }}
              </div>
            </draggable>
          </div>


            <div class="right">
            <h4>Draggable 2</h4>

                <draggable class="list-group" :list="list2" group="people" @change="log">
                  <div
                    class="item"
                    v-for="(element, index) in list2"
                    :key="element.title"
                  >
                    {{ element.title }} {{ index }}
                  </div>
                </draggable>
              </div>
          </div>
    </div>

</template>

<script>
  import vSelect from 'vue-select'
  import draggable from "vuedraggable";

    export default {
      name: "ConstructBacteria",
      components: {
      vSelect,
      draggable,
    },
      data() {
      return {
        bacteriaGroups: [],
        list1: ['1', '2', '3'],
        list2: ['2','3','5'],
        bacteriaGroup: 'all',
        selected: ''
      }
    },
    created() {
         this.load_culture_groups()
    },
    methods:{
        load_culture_groups() {
        const t = this;
        t.bacteriaGroups = [];
        fetch("/api/bacteria/loadculture?type=" + t.bacteriaGroup).then(r => r.json()).then(data => {
          console.log("22",data.groups)
          t.bacteriaGroups = data.groups
          t.list1 = data.groups
          t.list2 = [{"pk": 43, "title": "first"}, {"pk": 44, "title": "second"}, {"pk": 45, "title": "third"},
            {"pk": 46, "title": "first1"}, {"pk": 47, "title": "second1"}, {"pk": 48, "title": "third1"},
            {"pk": 49, "title": "first2"}, {"pk": 50, "title": "second2"}, {"pk": 51, "title": "third2"},
            {"pk": 43, "title": "first3"}, {"pk": 44, "title": "second3"}, {"pk": 45, "title": "third3"},
            {"pk": 46, "title": "f4irst"}, {"pk": 47, "title": "sec4ond"}, {"pk": 48, "title": "t4hird"},
            {"pk": 49, "title": "fi5st"}, {"pk": 50, "title": "secon5d"}, {"pk": 51, "title": "th5ird"}]
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
    }
  }

    }
</script>

<style lang="scss" scoped>

  .lists {
    padding-left: 5vw;
    display: flex;
    align-items: flex-start;

    .left,
    .right {
      padding: 20px;
      .list-group {
        height: 200px;
        width: 300px;
        overflow-y: scroll;
        .item {
          padding: 5px;
          border: 1px solid black;
          background-color: white;
          display: flex;
          justify-content: space-between;

        }
      }
    }
  }


</style>
