<template>
  <div class="main">
    <div class="company card-1 card-no-hover">
      <h5 class="text-center">
        Компании
      </h5>
      <input
        class="form-control"
        placeholder="Фильтр по названию..."
      >
      <div class="scroll">
        <table class="table table-bordered">
          <colgroup>
            <col>
            <col width="40">
          </colgroup>
          <tr>
            <td class="title">
              Название компании очень длинное оно что просто очень длинное прям очень
            </td>
            <td>
              <button
                v-tippy
                title="Редактировать"
                class="btn last btn-blue-nb nbr"
              >
                <i class="fa fa-pencil" />
              </button>
            </td>
          </tr>
        </table>
      </div>
    </div>
    <div class="edit card-1 card-no-hover">
      <h5 class="text-center">
        Редактирование
      </h5>
      <div>
        <label>Полное название</label>
        <input class="form-control">
        <label>Сокращенное название</label>
        <input class="form-control">
        <label>Код 1</label>
        <input class="form-control">
        <label>Код 2</label>
        <input class="form-control">
      </div>
    </div>
  </div>
</template>

<script lang="ts">
export default {
  name: 'ConstructCompany',
};
</script>

<style scoped>
.company {
  width: 50%;
  background-color: #FFF;
  margin-right: 20px;
}
.edit {
  width: 50%;
  background-color: #FFF;
  margin-left: 20px;
}
.main {
  display: flex;
  max-height: 80vh;
}
.scroll {
  overflow-y: auto;
  max-height: 70%;
}
.title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
</style>
