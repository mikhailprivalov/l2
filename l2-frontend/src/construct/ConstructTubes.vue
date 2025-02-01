<template>
  <div>
    <div
      class="card-no-hover card card-1"
    >
      <div class="scroll">
        <table class="table">
          <colgroup>
            <col>
            <col>
            <col>
            <col style="width: 30px">
          </colgroup>
          <thead>
            <tr>
              <td><strong>Название</strong></td>
              <td><strong>Код</strong></td>
              <td><strong>Цвет</strong></td>
              <td />
            </tr>
          </thead>
          <tr
            v-if="tubes.length === 0"
            class="text-center"
          >
            <td
              colspan="4"
            >
              Нет данных
            </td>
          </tr>
          <tr>
            <td class="border">
              <input class="form-control">
            </td>
            <td class="border">
              <input class="form-control">
            </td>
            <td class="border">
              <input class="form-control">
            </td>
            <td class="border">
              <div class="button">
                <button
                  v-tippy
                  class="btn last btn-blue-nb nbr"
                  title="Редактировать"
                >
                  <i class="fa fa-pencil" />
                </button>
              </div>
            </td>
          </tr>
        </table>
      </div>
    </div>
    <h4>
      Добавить пробирку
    </h4>
    <div>
      <table class="table">
        <colgroup>
          <col>
          <col>
          <col>
          <col style="width: 30px">
        </colgroup>
        <tr>
          <td class="border">
            <input class="form-control">
          </td>
          <td class="border">
            <input class="form-control">
          </td>
          <td class="border">
            <input class="form-control">
          </td>
          <td class="border">
            <div class="button">
              <button
                v-tippy
                class="btn last btn-blue-nb nbr"
                title="Добавить"
              >
                <i class="fa fa-plus" />
              </button>
            </div>
          </td>
        </tr>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

// import * as actions from '@/store/action-types';

const tubes = ref([]);
</script>

<style scoped>
::v-deep .form-control {
  border: 0;
}
::v-deep .card {
  margin: 0;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
.scroll {
  min-height: 112px;
  max-height: calc(100vh - 400px);
  overflow-y: auto;
}
.border {
  border: 1px solid #ddd;
  border-radius: 0;
}
.table > thead > tr > th {
  border-bottom: 0;
}
.button {
  width: 100%;
  display: flex;
  flex-wrap: nowrap;
  flex-direction: row;
  justify-content: stretch;
}
  .btn {
    align-self: stretch;
    flex: 1;
    padding: 7px 0;
  }
</style>
