<template>
  <div>

    <div class="input-group">
      <input type="text" class="form-control" id="search-field" name="search-field" placeholder="Введите запрос">
      <span class="input-group-btn">
        <select class="btn">
          <option>A</option>
          <option>B</option>
          <option>C</option>
        </select>
      </span>
      <span class="input-group-btn"><button class="btn btn-blue-nb" type="button">Поиск</button></span>
    </div>
    // TODO: Patient Picker
  </div>
</template>

<script>
  export default {
    name: 'patient-picker'
  }
</script>

<style scoped>
  .input-group-btn select {
    border-color: #ccc;
    margin-top: 0;
    margin-bottom: 0;
    padding-top: 7px;
    padding-bottom: 7px;
  }
</style>
