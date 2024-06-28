<template>
  <div class="two-col">
    <div class="sidebar">
      <div class="sidebar-row">
        <input
          class="form-control"
          placeholder="Номер документа"
        >
        <button class="btn btn-blue-nb nbr">
          Найти
        </button>
      </div>
    </div>
    <div class="viewer">
      <h4>Просмотрщик</h4>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps({});
</script>

<style scoped lang="scss">
.two-col {
  display: grid;
  grid-template-columns: minmax(200px, 380px) minmax(150px, auto);
  height: calc(100vh - 36px);
}
.sidebar {
  display: flex;
  flex-direction: column;
  background-color: #f8f7f7;
  border-right: 1px solid #b1b1b1;

  .form-control {
    border-radius: 0;
  }
}
.empty-list {
  height: 20px;
  width: 100px;
  margin: 20px auto;
}
.sidebar-row {
  display: flex;
}

.sidebar-content {
  height: calc(100vh - 142px);
  overflow-y: auto;
}

.sidebar-footer {
  border-radius: 0;
  margin: 0;
  flex: 0 0 34px;
}
</style>
