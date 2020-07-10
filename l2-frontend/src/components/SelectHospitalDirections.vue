<template>
  <div>
    <div class="form-group sidebar-history">
      <div style="background-color: white">
        <v-select :clearable="false" label="label" :options="dirs_options"
                  :searchable="true" placeholder="Выберите историю болезни"/>
      </div>
    </div>
  </div>
</template>

<script>
  import vSelect from 'vue-select'
  import 'vue-select/dist/vue-select.css';
  // import directions_point from '../api/directions-point'

    import Treeselect from '@riophae/vue-treeselect'
  import '@riophae/vue-treeselect/dist/vue-treeselect.css'
  export default {
    name: "SelectHospitalDirections",
    components: {vSelect, Treeselect},
    data() {
      return {
        cards: [],
        individuals: [],
        dirs_options: ['члх', 'нейрохирургия', 'ОПН', 'травматология', 'Пульмунология',],
                options: [{
          id: 'fruits',
          label: 'Fruits',
          children: [{
            id: 'apple',
            label: 'Apple 🍎',
            isNew: true,
          }, {
            id: 'grapes',
            label: 'Grapes 🍇',
          }, {
            id: 'pear',
            label: 'Pear 🍐',
          }, {
            id: 'strawberry',
            label: 'Strawberry 🍓',
          }, {
            id: 'watermelon',
            label: 'Watermelon 🍉',
          }],
        }, {
          id: 'vegetables',
          label: 'Vegetables',
          children: [{
            id: 'corn',
            label: 'Corn 🌽',
          }, {
            id: 'carrot',
            label: 'Carrot 🥕',
          }, {
            id: 'eggplant',
            label: 'Eggplant 🍆',
          }, {
            id: 'tomato',
            label: 'Tomato 🍅',
          }],
        }],
      }
    }
  }
</script>

<style scoped lang="scss">
   $sidebar-history-width: 240px;
    .sidebar-history {
    width: $sidebar-history-width;
    height: 420px;
    border-right: 1px solid #56616c;
  }

</style>
