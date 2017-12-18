<template>
  <table class="table table-bordered table-responsive">
    <colgroup>
      <col width="40">
      <col>
      <col v-if="can_edit" width="300">
    </colgroup>
    <tbody>
    <tr v-for="department in departments" :class="{'has-success': department.updated}">
      <td>{{ department.pk }}</td>
      <td><input class="form-control" v-model="department.title" :disabled="!can_edit"/></td>
      <td v-if="can_edit">
        <select-picker-m v-model="department.type" :options="types_options"></select-picker-m>
      </td>
    </tr>
    <tr v-if="can_edit">
      <td></td>
      <td><input type="text" class="form-control" placeholder="Название" v-model="create.title" autofocus></td>
      <td>
        <select-picker-m v-model="create.type" :options="types_options"></select-picker-m>
        <br/>
        <input type="button" class="btn btn-primary-nb form-control" @click="insert" value="Добавить" style="margin-top: 15px" :disabled="!create_valid">
      </td>
    </tr>
    </tbody>
  </table>
</template>

<script>
  import SelectPickerM from './SelectPickerM'

  export default {
    components: {SelectPickerM},
    name: 'departments-form',
    data() {
      return {
        create: {
          title: '',
          type: '0'
        }
      }
    },
    methods: {
      insert() {

      }
    },
    computed: {
      departments() {
        return this.$store.getters.allDepartments
      },
      can_edit() {
        return this.$store.getters.canEditDepartments
      },
      types() {
        return this.$store.getters.allTypes
      },
      types_options() {
        let r = []
        for (let row of this.types) {
          r.push({label: row.title, value: row.pk})
        }
        return r
      },
      create_valid() {
        return this.create.title.trim().length > 0
      }
    }
  }
</script>

<style scoped>

</style>
