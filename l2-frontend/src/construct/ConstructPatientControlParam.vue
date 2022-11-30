<template>
  <div>
    <h4>Контролируемые параметры пациентов</h4>
    <div class="card card1 card-no-hover">
      <div class="scroll">
        <table class="table">
          <colgroup>
            <col style="min-width: 200px">
            <col style="width: 200px">
            <col style="width: 108px">
            <col style="width: 100px">
            <col style="width: 39px">
            <col style="width: 36px">
          </colgroup>
          <thead class="sticky">
            <tr>
              <th
                class="text-center"
              >
                <strong>Название</strong>
              </th>
              <th
                class="text-center"
              >
                <strong>Код</strong>
              </th>
              <th
                class="text-center"
              >
                <strong>Глобальный</strong>
              </th>
              <th
                class="text-center"
              >
                <strong>Приоритет</strong>
              </th>
              <th />
              <th />
            </tr>
          </thead>
          <tr class="border">
            <td class="td-padding">
              <input
                class="form-control"
                style="border-bottom-right-radius: 0; border-top-right-radius: 0"
                type="text"
              >
            </td>
            <td class="td-padding">
              <input
                class="form-control"
                style="border-bottom-left-radius: 0; border-top-left-radius: 0"
                type="text"
              >
            </td>
            <td
              class="text-center td-padding"
            >
              <input
                class="checkbox"
                type="checkbox"
              >
            </td>
            <td class="td-padding">
              <input
                class="form-control text-right"
                type="number"
              >
            </td>
            <td class="text-center ">
              <button
                v-tippy
                class="btn btn-blue-nb"
                title="Сохранить"
              >
                <i class="fa fa-save" />
              </button>
            </td>
            <td class="text-center">
              <button
                v-tippy
                class="btn btn-blue-nb"
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
.checkbox {
  height: 20px;
  width: 100%;
}
.td-padding {
  padding: 3px 2px;
}
::v-deep .form-control {
  padding: 6px 9px;
  border-radius: 8px;
  background-color: transparent;
}
.table > thead > tr > th {
  border-bottom: 0;
}
</style>
