<template>
  <table class="table table-bordered table-responsive">
    <colgroup>
      <col width="40">
      <col>
      <col v-if="can_edit" width="300">
    </colgroup>
    <tbody>
    <tr v-for="department in departments">
      <td>{{ department.pk }}</td>
      <td :class="{'has-success': department.updated}"><input class="form-control" v-model="department.title" :disabled="!can_edit"/></td>
      <td v-if="can_edit"></td>
    </tr>
    <tr v-if="can_edit">
      <td></td>
      <td><input type="text" class="form-control" placeholder="Название" v-model="create.title" autofocus></td>
      <td><input type="submit" class="btn btn-primary-nb form-control" value="Добавить"></td>
    </tr>
    </tbody>
  </table>
</template>

<script>
  export default {
    name: 'departments-form',
    data() {
      return {
        create: {
          title: ''
        }
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
      }
    }
  }
</script>

<style scoped>

</style>
