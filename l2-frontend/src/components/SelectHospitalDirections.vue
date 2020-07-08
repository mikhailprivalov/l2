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
  export default {
    name: "SelectHospitalDirections",
    components: {vSelect},
    data() {
      return {
        cards: [],
        individuals: [],
        dirs_options: ['члх', 'нейрохирургия', 'ОПН', 'травматология', 'Пульмунология',]
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
