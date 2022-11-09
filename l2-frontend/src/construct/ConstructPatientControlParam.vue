<template>
  <div>
    <h4>Контролируемые параметры пациентов</h4>
    <div class="card card1 card-no-hover">
      <div class="scroll">
        <table class="table">
          <colgroup>
            <col>
            <col>
            <col width="108">
            <col width="100">
            <col width="39">
            <col width="35.8">
          </colgroup>
          <thead class="sticky">
            <tr>
              <th
                class="text-center"
                style="border-right: 1px solid #ddd; border-left: 1px solid #ddd"
              >
                <strong>Название</strong>
              </th>
              <th
                class="text-center"
                style="border-right: 1px solid #ddd"
              >
                <strong>Код</strong>
              </th>
              <th
                style="border-right: 1px solid #ddd"
                class="text-center"
              >
                <strong>Глобальный</strong>
              </th>
              <th
                style="border-right: 1px solid #ddd"
                class="text-center"
              >
                <strong>Приоритет</strong>
              </th>
              <th />
              <th style="border-right: 1px solid #ddd" />
            </tr>
          </thead>
          <tr>
            <td class="border">
              <input
                class="form-control"
                type="text"
              >
            </td>
            <td class="border">
              <input
                class="form-control"
                type="text"
              >
            </td>
            <td class="text-center border">
              <input
                type="checkbox"
              >
            </td>
            <td class="border">
              <input
                class="form-control text-right"
                type="number"
              >
            </td>
            <td class="border">
              <button
                v-tippy
                class="btn last btn-blue-nb nbr"
                title="Сохранить"
              >
                <i class="fa fa-save" />
              </button>
            </td>
            <td class="border">
              <button
                v-tippy
                class="btn last btn-blue-nb nbr"
                title="Удалить"
              >
                <i class="fa fa-times" />
              </button>
            </td>
          </tr>
        </table>
      </div>
    </div>
  </div>
</template>

<script>

export default {
  name: 'ConstructPatientControlParam',
  data() {
    return {
      data: '',
    };
  },
};
</script>

<style scoped>
::v-deep .card {
  margin: 1rem 0;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
.scroll {
  min-height: 100px;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}
.sticky {
  position: sticky;
  top: 0;
  background-color: white;
}
.border {
  border: 1px solid #ddd;
}
::v-deep .form-control {
  border: none;
  padding: 6px 9px;
  background-color: transparent;
}
.table > thead > tr > th {
  border-bottom: 0;
}
</style>
