<template>
  <div ref="root" class="construct-root" >
    <div class="construct-sidebar">
      <div class="sidebar-select" style="padding-top: 20px; padding-left: 15px">
<!--        <select-picker-m style="height: 34px;" :options="bacteriaGroups" v-model="bacteriaGroup"/>-->
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
       </div>
    </div>

  </div>

</template>

<script>
  import vSelect from 'vue-select'

    export default {
      name: "ConstructBacteria",
      components: {
      vSelect,
    },
      data() {
      return {
        bacteriaGroups: [],
        bacteriaGroup: 'all',
        selected:''
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
        })
      },
       someDummyMethod() {
      console.log('Hello from someDummyMethod');
    }
    },
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

<style scoped>

</style>
